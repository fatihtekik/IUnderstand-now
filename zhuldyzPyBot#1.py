import os
from datetime import datetime
import telebot
from telebot import types
import psycopg2 as psycopg
from telebot.types import ReplyKeyboardRemove

token = '8154463207:AAGRK4G288WXsWcARiPpHujaZVIoYhn9vtY'
bot = telebot.TeleBot(token)

STUDENT_R = 'student'
COACH_R = 'coach'

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

def save_or_update_chat_id(skate_student_id, chat_id):
    # В новой БД хранится chat_id в таблице stud_chat
    # Если запись уже есть, обновим chat_id, если нет - создадим.
    conn = connect_to_db()
    if not conn:
        print("Ошибка подключения к базе данных.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE skate_student_id = %s", (skate_student_id,))
        result = cursor.fetchone()
        if result:
            cursor.execute("UPDATE stud_chat SET skate_chat_id = %s WHERE skate_student_id = %s", (chat_id, skate_student_id))
        else:
            # Нужно знать, к какой группе принадлежит студент, чтобы вставить запись.
            # Предположим, она есть в user_data.
            # Если нет — сделаем запрос:
            cursor.execute("SELECT group_id FROM skating_students WHERE skate_student_id = %s", (skate_student_id,))
            group_id = cursor.fetchone()
            if group_id:
                group_id = group_id[0]
            else:
                group_id = None
            cursor.execute("INSERT INTO stud_chat (skate_student_id, group_id, skate_chat_id) VALUES (%s, %s, %s)", (skate_student_id, group_id, chat_id))
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
        "skate_student_id": None,
        "coach_id": None
    }
    bot.send_message(chat_id, "Добро пожаловать в Жулдыздар! Введите ваш логин.", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "login")
def process_login(message):
    chat_id = message.chat.id
    login = message.text.strip()

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        # Проверяем студента
        cursor.execute("SELECT skate_student_id FROM stud_login WHERE stud_login = %s", (login,))
        student = cursor.fetchone()

        # Проверяем тренера
        cursor.execute("SELECT coach_id FROM coach_login WHERE coach_login = %s", (login,))
        coach = cursor.fetchone()

        if student:
            user_data[chat_id]["step"] = "password"
            user_data[chat_id]["login"] = login
            user_data[chat_id]["skate_student_id"] = student[0]
            user_data[chat_id]["role"] = STUDENT_R
            bot.send_message(chat_id, "Логин студента найден. Введите ваш пароль.")
        elif coach:
            user_data[chat_id]["step"] = "password"
            user_data[chat_id]["login"] = login
            user_data[chat_id]["coach_id"] = coach[0]
            user_data[chat_id]["role"] = COACH_R
            bot.send_message(chat_id, "Логин тренера найден. Введите ваш пароль.")
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
            cursor.execute("SELECT stud_password FROM stud_login WHERE stud_login = %s", (login,))
        elif role == COACH_R:
            cursor.execute("SELECT coach_password FROM coach_login WHERE coach_login = %s", (login,))

        user = cursor.fetchone()

        if user and user[0] == password:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            if role == STUDENT_R:
                # Сохраняем/обновляем chat_id для студента
                save_or_update_chat_id(user_data[chat_id]["skate_student_id"], chat_id)
                # Меню для студента
                markup.add('Посещаемость и "оценки"', 'Расписание', 'Рейтинг', 'Документы')
            elif role == COACH_R:
                markup.add('Расписание', 'Переносы', 'Отметить пропуск/посещаемость')

            bot.send_message(chat_id, "Пароль верный! Добро пожаловать!", reply_markup=markup)
            user_data[chat_id]["step"] = "authenticated"
        else:
            bot.send_message(chat_id, "Неверный пароль. Попробуйте еще раз.")

        cursor.close()
        conn.close()
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")


