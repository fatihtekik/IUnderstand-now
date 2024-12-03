import os
import datetime
import telebot
from telebot import types
from telebot.types import ReplyKeyboardRemove
import psycopg

id_teach = None
id_stud = None

# Замените на ваш токен Telegram-бота
token = '8154463207:AAGRK4G288WXsWcARiPpHujaZVIoYhn9vtY'
bot = telebot.TeleBot(token)

STUDENT_R = 'student'
TEACHER_R = 'teacher'
login = ""

if not os.path.exists('documents'):
    os.makedirs('documents')

# Подключение к БД
def connect_to_db():
    try:
        conn = psycopg.connect(
            dbname="postgres",
            user="postgres",
            password="Aidana2007",
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        print("Ошибка подключения к базе данных.")
        return None

user_data = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    global user_data, id_stud, id_teach
    user_data[message.chat.id] = {}
    id_stud = None
    id_teach = None
    bot.send_message(message.chat.id, "Добро пожаловать в EVALIX, бот по учебной части!\nВведите ваш логин.", reply_markup=ReplyKeyboardRemove())
    user_data[message.chat.id] = {"step": "login"}  # Сохраняем, что находимся на шаге ввода логина

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == "login")
def process_login(message):
    global id_stud
    global id_teach
    login = message.text.strip()

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_student FROM login WHERE login = %s", (login,))
        student = cursor.fetchone()

        cursor.execute("SELECT id_teacher FROM teacher_login WHERE login = %s", (login,))
        teacher = cursor.fetchone()

        if student:
            user_data[message.chat.id]["step"] = "password"
            user_data[message.chat.id]["login"] = login
            user_data[message.chat.id]["id_student"] = student[0]
            id_stud = student[0]
            user_data[message.chat.id]["role"] = STUDENT_R
            bot.send_message(message.chat.id, "Логин студента найден. Введите ваш пароль.")
        elif teacher:
            user_data[message.chat.id]["step"] = "password"
            user_data[message.chat.id]["login"] = login
            user_data[message.chat.id]["id_teacher"] = teacher[0]
            id_teach = teacher[0]
            user_data[message.chat.id]["id_teacher"] = id_teach
            user_data[message.chat.id]["role"] = TEACHER_R
            bot.send_message(message.chat.id, "Логин преподавателя найден. Введите ваш пароль.")
        else:
            bot.send_message(message.chat.id, "Такого логина не существует. Попробуйте еще раз.")

        cursor.close()
        conn.close()

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == "password")
def process_password(message):
    password = message.text.strip()
    login = user_data[message.chat.id].get("login")
    role = user_data[message.chat.id].get("role")

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        if role == STUDENT_R:
            cursor.execute("SELECT password FROM login WHERE login = %s", (login,))
        elif role == TEACHER_R:
            cursor.execute("SELECT password FROM teacher_login WHERE login = %s", (login,))

        user = cursor.fetchone()

        if user and user[0] == password:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            if role == STUDENT_R:
                markup.add(
                    types.KeyboardButton('Академическая успеваемость'),
                    types.KeyboardButton('Оценки и GPA'),
                    types.KeyboardButton('Расписание'),
                    types.KeyboardButton('Рейтинг'),
                    types.KeyboardButton('Документы'),
                    types.KeyboardButton('Оплата за учёбу')
                )
            elif role == TEACHER_R:
                markup.add(
                    types.KeyboardButton('Расписание'),
                    types.KeyboardButton('Переносы'),
                    types.KeyboardButton('Ввод оценок и Н-ок')
                )

            bot.send_message(
                message.chat.id,
                "Пароль верный! Добро пожаловать!",
                reply_markup=markup
            )
            user_data[message.chat.id]["step"] = "authenticated"  # Пользователь аутентифицирован
        else:
            bot.send_message(message.chat.id, "Неверный пароль. Попробуйте еще раз.")

        cursor.close()
        conn.close()
    else:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")

