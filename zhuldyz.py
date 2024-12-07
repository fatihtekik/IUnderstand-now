import os
from datetime import datetime
import telebot
from telebot import types
import psycopg2 as psycopg
from telebot.types import ReplyKeyboardRemove

token = '8154463207:AAGRK4G288WXsWcARiPpHujaZVIoYhn9vtY'
bot = telebot.TeleBot(token)

STUDENT_R = 'student'
TEACHER_R = 'teacher'

if not os.path.exists('documents'):
    os.makedirs('documents')

# Словарь для хранения данных пользователей
user_data = {}

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
        print("Ошибка подключения к базе данных:", e)
        return None

def save_or_update_chat_id(id_student, chat_id):
    conn = connect_to_db()
    if not conn:
        print("Ошибка подключения к базе данных.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM student_chat_id WHERE id_student = %s", (id_student,))
        result = cursor.fetchone()
        if result:
            cursor.execute("UPDATE student_chat_id SET chat_id = %s WHERE id_student = %s", (chat_id, id_student))
        else:
            cursor.execute("INSERT INTO student_chat_id (id_student, chat_id) VALUES (%s, %s)", (id_student, chat_id))
        conn.commit()
        return True
    except Exception as e:
        print("Ошибка при сохранении chat_id:", e)
        return False
    finally:
        cursor.close()
        conn.close()

@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    user_data[chat_id] = {
        "step": "login",
        "role": None,
        "id_student": None,
        "id_teacher": None
    }
    bot.send_message(chat_id, "Добро пожаловать в 𝐀𝖼𝖾𝐒𝗐𝗂𝗆! Введите ваш логин.", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "login")
def process_login(message):
    chat_id = message.chat.id
    login = message.text.strip()

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_student FROM login WHERE login = %s", (login,))
        student = cursor.fetchone()

        cursor.execute("SELECT id_teacher FROM teacher_login WHERE login = %s", (login,))
        teacher = cursor.fetchone()

        if student:
            user_data[chat_id]["step"] = "password"
            user_data[chat_id]["login"] = login
            user_data[chat_id]["id_student"] = student[0]
            user_data[chat_id]["role"] = STUDENT_R
            bot.send_message(chat_id, "Логин студента найден. Введите ваш пароль.")
        elif teacher:
            user_data[chat_id]["step"] = "password"
            user_data[chat_id]["login"] = login
            user_data[chat_id]["id_teacher"] = teacher[0]
            user_data[chat_id]["role"] = TEACHER_R
            bot.send_message(chat_id, "Логин преподавателя найден. Введите ваш пароль.")
        else:
            bot.send_message(chat_id, "Такого логина не существует. Попробуйте еще раз.")

        cursor.close()
        conn.close()
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "password")
def process_password(message):
    chat_id = message.chat.id
    password = message.text.strip()
    login = user_data[chat_id].get("login")
    role = user_data[chat_id].get("role")

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
                # Сохраняем или обновляем chat_id для студента
                save_or_update_chat_id(user_data[chat_id]["id_student"], chat_id)
                markup.add('Академическая успеваемость', 'оценки и GPA', 'Расписание', 'Рейтинг', 'Документы')
            elif role == TEACHER_R:
                markup.add('Расписание', 'Переносы', 'Ввод оценок и Н-ок')

            bot.send_message(chat_id, "Пароль верный! Добро пожаловать!", reply_markup=markup)
            user_data[chat_id]["step"] = "authenticated"
        else:
            bot.send_message(chat_id, "Неверный пароль. Попробуйте еще раз.")

        cursor.close()
        conn.close()
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")