# В старом коде было статичное расписание. Мы можем оставить что-то похожее.
# Предположим, что расписание завязано на группы. Названия групп у нас в таблице groups.
# Для демонстрации оставим статические словари, но с новыми именами групп:
stud_schedules = {
    # Пусть у нас есть группы с id 1,2,3,4
    # В реальности можно динамически получать данные из БД.
    1: {
        'ПН': ['Тренировка', 'Отработка элементов', 'Растяжка'],
        'ВТ': ['Тренировка', 'Тренировка', 'Отработка элементов'],
        'СР': ['Тренировка', 'Растяжка', 'Тренировка'],
        'ЧТ': ['Отработка элементов', 'Тренировка', 'Растяжка'],
        'ПТ': ['Тренировка', 'Тренировка', 'Тренировка']
    },
    2: {
        'ПН': ['Отработка элементов', 'Растяжка', 'Тренировка'],
        'ВТ': ['Тренировка', 'Тренировка', 'Растяжка'],
        'СР': ['Тренировка', 'Отработка элементов', 'Тренировка'],
        'ЧТ': ['Тренировка', 'Тренировка', 'Отработка элементов'],
        'ПТ': ['Растяжка', 'Отработка элементов', 'Тренировка']
    },
    3: {
        'ПН': ['Растяжка', 'Отработка элементов', 'Тренировка'],
        'ВТ': ['Тренировка', 'Отработка элементов', 'Растяжка'],
        'СР': ['Отработка элементов', 'Тренировка', 'Тренировка'],
        'ЧТ': ['Тренировка', 'Растяжка', 'Отработка элементов'],
        'ПТ': ['Отработка элементов', 'Тренировка', 'Тренировка']
    },
    4: {
        'ПН': ['Тренировка', 'Растяжка', 'Отработка элементов'],
        'ВТ': ['Отработка элементов', 'Отработка элементов', 'Растяжка'],
        'СР': ['Тренировка', 'Тренировка', 'Отработка элементов'],
        'ЧТ': ['Растяжка', 'Тренировка', 'Отработка элементов'],
        'ПТ': ['Отработка элементов', 'Тренировка', 'Растяжка']
    }
}