# РАСПИСАНИЕ
schedules = {
    'ПО2301': {
        'ПН': ['ИКТ', 'ИКТ', 'Алгоритмы'],
        'ВТ': ['Алгоритмы', 'БД', 'ИКТ'],
        'СР': ['БД', 'БД', 'Алгоритмы'],
        'ЧТ': ['Алгоритмы', 'Алгоритмы', 'БД'],
        'ПТ': ['БД', 'БД', 'БД']
    },
    'ПО2302': {
        'ПН': ['Алгоритмы', 'Алгоритмы', 'Алгоритмы'],
        'ВТ': ['ИКТ', 'БД', 'БД'],
        'СР': ['БД', 'ИКТ', 'Алгоритмы'],
        'ЧТ': ['БД', 'Алгоритмы', 'БД'],
        'ПТ': ['Алгоритмы', 'БД', 'БД']
    },
    'ВТ2310': {
        'ПН': ['Алгоритмы', 'Алгоритмы', 'БД'],
        'ВТ': ['АК', 'Алгоритмы', 'БД'],
        'СР': ['БД', 'БД', 'Алгоритмы'],
        'ЧТ': ['АК', 'Алгоритмы', 'АК'],
        'ПТ': ['Алгоритмы', 'БД', 'АК']
    }
}

# Выбор группы
@bot.message_handler(func=lambda message: message.text == 'Расписание')
def choose_group(message):
    markup = types.InlineKeyboardMarkup()
    if "group_id" in user_data[message.chat.id]:
        markup = types.InlineKeyboardMarkup()
        days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']
        buttons = [types.InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days]
        markup.add(*buttons)
        bot.send_message(message.chat.id, f'Вы выбрали группу {user_data[message.chat.id]["group_id"]}. Теперь выберите день недели:',
                         reply_markup=markup)
    else:
        groups = ['ПО2301', 'ПО2302', 'ВТ2310']
        buttons = [types.InlineKeyboardButton(group, callback_data=f"group_{group}") for group in groups]
        markup.add(*buttons)
        bot.send_message(message.chat.id, 'Выберите свою группу:', reply_markup=markup)

# Обработчик выбора группы
@bot.callback_query_handler(func=lambda call: call.data.startswith("group_"))
def choose_day(call):
    group_id = call.data.split("_")[1]
    user_data[call.message.chat.id]["group_id"] = group_id
    markup = types.InlineKeyboardMarkup()
    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']
    buttons = [types.InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days]
    markup.add(*buttons)
    bot.send_message(call.message.chat.id, f'Вы выбрали группу {group_id}. Теперь выберите день недели:', reply_markup=markup)

# Обработчик выбора дня
@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def show_day_schedule(call):
    day = call.data.split("_")[1]

    group_id = user_data.get(call.message.chat.id)["group_id"]
    if not group_id:
        bot.send_message(call.message.chat.id, "Ошибка: группа не выбрана.")
        return
    if group_id in schedules:
        schedule = schedules[group_id].get(day, [])
        if schedule:
            schedule_text = '\n'.join([f'{i + 1}. {lesson}' for i, lesson in enumerate(schedule)])
            bot.send_message(call.message.chat.id, f'Расписание на {day} для группы {group_id}:\n{schedule_text}')
        else:
            bot.send_message(call.message.chat.id, f'На {day} у группы {group_id} нет занятий.')
    else:
        bot.send_message(call.message.chat.id, "Расписание для вашей группы не найдено.")

def get_gpa_from_score(score):
    if 95 <= score <= 100:
        return 4.0
    elif 90 <= score < 94:
        return 3.67
    elif 85 <= score < 89:
        return 3.33
    elif 80 <= score < 84:
        return 3.0
    elif 75 <= score < 79:
        return 2.67
    elif 70 <= score < 74:
        return 2.33
    elif 65 <= score < 69:
        return 2.0
    elif 60 <= score < 64:
        return 1.67
    elif 55 <= score < 59:
        return 1.33
    elif 50 <= score < 54:
        return 1.0
    else:
        return 0.0