stud_schedules = {
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

teach_schedules = {
    'ИКТ': {
        'ПН': ['ПО2301', 'ПО2301', ''],
        'ВТ': ['ПО2302', '', 'ПО2302'],
        'СР': [' ', ' ', ' '],
        'ЧТ': [' ', ' ', ' '],
        'ПТ': [' ', ' ', ' ']
    },
    'Составление алгоритмов': {
        'ПН': ['ПО2302', 'ПО2302', 'ПО2301'],
        'ВТ': ['ПО2301', 'ВТ2310', 'ПО2302'],
        'СР': [' ', ' ', 'ПО2302'],
        'ЧТ': ['ПО2301', 'ПО2301', 'ПО2302'],
        'ПТ': ['ПО2302', ' ', '  ']
    },
    'БД': {
        'ПН': [' ', ' ', 'ВТ2310'],
        'ВТ': [' ', 'ПО2301', 'ПО2302'],
        'СР': ['ВТ2310', 'ВТ2310', ' ПО2302'],
        'ЧТ': ['ПО2302', 'ПО2301', 'ПО2301'],
        'ПТ': ['ПО2301', 'ПО2301', 'ПО2301']
    }
}

@bot.message_handler(func=lambda message: message.text == 'Расписание')
def choose_group(message):
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)
    if role == STUDENT_R:
        # Если уже выбрана группа
        if "group_id" in user_data[chat_id]:
            markup = types.InlineKeyboardMarkup()
            days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']
            buttons = [types.InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days]
            markup.add(*buttons)
            bot.send_message(chat_id,
                             f'Вы выбрали группу {user_data[chat_id]["group_id"]}. Теперь выберите день недели:',
                             reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup()
            groups = ['ПО2301', 'ПО2302', 'ВТ2310']
            buttons = [types.InlineKeyboardButton(group, callback_data=f"group_{group}") for group in groups]
            markup.add(*buttons)
            bot.send_message(chat_id, 'Выберите свою группу:', reply_markup=markup)
    elif role == TEACHER_R:
        markup = types.InlineKeyboardMarkup()
        subjects = ['ИКТ', 'Составление алгоритмов', 'БД']
        buttons = [types.InlineKeyboardButton(subject, callback_data=f"subject_teach_{subject}") for subject in subjects]
        markup.add(*buttons)
        bot.send_message(chat_id, 'Выберите предмет для просмотра расписания:', reply_markup=markup)
    else:
        bot.send_message(chat_id, "Ваша роль не определена. Обратитесь к администратору.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("group_"))
def choose_day(call):
    chat_id = call.message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)
    group_id = call.data.split("_")[1]
    user_data[chat_id]["group_id"] = group_id
    markup = types.InlineKeyboardMarkup()
    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']
    buttons = [types.InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days]
    markup.add(*buttons)
    bot.send_message(chat_id, f'Вы выбрали группу {group_id}. Теперь выберите день недели:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("subject_teach_"))
def choose_subject(call):
    chat_id = call.message.chat.id
    subject = call.data.split("_")[2]
    user_data[chat_id]["subject"] = subject
    markup = types.InlineKeyboardMarkup()
    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']
    buttons = [types.InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days]
    markup.add(*buttons)
    bot.send_message(chat_id, f'Вы выбрали предмет "{subject}". Теперь выберите день недели:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def show_day_schedule(call):
    chat_id = call.message.chat.id
    role = user_data.get(chat_id, {}).get("role")
    day = call.data.split("_")[1]

    if role == STUDENT_R:
        group_id = user_data[chat_id].get("group_id")
        if group_id in stud_schedules:
            schedule = stud_schedules[group_id].get(day, [])
            if schedule:
                schedule_text = '\n'.join([f'{i+1}. {lesson}' for i, lesson in enumerate(schedule)])
                bot.send_message(chat_id, f'Расписание на {day} для группы {group_id}:\n{schedule_text}')
            else:
                bot.send_message(chat_id, f'На {day} для группы {group_id} нет занятий.')
        else:
            bot.send_message(chat_id, "Группа не найдена в расписании.")

    elif role == TEACHER_R:
        subject = user_data[chat_id].get("subject")
        if subject in teach_schedules:
            schedule = teach_schedules[subject].get(day, [])
            if schedule:
                schedule_text = '\n'.join([f'{i+1}. {g}' for i, g in enumerate(schedule) if g.strip()])
                if schedule_text:
                    bot.send_message(chat_id,
                                     f'Расписание на {day} для предмета {subject}:\n{schedule_text}')
                else:
                    bot.send_message(chat_id, f'На {day} для предмета {subject} нет занятий.')
            else:
                bot.send_message(chat_id, f'На {day} для предмета {subject} нет занятий.')
        else:
            bot.send_message(chat_id, "Расписание для вашего предмета не найдено.")

def get_gpa_from_score(score):
    if 95 <= score <= 100:
        return 4.0
    elif 90 <= score < 95:
        return 3.67
    elif 85 <= score < 90:
        return 3.33
    elif 80 <= score < 85:
        return 3.0
    elif 75 <= score < 80:
        return 2.67
    elif 70 <= score < 75:
        return 2.33
    elif 65 <= score < 70:
        return 2.0
    elif 60 <= score < 65:
        return 1.67
    elif 55 <= score < 60:
        return 1.33
    elif 50 <= score < 55:
        return 1.0
    else:
        return 0.0

@bot.message_handler(func=lambda message: message.text == 'оценки и GPA')
def show_GPA(message):
    chat_id = message.chat.id
    id_stud = user_data[chat_id].get("id_student")
    if not id_stud:
        bot.send_message(chat_id, "ID студента не найден. Перезапустите бота.")
        return

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()
    cursor.execute('''
        SELECT teachers.nazvanie_predmeta, teachers.FIO_teacher, AVG(ocenki.ocenka) as avg_score
        FROM ocenki 
        JOIN students ON students.id_student = ocenki.id_student 
        JOIN teachers ON teachers.id_teacher = ocenki.id_teacher 
        WHERE students.id_student = %s 
        GROUP BY teachers.nazvanie_predmeta, teachers.FIO_teacher
    ''', (id_stud,))
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(chat_id, "Нет данных об оценках.")
        cursor.close()
        conn.close()
        return

    count_s = 0
    total_GPA = 0
    result = ""
    for row in rows:
        nazvanie_predmeta, fio_teacher, avg_score = row
        gpa = get_gpa_from_score(avg_score)
        total_GPA += gpa
        count_s += 1
        result += (f"Предмет: {nazvanie_predmeta}\nПреподаватель: {fio_teacher}\n"
                   f"Средняя оценка: {avg_score:.2f}\nGPA: {gpa:.2f}\n\n")

    if count_s > 0:
        overall_gpa = total_GPA / count_s
        result += f"Средний GPA по всем предметам: {overall_gpa:.2f}"
    else:
        result += "Нет оценок для расчета среднего GPA."

    bot.send_message(chat_id, result)
    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == 'Академическая успеваемость')
def akadem(message):
    chat_id = message.chat.id
    id_stud = user_data[chat_id].get("id_student")
    if not id_stud:
        bot.send_message(chat_id, "ID студента не найден. Перезапустите бота.")
        return

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT teachers.nazvanie_predmeta 
        FROM ocenki
        JOIN teachers ON teachers.id_teacher = ocenki.id_teacher
        JOIN students ON students.id_student = ocenki.id_student
        WHERE students.id_student = %s;
    ''', (id_stud,))
    subjects = cursor.fetchall()
    if not subjects:
        bot.send_message(chat_id, "Нет данных об оценках.")
        cursor.close()
        conn.close()
        return

    markup = types.InlineKeyboardMarkup()
    print(subjects)
    buttons = [types.InlineKeyboardButton(subject[0], callback_data=f"subject_{subject[0]}") for subject in subjects]
    markup.add(*buttons)
    bot.send_message(chat_id, "Выберите предмет для просмотра успеваемости:", reply_markup=markup)

    cursor.close()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("subject_"))
def show_subject_ocenki(call):
    chat_id = call.message.chat.id
    id_stud = user_data[chat_id].get("id_student")
    subject = call.data.split("_")[1]

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()
    cursor.execute('''
        SELECT teachers.nazvanie_predmeta, teachers.fio_teacher, ocenki.ocenka, ocenki.date
        FROM ocenki
        JOIN teachers ON teachers.id_teacher = ocenki.id_teacher
        JOIN students ON students.id_student = ocenki.id_student
        WHERE students.id_student = %s AND teachers.nazvanie_predmeta = %s
        ORDER BY ocenki.date
    ''', (id_stud, subject))

    rows = cursor.fetchall()
    if not rows:
        bot.send_message(chat_id, f"Нет данных об успеваемости по предмету {subject}.")
        cursor.close()
        conn.close()
        return

    count_z = 0
    result = f"Предмет: *{subject}*\nПреподаватель: *{rows[0][1]}*\nОценки:\n"
    for row in rows:
        nazv, fio_t, ocenka, date = row[0], row[1], row[2], row[3]
        if ocenka > 0:
            result += f" - Оценка: {ocenka}, дата: {date}\n"
        else:
            count_z += 1
            result += f" - Н-ка: {date}\n"
    result += f"\nКоличество Н-ок: {count_z}"

    bot.send_message(chat_id, result, parse_mode="Markdown")
    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == 'Документы')
def docs(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    docs_add = types.InlineKeyboardButton(text="Загрузить документ", callback_data="docs_add")
    docs_show = types.InlineKeyboardButton(text="Показать документ", callback_data="docs_show")
    markup.add(docs_add, docs_show)
    bot.send_message(chat_id, "Выберите действие с документами:", reply_markup=markup)

def get_docs(stud):
    conn = connect_to_db()
    if not conn:
        return []
    cursor = conn.cursor()
    query = "SELECT file_name, file_path FROM documents WHERE stud = %s"
    cursor.execute(query, (stud,))
    documents = cursor.fetchall()
    cursor.close()
    conn.close()
    document_list = [{'file_name': doc[0], 'file_path': doc[1]} for doc in documents]
    return document_list

def save_file_db(stud, file_name, file_path):
    conn = connect_to_db()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        query = "INSERT INTO documents (stud, file_name, file_path) VALUES(%s, %s, %s)"
        cursor.execute(query, (stud, file_name, file_path))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("docs_"))
def handle_docs_callback(call):
    chat_id = call.message.chat.id
    action = call.data
    role = user_data[chat_id].get("role")
    id_stud = user_data[chat_id].get("id_student")
    id_teach = user_data[chat_id].get("id_teacher")

    if action == "docs_add":
        bot.send_message(chat_id, "Отправьте файл вашего документа")

        @bot.message_handler(content_types=['document'])
        def handle_file(message):
            c_id = message.chat.id
            stud_id = user_data[c_id].get("id_student")
            if message.document:
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                save_path = os.path.join("documents", message.document.file_name)
                with open(save_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                file_name = message.document.file_name
                save_file_db(stud_id, file_name, save_path)
                bot.reply_to(message, f'Файл {file_name} сохранен.')
            else:
                bot.send_message(c_id, "Документ должен быть в виде файла")

    elif action == "docs_show":
        # Показать документы для студента или преподавателя
        if id_stud is not None:
            docum = get_docs(id_stud)
        else:
            # Если у нас был бы функционал для преподавателя - можно добавить при необходимости
            docum = []
        if docum:
            for doc in docum:
                bot.send_message(chat_id, f"Документ: {doc['file_name']}")
                bot.send_document(chat_id, open(doc['file_path'], 'rb'))
        else:
            bot.send_message(chat_id, "Вы не загрузили ни один документ.")

@bot.message_handler(func=lambda message: message.text == 'Рейтинг')
def reiting(message):
    chat_id = message.chat.id
    id_stud = user_data[chat_id].get("id_student")
    if not id_stud:
        bot.send_message(chat_id, "ID студента не найден. Перезапустите бота.")
        return

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()
    cursor.execute('''
        SELECT students.id_student, ocenki.ocenka
        FROM ocenki 
        JOIN students ON students.id_student = ocenki.id_student  
        ORDER BY students.id_student
    ''')
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(chat_id, "Нет данных об оценках.")
        cursor.close()
        conn.close()
        return

    students_grades = {}
    for row in rows:
        s_id, ocenka = row
        if s_id not in students_grades:
            students_grades[s_id] = {"grades": [], "count_zeros": 0}
        students_grades[s_id]["grades"].append(ocenka)
        if ocenka == 0:
            students_grades[s_id]["count_zeros"] += 1

    students_avg = []
    for student_id, data in students_grades.items():
        total_grades = sum(data["grades"])
        total_count = len(data["grades"])
        avg_grade = total_grades / total_count if total_count > 0 else 0
        students_avg.append({"id_student": student_id, "avg_grade": avg_grade, "count_zeros": data["count_zeros"]})

    students_avg.sort(key=lambda x: x["avg_grade"], reverse=True)

    result = ""
    for index, student in enumerate(students_avg):
        rank = index + 1
        avg_grade = student["avg_grade"]
        count_zeros = student["count_zeros"]
        result += f"Место: {rank}.\nСредний балл: {avg_grade:.2f}.   Н-ок: {count_zeros}\n\n"

    user_rank = next((index + 1 for index, student in enumerate(students_avg) if student["id_student"] == id_stud), None)
    if user_rank:
        result += f"\nВаше место: {user_rank}.\nСредний балл: {students_avg[user_rank - 1]['avg_grade']:.2f}\n"
    else:
        result += "\nНе удалось найти ваше место в рейтинге."

    bot.send_message(chat_id, result)
    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == 'Переносы')
def vvod(message):
    chat_id = message.chat.id
    role = user_data[chat_id].get("role")
    id_teach = user_data[chat_id].get("id_teacher")
    if role == STUDENT_R:
        bot.send_message(chat_id, "Этой функцией могут пользоваться только учителя.")
    elif role == TEACHER_R:
        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            return
        cursor = conn.cursor()
        cursor.execute('''
            SELECT gruppy.nazvanie_gruppy 
            FROM gruppy
            JOIN spec_teacher ON spec_teacher.spec_id = gruppy.spec_id
            WHERE spec_teacher.teacher_id = %s
        ''', (id_teach,))
        rows = cursor.fetchall()
        if not rows:
            bot.send_message(chat_id, "Нет данных о группах.")
            cursor.close()
            conn.close()
            return
        markup = types.InlineKeyboardMarkup()
        for row in rows:
            nazvanie_gruppy = row[0]
            button = types.InlineKeyboardButton(text=nazvanie_gruppy, callback_data=f"perenos_{nazvanie_gruppy}")
            markup.add(button)
        bot.send_message(chat_id, "Выберите группу:", reply_markup=markup)
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("perenos_"))
def choose_group_pzh(call):
    chat_id = call.message.chat.id
    group_name = call.data.split("_")[1]
    user_data[chat_id]["perenos"] = {
        "group_name": group_name,
        "process_completed": False
    }
    bot.send_message(chat_id, "Напишите сообщение студентам")

@bot.message_handler(func=lambda message: "perenos" in user_data.get(message.chat.id, {}) and not user_data[message.chat.id]["perenos"]["process_completed"])
def handle_group_message(message):
    chat_id = message.chat.id
    text_message = message.text
    group_name = user_data[chat_id]["perenos"]["group_name"]
    id_teach = user_data[chat_id].get("id_teacher")

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()
    cursor.execute("SELECT id_gruppy FROM gruppy WHERE nazvanie_gruppy = %s", (group_name,))
    group_id = cursor.fetchone()
    if group_id:
        group_id = group_id[0]
    else:
        bot.send_message(chat_id, "Группа не найдена в базе данных.")
        cursor.close()
        conn.close()
        return

    cursor.execute("SELECT fio_teacher FROM teachers WHERE id_teacher = %s", (id_teach,))
    teacher_name = cursor.fetchone()
    if teacher_name:
        teacher_name = teacher_name[0]
    else:
        teacher_name = "Преподаватель"

    # Сохраняем сообщение о переносе в БД
    try:
        cursor.execute("INSERT INTO reschedule (id_gruppy, text_message) VALUES (%s, %s)", (group_id, text_message))
        conn.commit()
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка записи в базу данных: {e}")
        cursor.close()
        conn.close()
        return

    # Отправляем сообщение студентам
    try:
        cursor.execute("SELECT chat_id FROM student_chat_id WHERE id_gruppy = %s", (group_id,))
        students = cursor.fetchall()
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка получения списка студентов: {e}")
        cursor.close()
        conn.close()
        return

    cursor.close()
    conn.close()

    if not students:
        bot.send_message(chat_id, "В этой группе нет зарегистрированных учеников.")
        user_data[chat_id]["perenos"]["process_completed"] = True
        return

    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

    for student in students:
        student_id = student[0]
        try:
            bot.send_message(
                student_id,
                f"*{teacher_name}* отправил сообщение:\n\n_{text_message}_\n\n🕒 Отправлено: {current_time}",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка отправки сообщения пользователю {student_id}: {e}")

    bot.send_message(chat_id, "Сообщение отправлено всем ученикам группы.")
    user_data[chat_id]["perenos"]["process_completed"] = True

# Функция для получения chat_id студента
def get_student_chat_id(student_id):
    conn = connect_to_db()
    if not conn:
        print("Ошибка подключения к базе данных.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM student_chat_id WHERE id_student = %s", (student_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        print("Ошибка получения chat_id:", e)
        return None
    finally:
        cursor.close()
        conn.close()

@bot.message_handler(func=lambda message: message.text == 'Ввод оценок и Н-ок' and user_data.get(message.chat.id, {}).get("role") == TEACHER_R)
def teacher_menu(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Выставить оценку', 'Отметить пропуск', 'Назад')
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Выставить оценку' and user_data.get(message.chat.id, {}).get("role") == TEACHER_R)
def ask_student_for_grade(message):
    chat_id = message.chat.id
    id_teach = user_data[chat_id].get("id_teacher")
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT students.id_student, students.fio
            FROM spec_teacher
            JOIN gruppy ON gruppy.spec_id = spec_teacher.spec_id
            JOIN students ON students.id_gruppy = gruppy.id_gruppy
            WHERE spec_teacher.teacher_id = %s
        ''', (id_teach,))
        students = cursor.fetchall()
        cursor.close()
        conn.close()

        if students:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for student in students:
                student_id, fio = student
                markup.add(types.InlineKeyboardButton(text=fio, callback_data=f"select_student_grade_{student_id}"))
            bot.send_message(chat_id, "Выберите студента из списка:", reply_markup=markup)
            user_data[chat_id]["step"] = "selecting_student_for_grade"
        else:
            bot.send_message(chat_id, "Список студентов пуст.")
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_student_grade_"))
def receive_student_for_grade(call):
    chat_id = call.message.chat.id
    student_id = int(call.data.split("_")[-1])
    user_data[chat_id]["student_id_for_grade"] = student_id
    user_data[chat_id]["step"] = "awaiting_grade_date"
    bot.send_message(chat_id, "Введите дату в формате ДД.ММ.ГГГГ:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_grade_date")
def receive_grade_date(message):
    chat_id = message.chat.id
    date_text = message.text.strip()
    try:
        date_obj = datetime.strptime(date_text, "%d.%m.%Y").date()
        user_data[chat_id]["grade_date"] = date_obj
        user_data[chat_id]["step"] = "awaiting_grade_value"
        bot.send_message(chat_id, "Введите оценку (от 0 до 100):")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_grade_value")
def receive_grade_value(message):
    chat_id = message.chat.id
    id_teach = user_data[chat_id].get("id_teacher")
    try:
        grade = int(message.text.strip())
        if 0 <= grade <= 100:
            student_id = user_data[chat_id]["student_id_for_grade"]
            grade_date = user_data[chat_id]["grade_date"]
            conn = connect_to_db()
            if not conn:
                bot.send_message(chat_id, "Ошибка подключения к базе данных.")
                return
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ocenka FROM ocenki WHERE id_student = %s AND id_teacher = %s AND date = %s",
                (student_id, id_teach, grade_date)
            )
            existing_grade = cursor.fetchone()
            if existing_grade:
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("Да", callback_data="confirm_update_grade_yes"),
                    types.InlineKeyboardButton("Нет", callback_data="confirm_update_grade_no")
                )
                bot.send_message(
                    chat_id,
                    f"У этого студента уже есть оценка на {grade_date.strftime('%d.%m.%Y')}: {existing_grade[0]}.\nОбновить ее?",
                    reply_markup=markup
                )
                user_data[chat_id]["step"] = "confirming_update_grade"
                user_data[chat_id]["new_grade"] = grade
            else:
                # Вставляем новую оценку
                cursor.execute(
                    "INSERT INTO ocenki (id_student, id_teacher, ocenka, date) VALUES (%s, %s, %s, %s)",
                    (student_id, id_teach, grade, grade_date)
                )
                conn.commit()
                bot.send_message(chat_id, "Оценка успешно сохранена.")
                user_data[chat_id]["step"] = "authenticated"
            cursor.close()
            conn.close()
        else:
            bot.send_message(chat_id, "Введите корректную оценку от 0 до 100.")
    except ValueError:
        bot.send_message(chat_id, "Введите числовое значение для оценки.")

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_update_grade_yes", "confirm_update_grade_no"])
def confirm_update_grade(call):
    chat_id = call.message.chat.id
    if call.data == "confirm_update_grade_yes":
        student_id = user_data[chat_id]["student_id_for_grade"]
        id_teach = user_data[chat_id].get("id_teacher")
        new_grade = user_data[chat_id]["new_grade"]
        grade_date = user_data[chat_id]["grade_date"]
        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            return
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ocenki SET ocenka = %s WHERE id_student = %s AND id_teacher = %s AND date = %s",
            (new_grade, student_id, id_teach, grade_date)
        )
        conn.commit()
        cursor.close()
        conn.close()
        bot.send_message(chat_id, "Оценка успешно обновлена.")
        user_data[chat_id]["step"] = "authenticated"
    else:
        bot.send_message(chat_id, "Операция отменена.")
        user_data[chat_id]["step"] = "authenticated"