@bot.message_handler(func=lambda message: message.text == 'Расписание')
def choose_day_for_schedule(message):
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)
    if role == STUDENT_R:
        # Найдем группу студента
        skate_student_id = user_data[chat_id].get("skate_student_id")
        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM skating_students WHERE skate_student_id = %s", (skate_student_id,))
        group_id = cursor.fetchone()
        cursor.close()
        conn.close()
        if not group_id:
            bot.send_message(chat_id, "Не удалось определить вашу группу.")
            return
        group_id = group_id[0]

        user_data[chat_id]["group_id"] = group_id
        markup = types.InlineKeyboardMarkup()
        days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']
        buttons = [types.InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days]
        markup.add(*buttons)
        bot.send_message(chat_id, f'Вы принадлежите к группе с ID {group_id}. Выберите день недели:', reply_markup=markup)
    elif role == COACH_R:
        # Тренер может просматривать расписание по своей группе
        # Определим группы тренера
        coach_id = user_data[chat_id].get("coach_id")
        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM groups WHERE coach_id = %s", (coach_id,))
        groups = cursor.fetchall()
        cursor.close()
        conn.close()

        if not groups:
            bot.send_message(chat_id, "У вас нет прикрепленных групп.")
            return

        markup = types.InlineKeyboardMarkup()
        for g in groups:
            g_id = g[0]
            markup.add(types.InlineKeyboardButton(f"Группа {g_id}", callback_data=f"coach_group_{g_id}"))
        bot.send_message(chat_id, "Выберите группу:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Ваша роль не определена.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("coach_group_"))
def coach_choose_day(call):
    chat_id = call.message.chat.id
    group_id = int(call.data.split("_")[-1])
    user_data[chat_id]["coach_group_id"] = group_id
    markup = types.InlineKeyboardMarkup()
    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']
    buttons = [types.InlineKeyboardButton(day, callback_data=f"coach_day_{day}") for day in days]
    markup.add(*buttons)
    bot.send_message(chat_id, f"Вы выбрали группу {group_id}. Выберите день:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("day_") or call.data.startswith("coach_day_"))
def show_schedule_day(call):
    chat_id = call.message.chat.id
    data = call.data
    if data.startswith("day_"):
        # Для студента
        day = data.split("_")[1]
        group_id = user_data[chat_id]["group_id"]
        sched = stud_schedules.get(group_id, {}).get(day, [])
        if sched:
            schedule_text = '\n'.join([f"{i+1}. {s}" for i, s in enumerate(sched)])
            bot.send_message(chat_id, f"Расписание на {day} для группы {group_id}:\n{schedule_text}")
        else:
            bot.send_message(chat_id, f"На {day} для группы {group_id} нет занятий.")
    else:
        # Для тренера
        day = data.split("_")[2]
        group_id = user_data[chat_id].get("coach_group_id")
        sched = stud_schedules.get(group_id, {}).get(day, [])
        if sched:
            schedule_text = '\n'.join([f"{i+1}. {s}" for i, s in enumerate(sched)])
            bot.send_message(chat_id, f"Расписание на {day} для группы {group_id}:\n{schedule_text}")
        else:
            bot.send_message(chat_id, f"На {day} для группы {group_id} нет занятий.")


def interpret_attendance_value(att):
    # att = '0' -> 0 баллов (пропуск)
    # att = '1' -> 10 баллов
    # ...
    # att = '9' -> 90 баллов
    # Если это не цифра - считаем 0.
    if att.isdigit():
        return int(att)*10
    return 0

def get_gpa_from_score(score):
    # Переводим средний балл в GPA
    # Можно использовать ту же шкалу, что и раньше
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

@bot.message_handler(func=lambda message: message.text == 'Посещаемость и "оценки"')
def show_attendance_scores(message):
    # Аналог "оценки и GPA"
    chat_id = message.chat.id
    skate_student_id = user_data[chat_id].get("skate_student_id")
    if not skate_student_id:
        bot.send_message(chat_id, "ID студента не найден.")
        return

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()

    # Получаем средний балл по тренерам, предполагая, что каждый тренер может считаться "предметом"
    cursor.execute('''
        SELECT coach.coach_name, AVG(CASE WHEN attendance.attendance='0' THEN 0 ELSE CAST(attendance.attendance AS INT)*10 END) as avg_score
        FROM attendance
        JOIN coach ON coach.coach_id = attendance.coach_id
        WHERE attendance.skate_student_id = %s
        GROUP BY coach.coach_name
    ''', (skate_student_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        bot.send_message(chat_id, "Нет данных о посещаемости/оценках.")
        return

    count_s = 0
    total_GPA = 0
    result = ""
    for row in rows:
        coach_name, avg_score = row
        gpa = get_gpa_from_score(avg_score)
        total_GPA += gpa
        count_s += 1
        result += (f"Тренер: {coach_name}\n"
                   f"Средний 'балл': {avg_score:.2f}\nGPA: {gpa:.2f}\n\n")
    if count_s > 0:
        overall_gpa = total_GPA / count_s
        result += f"Средний GPA по всем тренерам: {overall_gpa:.2f}"
    else:
        result += "Нет оценок для расчета среднего GPA."

    bot.send_message(chat_id, result)


@bot.message_handler(func=lambda message: message.text == 'Документы')
def docs(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    docs_add = types.InlineKeyboardButton(text="Загрузить документ", callback_data="docs_add")
    docs_show = types.InlineKeyboardButton(text="Показать документ", callback_data="docs_show")
    markup.add(docs_add, docs_show)
    bot.send_message(chat_id, "Выберите действие с документами:", reply_markup=markup)

def get_docs(skate_student_id):
    conn = connect_to_db()
    if not conn:
        return []
    cursor = conn.cursor()
    query = "SELECT name_file, path_file FROM docs WHERE skate_student_id = %s"
    cursor.execute(query, (skate_student_id,))
    documents = cursor.fetchall()
    cursor.close()
    conn.close()
    document_list = [{'file_name': doc[0], 'file_path': doc[1]} for doc in documents]
    return document_list

def save_file_db(skate_student_id, file_name, file_path):
    conn = connect_to_db()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        query = "INSERT INTO docs (skate_student_id, name_file, path_file) VALUES(%s, %s, %s)"
        cursor.execute(query, (skate_student_id, file_name, file_path))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("docs_"))
def handle_docs_callback(call):
    chat_id = call.message.chat.id
    action = call.data
    role = user_data[chat_id].get("role")
    skate_student_id = user_data[chat_id].get("skate_student_id")

    if action == "docs_add":
        bot.send_message(chat_id, "Отправьте файл вашего документа")

        @bot.message_handler(content_types=['document'])
        def handle_file(message):
            c_id = message.chat.id
            stud_id = user_data[c_id].get("skate_student_id")
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
        if skate_student_id:
            docum = get_docs(skate_student_id)
        else:
            docum = []
        if docum:
            for doc in docum:
                bot.send_message(chat_id, f"Документ: {doc['file_name']}")
                bot.send_document(chat_id, open(doc['file_path'], 'rb'))
        else:
            bot.send_message(chat_id, "Вы не загрузили ни одного документа.")

@bot.message_handler(func=lambda message: message.text == 'Рейтинг')
def reiting(message):
    chat_id = message.chat.id
    skate_student_id = user_data[chat_id].get("skate_student_id")
    if not skate_student_id:
        bot.send_message(chat_id, "ID студента не найден.")
        return

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()
    # Получаем всех студентов и их "оценки" (attendance)
    cursor.execute('''
        SELECT skate_student_id, attendance
        FROM attendance
    ''')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        bot.send_message(chat_id, "Нет данных о посещаемости.")
        return

    students_grades = {}
    for row in rows:
        s_id, att = row
        val = interpret_attendance_value(att)
        if s_id not in students_grades:
            students_grades[s_id] = {"grades": [], "count_zeros": 0}
        students_grades[s_id]["grades"].append(val)
        if val == 0:
            students_grades[s_id]["count_zeros"] += 1

    students_avg = []
    for student_id, data in students_grades.items():
        total_grades = sum(data["grades"])
        total_count = len(data["grades"])
        avg_grade = total_grades / total_count if total_count > 0 else 0
        students_avg.append({"skate_student_id": student_id, "avg_grade": avg_grade, "count_zeros": data["count_zeros"]})

    students_avg.sort(key=lambda x: x["avg_grade"], reverse=True)

    result = ""
    for index, student in enumerate(students_avg):
        rank = index + 1
        avg_grade = student["avg_grade"]
        count_zeros = student["count_zeros"]
        result += f"Место: {rank}.\nСредний балл: {avg_grade:.2f}.   Пропусков: {count_zeros}\n\n"

    user_rank = next((index + 1 for index, student in enumerate(students_avg) if student["skate_student_id"] == skate_student_id), None)
    if user_rank:
        result += f"\nВаше место: {user_rank}.\nСредний балл: {students_avg[user_rank - 1]['avg_grade']:.2f}\n"
    else:
        result += "\nНе удалось найти ваше место в рейтинге."

    bot.send_message(chat_id, result)

@bot.message_handler(func=lambda message: message.text == 'Переносы')
def reschedule_func(message):
    chat_id = message.chat.id
    role = user_data[chat_id].get("role")
    coach_id = user_data[chat_id].get("coach_id")
    if role == STUDENT_R:
        bot.send_message(chat_id, "Этой функцией могут пользоваться только тренеры.")
    elif role == COACH_R:
        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM groups WHERE coach_id = %s", (coach_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if not rows:
            bot.send_message(chat_id, "Нет групп для этого тренера.")
            return
        markup = types.InlineKeyboardMarkup()
        for row in rows:
            g_id = row[0]
            markup.add(types.InlineKeyboardButton(text=f"Группа {g_id}", callback_data=f"perenos_{g_id}"))
        bot.send_message(chat_id, "Выберите группу:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("perenos_"))
def perenos_send_message(call):
    chat_id = call.message.chat.id
    group_id = int(call.data.split("_")[1])
    user_data[chat_id]["perenos"] = {
        "group_id": group_id,
        "process_completed": False
    }
    bot.send_message(chat_id, "Напишите сообщение студентам")

@bot.message_handler(func=lambda message: "perenos" in user_data.get(message.chat.id, {}) and not user_data[message.chat.id]["perenos"]["process_completed"])
def handle_perenos_message(message):
    chat_id = message.chat.id
    text_message = message.text
    group_id = user_data[chat_id]["perenos"]["group_id"]
    coach_id = user_data[chat_id].get("coach_id")

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()

    # Сохраняем перенос в таблицу skate_rescheldue
    try:
        cursor.execute("INSERT INTO skate_rescheldue (group_id, text_message) VALUES (%s, %s)", (group_id, text_message))
        conn.commit()
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка записи в базу данных: {e}")
        cursor.close()
        conn.close()
        return

    # Отправляем сообщение студентам
    try:
        cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE group_id = %s", (group_id,))
        students = cursor.fetchall()
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка получения списка студентов: {e}")
        cursor.close()
        conn.close()
        return

    # Узнаем имя тренера
    cursor.execute("SELECT coach_name FROM coach WHERE coach_id = %s", (coach_id,))
    coach_name = cursor.fetchone()
    coach_name = coach_name[0] if coach_name else "Тренер"

    cursor.close()
    conn.close()

    if not students:
        bot.send_message(chat_id, "В этой группе нет зарегистрированных учеников.")
        user_data[chat_id]["perenos"]["process_completed"] = True
        return

    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

    for student in students:
        student_chat_id = student[0]
        try:
            bot.send_message(
                student_chat_id,
                f"*{coach_name}* отправил сообщение:\n\n_{text_message}_\n\n🕒 Отправлено: {current_time}",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка отправки сообщения пользователю {student_chat_id}: {e}")

    bot.send_message(chat_id, "Сообщение отправлено всем ученикам группы.")
    user_data[chat_id]["perenos"]["process_completed"] = True

@bot.message_handler(func=lambda message: message.text == 'Отметить пропуск/посещаемость' and user_data.get(message.chat.id, {}).get("role") == COACH_R)
def mark_attendance(message):
    chat_id = message.chat.id
    # Переходим к запросу даты
    user_data[chat_id]["step"] = "awaiting_date_for_attendance"
    bot.send_message(chat_id, "Введите дату в формате ДД.ММ.ГГГГ:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_date_for_attendance")
def receive_attendance_date_first(message):
    chat_id = message.chat.id
    coach_id = user_data[chat_id].get("coach_id")
    date_text = message.text.strip()

    # Парсим дату
    try:
        date_obj = datetime.strptime(date_text, "%d.%m.%Y").date()
    except ValueError:
        bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ.")
        return

    # Сохраняем дату в user_data
    user_data[chat_id]["attendance_date"] = date_obj

    # Теперь получаем список студентов тренера
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        user_data[chat_id]["step"] = "authenticated"
        return

    cursor = conn.cursor()
    cursor.execute('''
        SELECT skating_students.skate_student_id, skating_students.fullname
        FROM groups
        JOIN skating_students ON skating_students.group_id = groups.group_id
        WHERE groups.coach_id = %s
    ''', (coach_id,))
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    if students:
        # Переходим в состояние, когда дата уже выбрана, и мы можем многократно выставлять оценки
        user_data[chat_id]["step"] = "date_selected_for_attendance"
        show_students_list_for_date(chat_id, students)
    else:
        bot.send_message(chat_id, "Список студентов пуст.")
        user_data[chat_id]["step"] = "authenticated"


def show_students_list_for_date(chat_id, students):
    # Функция для отображения списка студентов
    date_obj = user_data[chat_id]["attendance_date"]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for student_id, fio in students:
        markup.add(types.InlineKeyboardButton(text=fio, callback_data=f"attendance_student_{student_id}"))
    bot.send_message(chat_id, f"Дата: {date_obj.strftime('%d.%m.%Y')}\nВыберите студента для отметки посещаемости:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("attendance_student_") and user_data.get(call.message.chat.id, {}).get("step") == "date_selected_for_attendance")
def attendance_student_selected(call):
    chat_id = call.message.chat.id
    student_id = int(call.data.split("_")[-1])
    user_data[chat_id]["attendance_student_id"] = student_id
    # Переходим к вводу оценки
    user_data[chat_id]["step"] = "awaiting_attendance_value"
    bot.send_message(chat_id, "Введите значение посещаемости (0-пропуск, 1..9 - разные 'оценки'):")


@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_attendance_value")
def receive_attendance_value(message):
    chat_id = message.chat.id
    coach_id = user_data[chat_id].get("coach_id")
    val = message.text.strip()
    if not val.isdigit() or not (0 <= int(val) <= 9):
        bot.send_message(chat_id, "Введите число от 0 до 9.")
        return

    attendance_value = val
    student_id = user_data[chat_id]["attendance_student_id"]
    date_obj = user_data[chat_id]["attendance_date"]

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        user_data[chat_id]["step"] = "authenticated"
        return
    cursor = conn.cursor()
    # Проверяем есть ли уже запись на эту дату
    cursor.execute(
        "SELECT attendance FROM attendance WHERE skate_student_id = %s AND coach_id = %s AND date = %s",
        (student_id, coach_id, date_obj)
    )
    existing_record = cursor.fetchone()
    if existing_record:
        # Обновляем
        cursor.execute(
            "UPDATE attendance SET attendance = %s WHERE skate_student_id = %s AND coach_id = %s AND date = %s",
            (attendance_value, student_id, coach_id, date_obj)
        )
        conn.commit()
        bot.send_message(chat_id, "Посещаемость успешно обновлена.")
    else:
        # Вставляем новую запись
        cursor.execute(
            "INSERT INTO attendance (attendance, skate_student_id, coach_id, date) VALUES (%s, %s, %s, %s)",
            (attendance_value, student_id, coach_id, date_obj)
        )
        conn.commit()
        bot.send_message(chat_id, "Посещаемость успешно отмечена.")

    # Уведомляем студента
    cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE skate_student_id = %s", (student_id,))
    student_chat_id = cursor.fetchone()
    if student_chat_id:
        student_chat_id = student_chat_id[0]
        cursor.execute("SELECT coach_name FROM coach WHERE coach_id = %s", (coach_id,))
        coach_name = cursor.fetchone()
        coach_name = coach_name[0] if coach_name else "Тренер"
        mark_text = "пропуск" if attendance_value == '0' else f"оценка {int(attendance_value)*10}"
        bot.send_message(
            student_chat_id,
            f"Отметка от {coach_name} на дату {date_obj.strftime('%d.%m.%Y')}: {mark_text}."
        )

    cursor.close()
    conn.close()

    # Возвращаемся в состояние, когда дата выбрана, чтобы вновь выбрать другого студента
    user_data[chat_id]["step"] = "date_selected_for_attendance"

    # Снова показываем список студентов (дата остаётся)
    coach_id = user_data[chat_id].get("coach_id")
    if coach_id:
        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT skating_students.skate_student_id, skating_students.fullname
                FROM groups
                JOIN skating_students ON skating_students.group_id = groups.group_id
                WHERE groups.coach_id = %s
            ''', (coach_id,))
            students = cursor.fetchall()
            cursor.close()
            conn.close()
            if students:
                show_students_list_for_date(chat_id, students)
            else:
                bot.send_message(chat_id, "Список студентов пуст.")
                user_data[chat_id]["step"] = "authenticated"
        else:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            user_data[chat_id]["step"] = "authenticated"
    else:
        user_data[chat_id]["step"] = "authenticated"


@bot.message_handler(func=lambda message: message.text == 'Назад')
def go_back(message):
    chat_id = message.chat.id
    user_data[chat_id]["step"] = "authenticated"
    role = user_data[chat_id].get("role")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == STUDENT_R:
        markup.add(
            'Посещаемость и "оценки"',
            'Расписание',
            'Рейтинг',
            'Документы'
        )
    elif role == COACH_R:
        markup.add(
            'Расписание',
            'Переносы',
            'Отметить пропуск/посещаемость'
        )
    else:
        bot.send_message(chat_id, "Пожалуйста, введите /start для начала.")
        return
    bot.send_message(chat_id, "Вы вернулись в главное меню.", reply_markup=markup)

bot.infinity_polling()