@bot.message_handler(func=lambda message: message.text == 'Оценки и GPA')
def show_GPA(message):
    global id_stud

    conn = connect_to_db()

    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")
        return

    cursor = conn.cursor()
    cursor.execute(
        '''SELECT ocenki.ocenka, teachers.FIO_teacher, ocenki.date 
           FROM ocenki 
           JOIN students ON students.id_student = ocenki.id_student 
           JOIN teachers ON teachers.id_teacher = ocenki.id_teacher 
           WHERE students.id_student = %s 
           ORDER BY ocenki.date''', (id_stud,)
    )

    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "Нет данных об оценках.")
        cursor.close()
        conn.close()
        return

    column_names = [desc[0] for desc in cursor.description]
    grades = []

    result = ""
    for row in rows:
        ocenka, fio_teacher, date = row
        if ocenka == 0:  # Пропускаем нулевые оценки
            continue
        row_dict = {column_names[i]: row[i] for i in range(len(row))}
        result += f"Оценка: {row_dict['ocenka']}\nПреподаватель: {row_dict['fio_teacher']}\nДата: {row_dict['date']}\n\n"

        ocenka_int = int(ocenka)
        if ocenka_int > 0:  # Исключаем нулевые оценки
            gpa = get_gpa_from_score(ocenka_int)
            grades.append(gpa)

    if grades:
        gpa = sum(grades) / len(grades)
        result += f"Ваш GPA: {gpa:.2f}"
    else:
        result += "Не удалось рассчитать GPA, так как нет оценок"

    if result:
        bot.send_message(message.chat.id, result)
    else:
        bot.send_message(message.chat.id, "Нет данных об оценках.")

    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == 'Академическая успеваемость')
def akadem(message):
    global id_stud
    conn = connect_to_db()

    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")
        return

    cursor = conn.cursor()

    cursor.execute(
        '''SELECT ocenki.ocenka, teachers.FIO_teacher, ocenki.date 
           FROM ocenki 
           JOIN students ON students.id_student = ocenki.id_student 
           JOIN teachers ON teachers.id_teacher = ocenki.id_teacher 
           WHERE students.id_student = %s 
           ORDER BY ocenki.date''', (id_stud,)
    )

    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "Нет данных об оценках.")
        cursor.close()
        conn.close()
        return

    column_names = [desc[0] for desc in cursor.description]
    grade_nul = []
    gradess = []
    count = 0

    result = ""
    for row in rows:
        ocenka, fio_teacher, date = row
        grade_nul.append(int(ocenka))
        if ocenka > 0:  # Исключаем нулевые оценки
            gradess.append(ocenka)
        elif ocenka == 0:
            count += 1
            result += f"Дата Н-ки: {date}\n"

    if grade_nul:
        cr = sum(grade_nul) / len(grade_nul)
        crr = sum(gradess) / len(gradess) if gradess else 0
        result += f"Ваш средний балл: {cr:.2f} (учитывая Н-ки)\nКоличество Н-ок: {count}\n\nВаш средний балл: {crr:.2f} (не учитывая Н-ки)"
    else:
        result += "Нет оценок"

    if result:
        bot.send_message(message.chat.id, result)
    else:
        bot.send_message(message.chat.id, "Нет данных об оценках.")

    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == 'Документы')