@bot.message_handler(func=lambda message: message.text == 'Отметить пропуск' and user_data.get(message.chat.id, {}).get("role") == TEACHER_R)
def ask_student_for_absence(message):
    chat_id = message.chat.id
    id_teach = user_data[chat_id].get("id_teacher")
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT students.id_student, students.fio
            FROM spec_teacher
            JOIN gruppy ON gruppy.spec_id = spec_teacher.spec_id
            JOIN students ON students.id_gruppy = gruppy.id_gruppy
            WHERE spec_teacher.teacher_id = %s
        ''', (id_teach,))
        students = cursor.fetchall()
        cursor.close()
        conn.close()

        if students:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for student in students:
                student_id, fio = student
                markup.add(types.InlineKeyboardButton(text=fio, callback_data=f"select_student_absence_{student_id}"))
            bot.send_message(chat_id, "Выберите студента:", reply_markup=markup)
            user_data[chat_id]["step"] = "selecting_student_for_absence"
        else:
            bot.send_message(chat_id, "Список студентов пуст.")
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_student_absence_"))
def receive_student_for_absence(call):
    chat_id = call.message.chat.id
    student_id = int(call.data.split("_")[-1])
    user_data[chat_id]["student_id_for_absence"] = student_id
    user_data[chat_id]["step"] = "awaiting_absence_date"
    bot.send_message(chat_id, "Введите дату в формате ДД.ММ.ГГГГ:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_absence_date")
def receive_absence_date(message):
    chat_id = message.chat.id
    id_teach = user_data[chat_id].get("id_teacher")
    student_id = user_data[chat_id]["student_id_for_absence"]
    date_text = message.text.strip()
    try:
        date_obj = datetime.strptime(date_text, "%d.%m.%Y").date()
        user_data[chat_id]["absence_date"] = date_obj

        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            return
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ocenka FROM ocenki WHERE id_student = %s AND id_teacher = %s AND date = %s",
            (student_id, id_teach, date_obj)
        )
        existing_grade = cursor.fetchone()
        if existing_grade:
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("Да", callback_data="confirm_update_absence_yes"),
                types.InlineKeyboardButton("Нет", callback_data="confirm_update_absence_no")
            )
            bot.send_message(
                chat_id,
                f"У этого студента уже есть оценка на {date_obj.strftime('%d.%m.%Y')}: {existing_grade[0]}.\nОбновить её на Н-ку?",
                reply_markup=markup
            )
            user_data[chat_id]["step"] = "confirming_update_absence"
        else:
            # Вставляем Н-ку
            cursor.execute(
                "INSERT INTO ocenki (id_student, id_teacher, ocenka, date) VALUES (%s, %s, %s, %s)",
                (student_id, id_teach, 0, date_obj)
            )
            conn.commit()

            # Уведомляем студента
            cursor.execute("SELECT chat_id FROM student_chat_id WHERE id_student = %s", (student_id,))
            student_chat_id = cursor.fetchone()
            if student_chat_id:
                student_chat_id = student_chat_id[0]
                cursor.execute("SELECT fio_teacher FROM teachers WHERE id_teacher = %s", (id_teach,))
                teacher_fio = cursor.fetchone()
                teacher_fio = teacher_fio[0] if teacher_fio else "Преподаватель"
                bot.send_message(
                    student_chat_id,
                    f"Вы получили Н-ку от преподавателя {teacher_fio} на дату {date_obj.strftime('%d.%m.%Y')}."
                )
            bot.send_message(chat_id, "Пропуск успешно отмечен.")
            user_data[chat_id]["step"] = "authenticated"
        cursor.close()
        conn.close()
    except ValueError:
        bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ.")

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_update_absence_yes", "confirm_update_absence_no"])
def confirm_update_absence(call):
    chat_id = call.message.chat.id
    id_teach = user_data[chat_id].get("id_teacher")
    student_id = user_data[chat_id].get("student_id_for_absence")
    absence_date = user_data[chat_id].get("absence_date")

    if call.data == "confirm_update_absence_yes":
        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            return
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ocenki SET ocenka = %s WHERE id_student = %s AND id_teacher = %s AND date = %s",
            (0, student_id, id_teach, absence_date)
        )
        conn.commit()

        cursor.execute("SELECT chat_id FROM student_chat_id WHERE id_student = %s", (student_id,))
        student_chat_id = cursor.fetchone()
        if student_chat_id:
            student_chat_id = student_chat_id[0]
            cursor.execute("SELECT fio_teacher FROM teachers WHERE id_teacher = %s", (id_teach,))
            teacher_fio = cursor.fetchone()
            teacher_fio = teacher_fio[0] if teacher_fio else "Преподаватель"
            bot.send_message(
                student_chat_id,
                f"Вы получили Н-ку от преподавателя {teacher_fio} на дату {absence_date.strftime('%d.%m.%Y')}."
            )

        cursor.close()
        conn.close()

        bot.send_message(chat_id, "Оценка успешно обновлена на Н-ку.")
    else:
        bot.send_message(chat_id, "Операция отменена. Оценка не была изменена.")

    user_data[chat_id]["step"] = "authenticated"

@bot.message_handler(func=lambda message: message.text == 'Назад')
def go_back(message):
    chat_id = message.chat.id
    user_data[chat_id]["step"] = "authenticated"
    role = user_data[chat_id].get("role")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == STUDENT_R:
        markup.add(
            'Академическая успеваемость',
            'оценки и GPA',
            'Расписание',
            'Рейтинг',
            'Документы'
        )
    elif role == TEACHER_R:
        markup.add(
            'Расписание',
            'Переносы',
            'Ввод оценок и Н-ок'
        )
    else:
        bot.send_message(chat_id, "Пожалуйста, введите /start для начала работы с ботом.")
        return
    bot.send_message(chat_id, "Вы вернулись в главное меню.", reply_markup=markup)

bot.infinity_polling()