def docs(message):
    markup = types.InlineKeyboardMarkup()
    docs_add = types.InlineKeyboardButton(text="Загрузить документ", callback_data="docs_add")
    docs_show = types.InlineKeyboardButton(text="Показать документ", callback_data="docs_show")
    markup.add(docs_add, docs_show)

    bot.send_message(message.chat.id, "Выберите действие с документами", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    docum = None
    global id_stud
    global id_teach
    if call.data == "docs_add":
        bot.send_message(call.message.chat.id, "Отправьте файл вашего документа")
        user_data[call.message.chat.id]["step"] = "awaiting_document"

    elif call.data == "docs_show":
        if id_stud is not None:
            docum = get_docs(id_stud)
        elif id_teach is not None:
            docum = get_docs(id_teach)

        if docum:
            for doc in docum:
                bot.send_message(call.message.chat.id, f"Документ: {doc['file_name']}")
                # Отправляем сам файл
                bot.send_document(call.message.chat.id, open(doc['file_path'], 'rb'))
        else:
            bot.send_message(call.message.chat.id, "Вы не загрузили ни один документ.")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    if user_data.get(message.chat.id, {}).get("step") == "awaiting_document":
        if message.document:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            save_path = os.path.join(r"documents", message.document.file_name)  # сохраняем файл с его исходным именем
            with open(save_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            file_name = message.document.file_name
            if id_stud is not None:
                save_file_db(id_stud, file_name, save_path)
            elif id_teach is not None:
                save_file_db(id_teach, file_name, save_path)
            bot.reply_to(message, f'Файл {file_name} сохранен.')
            user_data[message.chat.id]["step"] = "authenticated"
        else:
            bot.send_message(message.chat.id, "Документ должен быть в виде файла")

def get_docs(stud):
    conn = connect_to_db()
    cursor = conn.cursor()
    query = "SELECT file_name, file_path FROM documents WHERE stud = %s"
    cursor.execute(query, (stud,))
    documents = cursor.fetchall()
    document_list = [{'file_name': doc[0], 'file_path': doc[1]} for doc in documents]
    cursor.close()
    conn.close()
    return document_list

def save_file_db(stud, file_name, file_path):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO documents (stud, file_name, file_path) VALUES (%s, %s, %s)"
        cursor.execute(query, (stud, file_name, file_path))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

@bot.message_handler(func=lambda message: message.text == 'Рейтинг')
def reiting(message):
    global id_stud
    conn = connect_to_db()

    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")
        return

    cursor = conn.cursor()

    cursor.execute(
        '''SELECT students.id_student, AVG(ocenki.ocenka) as avg_grade, SUM(CASE WHEN ocenki.ocenka = 0 THEN 1 ELSE 0 END) as count_zeros
           FROM ocenki 
           JOIN students ON students.id_student = ocenki.id_student  
           GROUP BY students.id_student
           ORDER BY avg_grade DESC'''
    )

    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "Нет данных об оценках.")
        cursor.close()
        conn.close()
        return

    result = ""
    user_rank = None
    for index, row in enumerate(rows):
        student_id, avg_grade, count_zeros = row
        rank = index + 1
        result += f"Место: {rank}.\nСредний балл: {avg_grade:.2f}. Н-ок: {count_zeros}\n\n"
        if student_id == id_stud:
            user_rank = rank
            user_avg_grade = avg_grade
            user_count_zeros = count_zeros

    if user_rank:
        result += f"\nВаше место: {user_rank}.\nСредний балл: {user_avg_grade:.2f} (с учетом Н-ок).\nН-ок: {user_count_zeros}"
    else:
        result += "\nНе удалось найти ваше место в рейтинге."

    bot.send_message(message.chat.id, result)

    cursor.close()
    conn.close()

# Начало интеграции функционала для преподавателей
@bot.message_handler(func=lambda message: message.text == 'Ввод оценок и Н-ок' and user_data.get(message.chat.id, {}).get("role") == TEACHER_R)
def teacher_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Выставить оценку'),
        types.KeyboardButton('Отметить пропуск'),
        types.KeyboardButton('Назад')
    )
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

# Обработка выставления оценки
@bot.message_handler(func=lambda message: message.text == 'Выставить оценку' and user_data.get(message.chat.id, {}).get("role") == TEACHER_R)
def ask_student_id_for_grade(message):
    bot.send_message(message.chat.id, "Введите ID студента или его логин:")
    user_data[message.chat.id]["step"] = "awaiting_student_id_for_grade"

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_student_id_for_grade")
def receive_student_id_for_grade(message):
    student_identifier = message.text.strip()
    # Проверяем, существует ли студент в базе данных
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id_student FROM login WHERE login = %s OR id_student::text = %s", (student_identifier, student_identifier))
    student = cursor.fetchone()
    cursor.close()
    conn.close()

    if student:
        user_data[message.chat.id]["student_id_for_grade"] = student[0]
        bot.send_message(message.chat.id, "Введите дату в формате ДД.ММ.ГГГГ:")
        user_data[message.chat.id]["step"] = "awaiting_grade_date"
    else:
        bot.send_message(message.chat.id, "Студент не найден. Попробуйте ещё раз.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_grade_date")
def receive_grade_date(message):
    date_text = message.text.strip()
    try:
        date_obj = datetime.datetime.strptime(date_text, "%d.%m.%Y").date()
        user_data[message.chat.id]["grade_date"] = date_obj
        bot.send_message(message.chat.id, "Введите оценку (от 0 до 100):")
        user_data[message.chat.id]["step"] = "awaiting_grade_value"
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_grade_value")
def receive_grade_value(message):
    try:
        grade = int(message.text.strip())
        if 0 <= grade <= 100:
            student_id = user_data[message.chat.id]["student_id_for_grade"]
            teacher_id = user_data[message.chat.id].get("id_teacher")
            grade_date = user_data[message.chat.id]["grade_date"]
            conn = connect_to_db()
            cursor = conn.cursor()

            # Проверяем, есть ли уже оценка для этого студента на указанную дату
            cursor.execute(
                "SELECT ocenka FROM ocenki WHERE id_student = %s AND id_teacher = %s AND date = %s",
                (student_id, teacher_id, grade_date)
            )
            existing_grade = cursor.fetchone()

            if existing_grade:
                existing_grade_value = existing_grade[0]
                bot.send_message(
                    message.chat.id,
                    f"У этого студента уже есть оценка на дату {grade_date.strftime('%d.%m.%Y')}: {existing_grade_value}.\nХотите обновить ее? (да/нет)"
                )
                user_data[message.chat.id]["step"] = "confirm_update_grade"
                user_data[message.chat.id]["new_grade"] = grade
            else:
                # Вставляем новую оценку
                cursor.execute(
                    "INSERT INTO ocenki (id_student, id_teacher, ocenka, date) VALUES (%s, %s, %s, %s)",
                    (student_id, teacher_id, grade, grade_date)
                )
                conn.commit()
                bot.send_message(message.chat.id, "Оценка успешно сохранена.")
                user_data[message.chat.id]["step"] = "authenticated"

            cursor.close()
            conn.close()
        else:
            bot.send_message(message.chat.id, "Введите корректную оценку от 0 до 100.")
    except ValueError:
        bot.send_message(message.chat.id, "Введите числовое значение для оценки.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "confirm_update_grade")
def confirm_update_grade(message):
    response = message.text.strip().lower()
    if response == 'да':
        student_id = user_data[message.chat.id]["student_id_for_grade"]
        teacher_id = user_data[message.chat.id].get("id_teacher")
        new_grade = user_data[message.chat.id]["new_grade"]
        grade_date = user_data[message.chat.id]["grade_date"]
        conn = connect_to_db()
        cursor = conn.cursor()

        # Обновляем существующую оценку
        cursor.execute(
            "UPDATE ocenki SET ocenka = %s WHERE id_student = %s AND id_teacher = %s AND date = %s",
            (new_grade, student_id, teacher_id, grade_date)
        )
        conn.commit()
        cursor.close()
        conn.close()

        bot.send_message(message.chat.id, "Оценка успешно обновлена.")
        user_data[message.chat.id]["step"] = "authenticated"
    elif response == 'нет':
        bot.send_message(message.chat.id, "Операция отменена. Оценка не была изменена.")
        user_data[message.chat.id]["step"] = "authenticated"
    else:
        bot.send_message(message.chat.id, "Пожалуйста, ответьте 'да' или 'нет'.")

# Обработка отметки пропуска (Н-ки)
@bot.message_handler(func=lambda message: message.text == 'Отметить пропуск' and user_data.get(message.chat.id, {}).get("role") == TEACHER_R)
def ask_student_id_for_absence(message):
    bot.send_message(message.chat.id, "Введите ID студента или его логин:")
    user_data[message.chat.id]["step"] = "awaiting_student_id_for_absence"

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_student_id_for_absence")
def receive_student_id_for_absence(message):
    student_identifier = message.text.strip()
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id_student FROM login WHERE login = %s OR id_student::text = %s", (student_identifier, student_identifier))
    student = cursor.fetchone()

    if student:
        user_data[message.chat.id]["student_id_for_absence"] = student[0]
        bot.send_message(message.chat.id, "Введите дату в формате ДД.ММ.ГГГГ:")
        user_data[message.chat.id]["step"] = "awaiting_absence_date"
    else:
        bot.send_message(message.chat.id, "Студент не найден. Попробуйте ещё раз.")
    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_absence_date")
def receive_absence_date(message):
    date_text = message.text.strip()
    try:
        date_obj = datetime.datetime.strptime(date_text, "%d.%m.%Y").date()
        user_data[message.chat.id]["absence_date"] = date_obj
        student_id = user_data[message.chat.id]["student_id_for_absence"]
        teacher_id = user_data[message.chat.id].get("id_teacher")
        conn = connect_to_db()
        cursor = conn.cursor()

        # Проверяем, есть ли уже оценка для этого студента на указанную дату
        cursor.execute(
            "SELECT ocenka FROM ocenki WHERE id_student = %s AND id_teacher = %s AND date = %s",
            (student_id, teacher_id, date_obj)
        )
        existing_grade = cursor.fetchone()

        if existing_grade:
            existing_grade_value = existing_grade[0]
            bot.send_message(
                message.chat.id,
                f"У этого студента уже есть оценка на дату {date_obj.strftime('%d.%m.%Y')}: {existing_grade_value}.\nХотите обновить ее на Н-ку? (да/нет)"
            )
            user_data[message.chat.id]["step"] = "confirm_update_absence"
        else:
            # Вставляем Н-ку
            cursor.execute(
                "INSERT INTO ocenki (id_student, id_teacher, ocenka, date) VALUES (%s, %s, %s, %s)",
                (student_id, teacher_id, 0, date_obj)
            )
            conn.commit()
            bot.send_message(message.chat.id, "Пропуск успешно отмечен.")
            user_data[message.chat.id]["step"] = "authenticated"

        cursor.close()
        conn.close()
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "confirm_update_absence")
def confirm_update_absence(message):
    response = message.text.strip().lower()
    if response == 'да':
        student_id = user_data[message.chat.id]["student_id_for_absence"]
        teacher_id = user_data[message.chat.id].get("id_teacher")
        absence_date = user_data[message.chat.id]["absence_date"]
        conn = connect_to_db()
        cursor = conn.cursor()

        # Обновляем оценку на Н-ку
        cursor.execute(
            "UPDATE ocenki SET ocenka = %s WHERE id_student = %s AND id_teacher = %s AND date = %s",
            (0, student_id, teacher_id, absence_date)
        )
        conn.commit()
        cursor.close()
        conn.close()

        bot.send_message(message.chat.id, "Оценка успешно обновлена на Н-ку.")
        user_data[message.chat.id]["step"] = "authenticated"
    elif response == 'нет':
        bot.send_message(message.chat.id, "Операция отменена. Оценка не была изменена.")
        user_data[message.chat.id]["step"] = "authenticated"
    else:
        bot.send_message(message.chat.id, "Пожалуйста, ответьте 'да' или 'нет'.")

@bot.message_handler(func=lambda message: message.text == 'Назад')
def go_back(message):
    user_data[message.chat.id]["step"] = "authenticated"
    # Отправляем главное меню в зависимости от роли
    role = user_data[message.chat.id].get("role")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == STUDENT_R:
        markup.add(
            types.KeyboardButton('Академическая успеваемость'),
            types.KeyboardButton('Оценки и GPA'),
            types.KeyboardButton('Расписание'),
            types.KeyboardButton('Рейтинг'),
            types.KeyboardButton('Документы'),
            types.KeyboardButton('Оплата за учёбу')
        )
    elif role == TEACHER_R:
        markup.add(
            types.KeyboardButton('Расписание'),
            types.KeyboardButton('Переносы'),
            types.KeyboardButton('Ввод оценок и Н-ок')
        )
    bot.send_message(message.chat.id, "Вы вернулись в главное меню.", reply_markup=markup)

# Запуск бота
bot.infinity_polling()
