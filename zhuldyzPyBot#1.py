import logging
import os
import json  # Добавлен импорт json
from datetime import datetime
import telebot
from telebot import types
import psycopg2 as psycopg
from telebot.types import ReplyKeyboardRemove

def get_element_name(element_id):
    conn = connect_to_db()
    if not conn:
        logging.error(f"Не удалось подключиться к базе данных для получения имени элемента {element_id}.")
        return "Неизвестный элемент"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM elements WHERE element_id = %s", (element_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return result[0]
        else:
            return "Неизвестный элемент"
    except Exception as e:
        logging.error(f"Ошибка при получении имени элемента {element_id}: {e}")
        cursor.close()
        conn.close()
        return "Неизвестный элемент"

def send_notification(student_id, message):
    """
    Отправляет уведомление студенту по его skate_student_id.

    :param student_id: ID студента (skate_student_id)
    :param message: Текст уведомления
    """
    conn = connect_to_db()
    if not conn:
        logging.error(f"Не удалось подключиться к базе данных для отправки уведомления студенту {student_id}.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE skate_student_id = %s", (student_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result and result[0]:
            chat_id = result[0]
            bot.send_message(chat_id, message, parse_mode="Markdown")
            logging.info(f"Уведомление отправлено студенту {student_id} (chat_id: {chat_id}).")
        else:
            logging.warning(f"Chat ID для студента {student_id} не найден.")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления студенту {student_id}: {e}")
        cursor.close()
        conn.close()


token = '8154463207:AAGRK4G288WXsWcARiPpHujaZVIoYhn9vtY'
bot = telebot.TeleBot(token)

STUDENT_R = 'student'
COACH_R = 'coach'
ADMIN_R = 'admin'

if not os.path.exists('documents'):
    os.makedirs('documents')

user_data = {}

def attendance_status_str(value):
    if value == '0':
        return "Н-ка"
    elif value == '1':
        return "Опоздал"
    elif value == '2':
        return "Пришел"
    else:
        return "Неизвестный статус"

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
            # Роль определим после ввода пароля
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
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return

    cursor = conn.cursor()

    if role == STUDENT_R:
        cursor.execute("SELECT stud_password FROM stud_login WHERE stud_login = %s", (login,))
        user = cursor.fetchone()
        if user and user[0] == password:
            # Студент авторизован
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            save_or_update_chat_id(user_data[chat_id]["skate_student_id"], chat_id)
            markup.add('Посещаемость и "оценки"', 'Расписание', 'Оценки Прыжков', 'Документы')
            bot.send_message(chat_id, "Пароль верный! Добро пожаловать!", reply_markup=markup)
            user_data[chat_id]["step"] = "authenticated"
        else:
            bot.send_message(chat_id, "Неверный пароль. Попробуйте еще раз.")

    else:
        # Тренер или админ
        cursor.execute("SELECT coach_id, coach_password FROM coach_login WHERE coach_login = %s", (login,))
        coach_data = cursor.fetchone()
        if coach_data and coach_data[1] == password:
            coach_id = coach_data[0]
            user_data[chat_id]["coach_id"] = coach_id

            # Определяем роль тренера из таблицы roles
            cursor.execute("SELECT role FROM roles WHERE coach_id = %s", (coach_id,))
            r = cursor.fetchone()
            if r:
                user_role = r[0]
            else:
                user_role = COACH_R  # по умолчанию coach, если нет записи

            user_data[chat_id]["role"] = user_role

            # Получаем имя тренера
            cursor.execute("SELECT coach_name FROM coach WHERE coach_id = %s", (coach_id,))
            c_name = cursor.fetchone()
            c_name = c_name[0] if c_name else None
            user_data[chat_id]["coach_name"] = c_name

            # Формируем меню
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            if user_role == ADMIN_R:
                # Администратор
                # Предположим админ может всё: просмотр всех групп, переносы, отметки, расписание, документы
                markup.add('Просмотр всех групп', 'Просмотр посещаемости', 'Переносы',
                           'Отметить пропуск/посещаемость','Оценки Прыжков', 'Расписание', 'Документы')

            else:
                # Обычный тренер
                # Если имя тренера Ясмин, даём доступ к переносам
                if c_name == 'Ясмин':
                    markup.add('Расписание','Оценки Прыжков', 'Переносы', 'Отметить пропуск/посещаемость')
                else:
                    # Обычный тренер без переносов
                    markup.add('Расписание','Оценки Прыжков', 'Отметить пропуск/посещаемость')

            bot.send_message(chat_id, "Пароль верный! Добро пожаловать!", reply_markup=markup)
            user_data[chat_id]["step"] = "authenticated"
        else:
            bot.send_message(chat_id, "Неверный пароль. Попробуйте еще раз.")

    cursor.close()
    conn.close()

# Расписания групп (упрощены для примера)
stud_schedules = {
    1: {
        'ПН': ['17:45–18:45 лед', '18:55–19:55 ОФП'],
        'ВТ': [],
        'СР': ['17:45–18:45 лед', '18:55–19:55 ОФП'],
        'ЧТ': [],
        'ПТ': ['17:15–18:15 лед', '18:30–19:30 ОФП/акробатика'],
        'СБ': [],
        'ВС': ['15:30–16:30 СФП/растяжка', '16:45–17:45 лед']
    },
    2: {
        'ПН': ['17:45–18:45 лед', '18:55–19:55 ОФП'],
        'ВТ': [],
        'СР': ['17:45–18:45 лед', '18:55–19:55 ОФП'],
        'ЧТ': [],
        'ПТ': ['17:15–18:15 лед', '18:30–19:30 ОФП/акробатика'],
        'СБ': [],
        'ВС': ['15:30–16:30 СФП/растяжка', '16:45–17:45 лед']
    },
    3: {
        'ПН': ['17:45–18:45 лед', '18:55–19:55 ОФП'],
        'ВТ': ['Тренировка', 'Отработка элементов', 'Растяжка'],
        'СР': ['17:45–18:45 лед', '18:55–19:55 ОФП'],
        'ЧТ': ['Тренировка', 'Растяжка', 'Отработка элементов'],
        'ПТ': ['17:15–18:15 лед', '18:30–19:30 ОФП/акробатика'],
        'СБ': [],
        'ВС': ['15:30–16:30 СФП/растяжка', '16:45–17:45 лед']
    },
    4: {
        'ПН': ['17:45–18:45 лед', '18:55–19:55 ОФП'],
        'ВТ': [],
        'СР': ['17:45–18:45 лед', '18:55–19:55 ОФП'],
        'ЧТ': [],
        'ПТ': ['17:15–18:15 лед', '18:30–19:30 ОФП/акробатика'],
        'СБ': [],
        'ВС': ['15:30–16:30 СФП/растяжка', '16:45–17:45 лед']
    }
}

@bot.message_handler(func=lambda message: message.text == 'Расписание')
def choose_day_for_schedule(message):
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)
    if role == STUDENT_R:
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
        days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ','СБ','ВС']
        buttons = [types.InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days]
        markup.add(*buttons)
        bot.send_message(chat_id, f'Вы принадлежите к группе с ID {group_id}. Выберите день недели:', reply_markup=markup)

    elif role == COACH_R or role == ADMIN_R:
        # Тренер или админ может смотреть расписание своих групп или все (если admin).
        coach_id = user_data[chat_id].get("coach_id")
        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            return
        cursor = conn.cursor()

        if role == ADMIN_R:
            # Админ видит все группы
            cursor.execute("SELECT group_id FROM groups")
        else:
            # Обычный тренер - только свои
            cursor.execute("SELECT group_id FROM groups WHERE coach_id = %s", (coach_id,))
        groups = cursor.fetchall()
        cursor.close()
        conn.close()

        if not groups:
            bot.send_message(chat_id, "Нет прикрепленных групп.")
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
    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ','СБ','ВС']
    buttons = [types.InlineKeyboardButton(day, callback_data=f"coach_day_{day}") for day in days]
    markup.add(*buttons)
    bot.send_message(chat_id, f"Вы выбрали группу {group_id}. Выберите день:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("day_") or call.data.startswith("coach_day_"))
def show_schedule_day(call):
    chat_id = call.message.chat.id
    data = call.data
    if data.startswith("day_"):
        day = data.split("_")[1]
        group_id = user_data[chat_id]["group_id"]
        sched = stud_schedules.get(group_id, {}).get(day, [])
        if sched:
            schedule_text = '\n'.join([f"{i+1}. {s}" for i, s in enumerate(sched)])
            bot.send_message(chat_id, f"Расписание на {day} для группы {group_id}:\n{schedule_text}")
        else:
            bot.send_message(chat_id, f"На {day} для группы {group_id} нет занятий.")
    else:
        day = data.split("_")[2]
        group_id = user_data[chat_id].get("coach_group_id")
        sched = stud_schedules.get(group_id, {}).get(day, [])
        if sched:
            schedule_text = '\n'.join([f"{i+1}. {s}" for i, s in enumerate(sched)])
            bot.send_message(chat_id, f"Расписание на {day} для группы {group_id}:\n{schedule_text}")
        else:
            bot.send_message(chat_id, f"На {day} для группы {group_id} нет занятий.")

@bot.message_handler(func=lambda message: message.text == 'Посещаемость и "оценки"')
def show_attendance_scores(message):
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

    cursor.execute('''
        SELECT coach.coach_name,
               SUM(CASE WHEN attendance.attendance = '0' THEN 1 ELSE 0 END) AS count_n,
               SUM(CASE WHEN attendance.attendance = '1' THEN 1 ELSE 0 END) AS count_late,
               SUM(CASE WHEN attendance.attendance = '2' THEN 1 ELSE 0 END) AS count_present
        FROM attendance
        JOIN coach ON coach.coach_id = attendance.coach_id
        WHERE attendance.skate_student_id = %s
        GROUP BY coach.coach_name
    ''', (skate_student_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        bot.send_message(chat_id, "Нет данных о посещаемости.")
        return

    result = ""
    for row in rows:
        coach_name, count_n, count_late, count_present = row
        result += (f"Тренер: {coach_name}\n"
                   f"Н-ок: {count_n}\n"
                   f"Опоздал: {count_late}\n"
                   f"Пришел: {count_present}\n\n")

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
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("docs_"))
def handle_docs_callback(call):
    chat_id = call.message.chat.id
    action = call.data
    skate_student_id = user_data[chat_id].get("skate_student_id")

    if action == "docs_add":
        bot.send_message(chat_id, "Отправьте файл вашего документа")
        @bot.message_handler(content_types=['document'])
        def handle_file(message):
            c_id = message.chat.id
            stud_id = user_data[c_id].get("skate_student_id")
            if message.document:
                try:
                    file_info = bot.get_file(message.document.file_id)
                    downloaded_file = bot.download_file(file_info.file_path)
                    save_path = os.path.join("documents", message.document.file_name)
                    with open(save_path, 'wb') as new_file:
                        new_file.write(downloaded_file)
                    file_name = message.document.file_name
                    save_file_db(stud_id, file_name, save_path)
                    bot.reply_to(message, f'Файл {file_name} сохранен.')
                except Exception as e:
                    bot.send_message(c_id, f"Ошибка при сохранении файла: {e}")
            else:
                bot.send_message(c_id, "Документ должен быть в виде файла")
    elif action == "docs_show":
        if skate_student_id:
            docum = get_docs(skate_student_id)
        else:
            docum = []
        if docum:
            for doc in docum:
                try:
                    bot.send_message(chat_id, f"Документ: {doc['file_name']}")
                    with open(doc['file_path'], 'rb') as file:
                        bot.send_document(chat_id, file)
                except Exception as e:
                    bot.send_message(chat_id, f"Ошибка при отправке документа {doc['file_name']}: {e}")
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
    cursor.execute('SELECT skate_student_id, attendance FROM attendance')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        bot.send_message(chat_id, "Нет данных о посещаемости.")
        return

    # Рейтинг по средней "оценке"
    students_grades = {}
    for row in rows:
        s_id, att = row
        val = 0 if att == '0' else (10 if att == '1' else (20 if att == '2' else 0))
        if s_id not in students_grades:
            students_grades[s_id] = {"grades": [], "count_zeros": 0}
        students_grades[s_id]["grades"].append(val)
        if val == 0:
            students_grades[s_id]["count_zeros"] += 1

    students_avg = []
    for s_id, data in students_grades.items():
        total_grades = sum(data["grades"])
        total_count = len(data["grades"])
        avg_grade = total_grades / total_count if total_count > 0 else 0
        students_avg.append({"skate_student_id": s_id, "avg_grade": avg_grade, "count_zeros": data["count_zeros"]})

    students_avg.sort(key=lambda x: x["avg_grade"], reverse=True)

    result = ""
    for index, student in enumerate(students_avg):
        rank = index + 1
        avg_grade = student["avg_grade"]
        count_zeros = student["count_zeros"]
        result += f"Место: {rank}.\nСредний балл: {avg_grade:.2f}.   Пропусков: {count_zeros}\n\n"

    user_rank = next((index + 1 for index, s in enumerate(students_avg) if s["skate_student_id"] == skate_student_id), None)
    if user_rank:
        result += f"\nВаше место: {user_rank}.\nСредний балл: {students_avg[user_rank - 1]['avg_grade']:.2f}\n"
    else:
        result += "\nНе удалось найти ваше место в рейтинге."

    bot.send_message(chat_id, result)

@bot.message_handler(func=lambda message: message.text == 'Переносы')
def reschedule_func(message):
    chat_id = message.chat.id
    user_role = user_data[chat_id].get("role")
    coach_name = user_data[chat_id].get("coach_name")
    coach_id = user_data[chat_id].get("coach_id")

    # Переносы доступны, если user_role = admin или coach_name = 'Ясмин'
    if user_role == ADMIN_R or coach_name == 'Ясмин':
        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM groups")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if not rows:
            bot.send_message(chat_id, "Нет групп для просмотра.")
            return
        markup = types.InlineKeyboardMarkup()
        groups_name = ['Старшая', 'Средняя', 'Младшая Фатих', 'Младшая Салима']
        for row in rows:
            g_id = row[0]
            # Учитываем, что group_id начинается с 1, а индексы списка с 0
            group_name = groups_name[g_id - 1] if 0 < g_id <= len(groups_name) else f"Группа {g_id}"
            markup.add(types.InlineKeyboardButton(text=group_name, callback_data=f"perenos_{g_id}"))
        bot.send_message(chat_id, "Выберите группу:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Этой функцией могут пользоваться только главный или тренер Ясмин.")

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

    try:
        cursor.execute("INSERT INTO skate_rescheldue (group_id, text_message) VALUES (%s, %s)", (group_id, text_message))
        conn.commit()
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка записи в базу данных: {e}")
        cursor.close()
        conn.close()
        return

    try:
        cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE group_id = %s", (group_id,))
        students = cursor.fetchall()
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка получения списка студентов: {e}")
        cursor.close()
        conn.close()
        return

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
                f"Тренер *{coach_name}* отправил сообщение:\n\n_{text_message}_\n\n🕒 Отправлено: {current_time}",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка отправки сообщения пользователю {student_chat_id}: {e}")

    bot.send_message(chat_id, "Сообщение отправлено всем ученикам группы.")
    user_data[chat_id]["perenos"]["process_completed"] = True

@bot.message_handler(func=lambda message: message.text == 'Отметить пропуск/посещаемость' and user_data.get(message.chat.id, {}).get("role") in [COACH_R, ADMIN_R])
def mark_attendance(message):
    chat_id = message.chat.id
    user_data[chat_id]["step"] = "awaiting_date_for_attendance"
    bot.send_message(chat_id, "Введите дату в формате ДД.ММ.ГГГГ:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_date_for_attendance")
def receive_attendance_date_first(message):
    chat_id = message.chat.id
    coach_id = user_data[chat_id].get("coach_id")
    date_text = message.text.strip()

    try:
        date_obj = datetime.strptime(date_text, "%d.%m.%Y").date()
    except ValueError:
        bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ.")
        return

    user_data[chat_id]["attendance_date"] = date_obj

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        user_data[chat_id]["step"] = "authenticated"
        return

    cursor = conn.cursor()
    # Если admin, видит все группы студентов
    if user_data[chat_id]["role"] == ADMIN_R:
        cursor.execute('''
            SELECT skating_students.skate_student_id, skating_students.fullname
            FROM skating_students
        ''')
    else:
        # Обычный тренер видит только своих
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
        user_data[chat_id]["step"] = "date_selected_for_attendance"
        show_students_list_for_date(chat_id, students)
    else:
        bot.send_message(chat_id, "Список студентов пуст.")
        user_data[chat_id]["step"] = "authenticated"

def show_students_list_for_date(chat_id, students):
    date_obj = user_data[chat_id]["attendance_date"]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for student_id, fio in students:
        markup.add(types.InlineKeyboardButton(text=fio, callback_data=f"attendance_student_{student_id}"))
    # Добавляем кнопку "Отметить всех"
    markup.add(types.InlineKeyboardButton(text="Отметить всех", callback_data="attendance_mark_all"))
    bot.send_message(chat_id, f"Дата: {date_obj.strftime('%d.%m.%Y')}\nВыберите студента для отметки посещаемости или отметьте всех:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("attendance_student_") and user_data.get(call.message.chat.id, {}).get("step") == "date_selected_for_attendance")
def attendance_student_selected(call):
    chat_id = call.message.chat.id
    student_id = int(call.data.split("_")[-1])
    user_data[chat_id]["attendance_student_id"] = student_id
    user_data[chat_id]["step"] = "awaiting_attendance_value"
    bot.send_message(chat_id, "Введите значение посещаемости (0-пропуск, 1-опоздал, 2-пришел:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_attendance_value")
def receive_attendance_value(message):
    chat_id = message.chat.id
    coach_id = user_data[chat_id].get("coach_id")
    val = message.text.strip()

    if not val.isdigit() or val not in ['0','1','2']:
        bot.send_message(chat_id, "Введите 0 (Н-ка), 1 (Опоздал) или 2 (Пришел).")
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
    cursor.execute(
        "SELECT attendance FROM attendance WHERE skate_student_id = %s AND coach_id = %s AND date = %s",
        (student_id, coach_id, date_obj)
    )
    existing_record = cursor.fetchone()

    if existing_record:
        user_data[chat_id]["new_attendance_value"] = attendance_value
        existing_status = attendance_status_str(existing_record[0])
        new_status = attendance_status_str(attendance_value)

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("Да, обновить", callback_data="confirm_update_yes"),
            types.InlineKeyboardButton("Нет, отмена", callback_data="confirm_update_no")
        )

        bot.send_message(
            chat_id,
            f"На дату {date_obj.strftime('%d.%m.%Y')} у ученика уже есть отметка: {existing_status}.\nОбновить её на {new_status}?",
            reply_markup=markup
        )
        user_data[chat_id]["step"] = "confirming_update_attendance"
    else:
        cursor.execute(
            "INSERT INTO attendance (attendance, skate_student_id, coach_id, date) VALUES (%s, %s, %s, %s)",
            (attendance_value, student_id, coach_id, date_obj)
        )
        conn.commit()
        bot.send_message(chat_id, "Посещаемость успешно отмечена.")
        notify_student_about_mark(chat_id, student_id, coach_id, attendance_value, date_obj)
        cursor.close()
        conn.close()
        user_data[chat_id]["step"] = "date_selected_for_attendance"
        show_students_list_again(chat_id, coach_id)

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_update_yes", "confirm_update_no"] and user_data.get(call.message.chat.id, {}).get("step") == "confirming_update_attendance")
def confirm_update_attendance(call):
    chat_id = call.message.chat.id
    coach_id = user_data[chat_id].get("coach_id")
    student_id = user_data[chat_id]["attendance_student_id"]
    date_obj = user_data[chat_id]["attendance_date"]
    attendance_value = user_data[chat_id]["new_attendance_value"]

    conn = connect_to_db()
    cursor = conn.cursor()

    if call.data == "confirm_update_yes":
        cursor.execute(
            "UPDATE attendance SET attendance = %s WHERE skate_student_id = %s AND coach_id = %s AND date = %s",
            (attendance_value, student_id, coach_id, date_obj)
        )
        conn.commit()
        bot.send_message(chat_id, "Посещаемость успешно обновлена.")
        notify_student_about_mark(chat_id, student_id, coach_id, attendance_value, date_obj)
    else:
        bot.send_message(chat_id, "Обновление отменено.")

    cursor.close()
    conn.close()

    user_data[chat_id]["step"] = "date_selected_for_attendance"
    show_students_list_again(chat_id, coach_id)

def notify_student_about_mark(chat_id, student_id, coach_id, attendance_value, date_obj):
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE skate_student_id = %s", (student_id,))
        student_chat_id = cursor.fetchone()
        if student_chat_id:
            student_chat_id = student_chat_id[0]
            cursor.execute("SELECT coach_name FROM coach WHERE coach_id = %s", (coach_id,))
            coach_name = cursor.fetchone()
            coach_name = coach_name[0] if coach_name else "Тренер"

            if attendance_value == '0':
                mark_text = "Н-ка"
            elif attendance_value == '1':
                mark_text = "Опоздал"
            elif attendance_value == '2':
                mark_text = "Пришел"
            else:
                mark_text = "Неизвестный статус"

            bot.send_message(
                student_chat_id,
                f"Отметка от тренера {coach_name} на дату {date_obj.strftime('%d.%m.%Y')}: {mark_text}."
            )
        cursor.close()
        conn.close()

@bot.callback_query_handler(
    func=lambda call: call.data == "attendance_mark_all" and user_data.get(call.message.chat.id, {}).get(
        "step") == "date_selected_for_attendance")
def attendance_mark_all(call):
    chat_id = call.message.chat.id
    user_data[chat_id]["step"] = "awaiting_mark_all_value"

    # Создаем клавиатуру с вариантами посещаемости
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("Н-ка (0)", callback_data="mark_all_0"),
        types.InlineKeyboardButton("Опоздал (1)", callback_data="mark_all_1"),
        types.InlineKeyboardButton("Пришел (2)", callback_data="mark_all_2")
    )

    bot.send_message(chat_id, "Выберите значение посещаемости для всех студентов:", reply_markup=markup)

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("mark_all_") and user_data.get(call.message.chat.id, {}).get(
        "step") == "awaiting_mark_all_value")
def process_mark_all(call):
    chat_id = call.message.chat.id
    mark_value = call.data.split("_")[-1]  # Получаем значение: '0', '1', '2'
    date_obj = user_data[chat_id].get("attendance_date")
    coach_id = user_data[chat_id].get("coach_id")
    role = user_data[chat_id].get("role")

    # Получаем список студентов
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        user_data[chat_id]["step"] = "authenticated"
        return

    cursor = conn.cursor()
    try:
        if role == ADMIN_R:
            # Администратор видит всех студентов
            cursor.execute('SELECT skate_student_id, fullname FROM skating_students')
        else:
            # Тренер видит только своих студентов
            cursor.execute('''
                SELECT skating_students.skate_student_id, skating_students.fullname
                FROM groups
                JOIN skating_students ON skating_students.group_id = groups.group_id
                WHERE groups.coach_id = %s
            ''', (coach_id,))
        students = cursor.fetchall()
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка получения списка студентов: {e}")
        cursor.close()
        conn.close()
        user_data[chat_id]["step"] = "authenticated"
        return

    if not students:
        bot.send_message(chat_id, "Список студентов пуст.")
        cursor.close()
        conn.close()
        user_data[chat_id]["step"] = "authenticated"
        return

    # Обновляем посещаемость для всех студентов
    try:
        for student_id, fio in students:
            # Проверяем, существует ли запись посещаемости
            cursor.execute(
                "SELECT attendance FROM attendance WHERE skate_student_id = %s AND coach_id = %s AND date = %s",
                (student_id, coach_id, date_obj)
            )
            existing_record = cursor.fetchone()
            if existing_record:
                cursor.execute(
                    "UPDATE attendance SET attendance = %s WHERE skate_student_id = %s AND coach_id = %s AND date = %s",
                    (mark_value, student_id, coach_id, date_obj)
                )
            else:
                cursor.execute(
                    "INSERT INTO attendance (attendance, skate_student_id, coach_id, date) VALUES (%s, %s, %s, %s)",
                    (mark_value, student_id, coach_id, date_obj)
                )
        conn.commit()
        bot.send_message(chat_id,
                         f"Посещаемость успешно отмечена для всех студентов с значением '{attendance_status_str(mark_value)}'.")

        # Уведомляем студентов
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

        for student_id, fio in students:
            # Получаем chat_id студента
            cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE skate_student_id = %s", (student_id,))
            student_chat = cursor.fetchone()
            if student_chat:
                student_chat_id = student_chat[0]
                # Получаем имя тренера
                cursor.execute("SELECT coach_name FROM coach WHERE coach_id = %s", (coach_id,))
                coach_name = cursor.fetchone()
                coach_name = coach_name[0] if coach_name else "Тренер"

                # Отправляем сообщение студенту
                try:
                    bot.send_message(
                        student_chat_id,
                        f"Отметка от тренера *{coach_name}* на дату {date_obj.strftime('%d.%m.%Y')}: {attendance_status_str(mark_value)}.\n🕒 Отправлено: {current_time}",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Ошибка отправки уведомления студенту {student_chat_id}: {e}")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при обновлении посещаемости: {e}")
    finally:
        cursor.close()
        conn.close()
        user_data[chat_id]["step"] = "authenticated"

def show_students_list_again(chat_id, coach_id):
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        # Если admin - все студенты, иначе только студенты тренера
        if user_data[chat_id]["role"] == ADMIN_R:
            cursor.execute('SELECT skate_student_id, fullname FROM skating_students')
        else:
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
            markup = types.InlineKeyboardMarkup(row_width=1)
            for s_id, fio in students:
                markup.add(types.InlineKeyboardButton(text=fio, callback_data=f"attendance_student_{s_id}"))
            date_obj = user_data[chat_id]["attendance_date"]
            bot.send_message(chat_id, f"Дата: {date_obj.strftime('%d.%m.%Y')}\nВыберите студента для отметки посещаемости:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Список студентов пуст.")
            user_data[chat_id]["step"] = "authenticated"
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        user_data[chat_id]["step"] = "authenticated"

@bot.message_handler(func=lambda message: message.text == 'Просмотр всех групп' and user_data.get(message.chat.id, {}).get("role") == ADMIN_R)
def view_all_groups(message):
    chat_id = message.chat.id
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()
    cursor.execute("SELECT group_id, id_category, coach_id FROM groups")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    if not rows:
        bot.send_message(chat_id, "Нет групп.")
        return
    result = "Все группы:\n"
    for r in rows:
        g_id, cat_id, c_id = r
        result += f"Группа {g_id}, Категория {cat_id}, Тренер {c_id}\n"
    bot.send_message(chat_id, result)

@bot.message_handler(
    func=lambda message: message.text == 'Просмотр посещаемости' and user_data.get(message.chat.id, {}).get(
        "role") == ADMIN_R)
def view_attendance_for_admin(message):
    chat_id = message.chat.id
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT groups.group_id, category.category_name, coach.coach_name 
        FROM groups 
        JOIN category ON groups.id_category = category.id_category 
        JOIN coach ON groups.coach_id = coach.coach_id
    """)
    groups = cursor.fetchall()
    cursor.close()
    conn.close()

    if not groups:
        bot.send_message(chat_id, "Нет групп для просмотра.")
        return

    markup = types.InlineKeyboardMarkup()
    for group in groups:
        group_id, category_name, coach_name = group
        button_text = f"Группа {group_id} ({category_name}) - Тренер: {coach_name}"
        markup.add(
            types.InlineKeyboardButton(text=button_text, callback_data=f"admin_view_attendance_group_{group_id}"))

    # Добавляем кнопку для выбора всех групп
    markup.add(types.InlineKeyboardButton(text="Все группы", callback_data="admin_view_attendance_all_groups"))

    bot.send_message(chat_id, "Выберите группу для просмотра посещаемости или выберите 'Все группы':",
                     reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_view_attendance_group_") or call.data == "admin_view_attendance_all_groups")
def admin_select_group(call):
    chat_id = call.message.chat.id
    if call.data == "admin_view_attendance_all_groups":
        user_data[chat_id]["selected_group_id"] = "all"
    else:
        group_id = int(call.data.split("_")[-1])
        user_data[chat_id]["selected_group_id"] = group_id
    user_data[chat_id]["step"] = "awaiting_attendance_date_range"
    bot.send_message(chat_id, "Введите дату или интервал дат в формате:\n1) Для одной даты: ДД.ММ.ГГГГ\n2) Для интервала: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ")

@bot.message_handler(
    func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_attendance_date_range")
def process_date_range(message):
    chat_id = message.chat.id
    date_input = message.text.strip()
    group_id = user_data[chat_id].get("selected_group_id")

    try:
        if "-" in date_input:
            # Интервал дат
            start_date, end_date = date_input.split("-")
            start_date = datetime.strptime(start_date.strip(), "%d.%m.%Y").date()
            end_date = datetime.strptime(end_date.strip(), "%d.%m.%Y").date()
        else:
            # Одна дата
            start_date = end_date = datetime.strptime(date_input, "%d.%m.%Y").date()
    except ValueError:
        bot.send_message(chat_id, "Неверный формат даты. Попробуйте снова.")
        return

    user_data[chat_id]["start_date"] = start_date
    user_data[chat_id]["end_date"] = end_date

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return

    cursor = conn.cursor()

    if group_id == "all":
        # Получаем информацию обо всех группах
        cursor.execute("""
            SELECT groups.group_id, category.category_name, coach.coach_name 
            FROM groups 
            JOIN category ON groups.id_category = category.id_category 
            JOIN coach ON groups.coach_id = coach.coach_id
        """)
        all_groups = cursor.fetchall()

        if not all_groups:
            bot.send_message(chat_id, "Нет групп для просмотра.")
            cursor.close()
            conn.close()
            return

        result = f"📅 Посещаемость для всех групп\n📆 Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n\n"

        for grp in all_groups:
            grp_id, category_name, coach_name = grp
            result += f"🔹 Группа {grp_id} ({category_name}) - Тренер: {coach_name}\n"

            cursor.execute("""
                SELECT skating_students.fullname, attendance.date, attendance.attendance, coach.coach_name
                FROM attendance
                JOIN skating_students ON attendance.skate_student_id = skating_students.skate_student_id
                JOIN coach ON attendance.coach_id = coach.coach_id
                WHERE attendance.date BETWEEN %s AND %s AND skating_students.group_id = %s
                ORDER BY attendance.date, skating_students.fullname
            """, (start_date, end_date, grp_id))

            rows = cursor.fetchall()

            if not rows:
                result += "   Нет данных о посещаемости.\n\n"
                continue

            # Организация данных по студентам
            attendance_dict = {}
            for row in rows:
                student_name, date, attendance, coach_name = row
                if student_name not in attendance_dict:
                    attendance_dict[student_name] = []
                attendance_dict[student_name].append((date, attendance))

            for student, attendances in attendance_dict.items():
                result += f"👤 Студент: {student}\n"
                for att in attendances:
                    date_str = att[0].strftime('%d.%m.%Y')
                    status = attendance_status_str(att[1])
                    result += f"   📌 {date_str}: {status}\n"
                result += "\n"
            result += "\n"

    else:
        # Обработка для конкретной группы
        cursor.execute("""
            SELECT skating_students.fullname, attendance.date, attendance.attendance, coach.coach_name
            FROM attendance
            JOIN skating_students ON attendance.skate_student_id = skating_students.skate_student_id
            JOIN coach ON attendance.coach_id = coach.coach_id
            WHERE attendance.date BETWEEN %s AND %s AND skating_students.group_id = %s
            ORDER BY attendance.date, skating_students.fullname
        """, (start_date, end_date, group_id))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            bot.send_message(chat_id, "Нет данных о посещаемости за выбранный период для данной группы.")
            return

        # Получение информации о группе для заголовка
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category.category_name, coach.coach_name 
            FROM groups 
            JOIN category ON groups.id_category = category.id_category 
            JOIN coach ON groups.coach_id = coach.coach_id 
            WHERE group_id = %s
        """, (group_id,))
        group_info = cursor.fetchone()
        cursor.close()
        conn.close()
        if group_info:
            category_name, coach_name = group_info
        else:
            category_name, coach_name = "Неизвестно", "Неизвестно"

        result = f"📅 Посещаемость группы {group_id} ({category_name})\n👨‍🏫 Тренер: {coach_name}\n📆 Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n\n"

        # Организация данных по студентам
        attendance_dict = {}
        for row in rows:
            student_name, date, attendance, coach_name = row
            if student_name not in attendance_dict:
                attendance_dict[student_name] = []
            attendance_dict[student_name].append((date, attendance))

        for student, attendances in attendance_dict.items():
            result += f"👤 Студент: {student}\n"
            for att in attendances:
                date_str = att[0].strftime('%d.%m.%Y')
                status = attendance_status_str(att[1])
                result += f"   📌 {date_str}: {status}\n"
            result += "\n"

    bot.send_message(chat_id, result)
    user_data[chat_id]["step"] = "authenticated"

def attendance_status_str(value):
    if value == '0':
        return "❌ Пропуск"
    elif value == '1':
        return "⏰ Опоздал"
    elif value == '2':
        return "✅ Пришел"
    else:
        return "❓ Неизвестный статус"

@bot.message_handler(func=lambda message: message.text == 'Оценки Прыжков')
def handle_jump_scores(message):
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)

    if role == STUDENT_R:
        # Студенты могут только просматривать свои оценки
        skate_student_id = user_data[chat_id].get("skate_student_id")
        if not skate_student_id:
            bot.send_message(chat_id, "ID студента не найден.")
            return

        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            return
        cursor = conn.cursor()

        cursor.execute("""
            SELECT elements.name, jump_scores.date, jump_scores.technical_score, jump_scores.overall_score, jump_scores.specific_criteria
            FROM jump_scores
            JOIN elements ON jump_scores.element_id = elements.element_id
            WHERE jump_scores.skate_student_id = %s
            ORDER BY jump_scores.date DESC
        """, (skate_student_id,))

        scores = cursor.fetchall()
        cursor.close()
        conn.close()

        if not scores:
            bot.send_message(chat_id, "Нет оценок для отображения.")
            return

        result = "📊 Ваши оценки прыжков и вращений:\n\n"
        for score in scores:
            element_name, date, technical, overall, criteria = score
            # Предполагается, что 'criteria' хранится в формате JSON
            try:
                criteria_dict = json.loads(criteria)
                criteria_text = "\n".join([f"    - {k.capitalize()}: {v}" for k, v in criteria_dict.items()])
            except:
                criteria_text = "Нет данных."

            result += (f"📅 Дата: {date.strftime('%d.%m.%Y')}\n"
                       f"🔸 Элемент: {element_name}\n"
                       f"⭐ Техническая оценка: {technical}\n"
                       f"⭐ Общая оценка: {overall}\n"
                       f"🔍 Специфические критерии:\n{criteria_text}\n\n")

        bot.send_message(chat_id, result)

    elif role == COACH_R or role == ADMIN_R:
        # Тренеры и администраторы могут вводить и просматривать оценки
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Ввод оценки', 'Просмотр оценок')
        markup.add('Назад')
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

    else:
        bot.send_message(chat_id, "Ваша роль не определена.")


@bot.message_handler(func=lambda message: message.text == 'Ввод оценки')
def input_score(message):
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role")

    if role not in [COACH_R, ADMIN_R]:
        bot.send_message(chat_id, "У вас нет прав для ввода оценок.")
        logging.warning(f"Пользователь {chat_id} попытался ввести оценку без соответствующей роли.")
        return

    # Получение списка групп, доступных для ввода оценок
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        logging.error(f"Пользователь {chat_id} не смог подключиться к базе данных для ввода оценок.")
        return
    cursor = conn.cursor()

    try:
        if role == ADMIN_R:
            cursor.execute("SELECT group_id, id_category FROM groups")
        else:
            coach_id = user_data[chat_id].get("coach_id")
            cursor.execute("SELECT group_id, id_category FROM groups WHERE coach_id = %s", (coach_id,))
        groups = cursor.fetchall()
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка получения групп: {e}")
        logging.error(f"Ошибка получения групп для ввода оценок пользователем {chat_id}: {e}")
        cursor.close()
        conn.close()
        return

    cursor.close()
    conn.close()

    if not groups:
        bot.send_message(chat_id, "Нет доступных групп для ввода оценок.")
        logging.info(f"Нет групп для ввода оценок пользователем {chat_id}.")
        return

    # Создание клавиатуры для выбора группы
    markup = types.InlineKeyboardMarkup()
    for group in groups:
        group_id, category_id = group
        button_text = f"Группа {group_id}"
        callback_data = f"input_score_group_{group_id}"
        markup.add(types.InlineKeyboardButton(text=button_text, callback_data=callback_data))

    bot.send_message(chat_id, "Выберите группу для ввода оценок:", reply_markup=markup)
    logging.info(f"Пользователь {chat_id} выбрал ввод оценок и получил список групп.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("input_score_group_"))
def select_group_for_score(call):
    chat_id = call.message.chat.id
    group_id = int(call.data.split("_")[-1])

    logging.info(f"Пользователь {chat_id} выбрал группу {group_id} для ввода оценок.")

    user_data[chat_id]["selected_group_id_for_score"] = group_id
    user_data[chat_id]["step"] = "select_student_for_score"

    # Получение списка студентов в выбранной группе
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        logging.error(f"Пользователь {chat_id} не смог подключиться к базе данных для группы {group_id}.")
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT skate_student_id, fullname 
        FROM skating_students 
        WHERE group_id = %s
    """, (group_id,))
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    if not students:
        bot.send_message(chat_id, "В выбранной группе нет студентов.")
        logging.info(f"В группе {group_id} нет студентов для пользователя {chat_id}.")
        user_data[chat_id]["step"] = "authenticated"
        return

    # Создание клавиатуры для выбора студента
    markup = types.InlineKeyboardMarkup()
    for student in students:
        student_id, fullname = student
        callback_data = f"input_score_student_{student_id}"
        markup.add(types.InlineKeyboardButton(text=fullname, callback_data=callback_data))

    bot.send_message(chat_id, "Выберите студента для ввода оценки:", reply_markup=markup)
    bot.answer_callback_query(call.id, "Группа выбрана.")
    logging.info(f"Пользователь {chat_id} получил список студентов для группы {group_id}.")


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("input_score_student_") and user_data.get(call.message.chat.id, {}).get(
        "step") == "select_student_for_score")
def select_student_for_score(call):
    chat_id = call.message.chat.id
    student_id = int(call.data.split("_")[-1])

    logging.info(f"Пользователь {chat_id} выбрал студента {student_id} для ввода оценки.")

    user_data[chat_id]["selected_student_id_for_score"] = student_id
    user_data[chat_id]["step"] = "select_element_for_score"

    # Получение списка элементов для группы и тренера
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        logging.error(f"Пользователь {chat_id} не смог подключиться к базе данных для студента {student_id}.")
        return
    cursor = conn.cursor()

    role = user_data[chat_id].get("role")
    group_id = user_data[chat_id].get("selected_group_id_for_score")

    if role == ADMIN_R:
        cursor.execute("SELECT element_id, element_type, name FROM elements WHERE group_id = %s", (group_id,))
    else:
        coach_id = user_data[chat_id].get("coach_id")
        cursor.execute("""
            SELECT element_id, element_type, name 
            FROM elements 
            WHERE group_id = %s AND coach_id = %s
        """, (group_id, coach_id))

    elements = cursor.fetchall()
    cursor.close()
    conn.close()

    if not elements:
        bot.send_message(chat_id, "В выбранной группе нет элементов для оценки.")
        logging.info(f"В группе {group_id} нет элементов для пользователя {chat_id}.")
        user_data[chat_id]["step"] = "authenticated"
        return

    # Создание клавиатуры для выбора элемента
    markup = types.InlineKeyboardMarkup()
    for element in elements:
        element_id, element_type, name = element
        button_text = f"{element_type}: {name}"
        callback_data = f"input_score_element_{element_id}"
        markup.add(types.InlineKeyboardButton(text=button_text, callback_data=callback_data))

    bot.send_message(chat_id, "Выберите элемент для оценки:", reply_markup=markup)
    bot.answer_callback_query(call.id, "Студент выбран.")

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("input_score_element_") and user_data.get(call.message.chat.id, {}).get(
        "step") == "select_element_for_score")
def select_element_for_score(call):
    chat_id = call.message.chat.id
    element_id = int(call.data.split("_")[-1])
    user_data[chat_id]["selected_element_id_for_score"] = element_id
    user_data[chat_id]["step"] = "awaiting_technical_score"

    bot.send_message(chat_id, "Введите техническую оценку (1-10):")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_technical_score")
def receive_technical_score(message):
    chat_id = message.chat.id
    technical_score = message.text.strip()

    if not technical_score.isdigit() or not (1 <= int(technical_score) <= 10):
        bot.send_message(chat_id, "Неверная оценка. Введите число от 1 до 10.")
        return

    user_data[chat_id]["technical_score"] = int(technical_score)
    user_data[chat_id]["step"] = "awaiting_overall_score"
    bot.send_message(chat_id, "Введите общую оценку (1-10):")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_overall_score")
def receive_overall_score(message):
    chat_id = message.chat.id
    overall_score = message.text.strip()

    if not overall_score.isdigit() or not (1 <= int(overall_score) <= 10):
        bot.send_message(chat_id, "Неверная оценка. Введите число от 1 до 10.")
        return

    user_data[chat_id]["overall_score"] = int(overall_score)
    user_data[chat_id]["step"] = "awaiting_specific_criteria"
    bot.send_message(chat_id,
                     "Введите оценки по специфическим критериям в формате Критерий:Оценка, разделенные запятыми.\nНапример: Баланс:8, Контроль:7, Время в воздухе:9")

@bot.message_handler(
    func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_specific_criteria")
def receive_specific_criteria(message):
    chat_id = message.chat.id
    criteria_input = message.text.strip()

    try:
        criteria_pairs = [pair.strip().split(":") for pair in criteria_input.split(",")]
        criteria_dict = {pair[0].strip().lower(): int(pair[1].strip()) for pair in criteria_pairs if
                         len(pair) == 2 and pair[1].isdigit() and 1 <= int(pair[1].strip()) <= 10}

        if not criteria_dict:
            raise ValueError("Некорректный формат ввода критериев.")

    except Exception as e:
        bot.send_message(chat_id,
                         "Неверный формат ввода критериев. Пожалуйста, используйте формат Критерий:Оценка, разделенные запятыми.")
        return

    # Сохранение оценок в базе данных
    student_id = user_data[chat_id].get("selected_student_id_for_score")
    element_id = user_data[chat_id].get("selected_element_id_for_score")
    technical = user_data[chat_id].get("technical_score")
    overall = user_data[chat_id].get("overall_score")
    coach_id = user_data[chat_id].get("coach_id")
    date = datetime.now().date()

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO jump_scores (skate_student_id, element_id, coach_id, technical_score, overall_score, specific_criteria, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (student_id, element_id, coach_id, technical, overall, json.dumps(criteria_dict), date))
        conn.commit()
        element_name = get_element_name(element_id)  # Функция для получения имени элемента по ID
        notification_message = (
            f"🎓 *Новая оценка за элемент:* {element_name}\n\n"
            f"📅 Дата: {date.strftime('%d.%m.%Y')}\n"
            f"⭐ Техническая оценка: {technical}\n"
            f"⭐ Общая оценка: {overall}\n"
            f"🔍 Специфические критерии:\n"
        )

        for crit, score in criteria_dict.items():
            notification_message += f"    - {crit.capitalize()}: {score}\n"

        send_notification(student_id, notification_message)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при сохранении оценки: {e}")
        cursor.close()
        conn.close()
        user_data[chat_id]["step"] = "authenticated"
        return

    cursor.close()
    conn.close()

    bot.send_message(chat_id, "Оценка успешно сохранена.")
    user_data[chat_id]["step"] = "authenticated"

@bot.message_handler(
    func=lambda message: message.text == 'Просмотр оценок' and user_data.get(message.chat.id, {}).get("role") in [
        COACH_R, ADMIN_R])
def view_jump_scores(message):
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role")

    # Выбор группы
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()

    if role == ADMIN_R:
        cursor.execute(
            "SELECT group_id, category.category_name FROM groups JOIN category ON groups.id_category = category.id_category")
    else:
        coach_id = user_data[chat_id].get("coach_id")
        cursor.execute("""
            SELECT group_id, category.category_name 
            FROM groups 
            JOIN category ON groups.id_category = category.id_category 
            WHERE coach_id = %s
        """, (coach_id,))

    groups = cursor.fetchall()
    cursor.close()
    conn.close()

    if not groups:
        bot.send_message(chat_id, "Нет групп для выбора.")
        return

    markup = types.InlineKeyboardMarkup()
    for group in groups:
        group_id, category_name = group
        button_text = f"Группа {group_id} ({category_name})"
        markup.add(types.InlineKeyboardButton(text=button_text, callback_data=f"view_score_group_{group_id}"))

    bot.send_message(chat_id, "Выберите группу для просмотра оценок:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_score_group_"))
def select_group_for_view_score(call):
    chat_id = call.message.chat.id
    group_id = int(call.data.split("_")[-1])
    user_data[chat_id]["selected_group_id_for_view_score"] = group_id
    user_data[chat_id]["step"] = "select_student_for_view_score"

    # Получение списка студентов в группе
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT skate_student_id, fullname 
        FROM skating_students 
        WHERE group_id = %s
    """, (group_id,))
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    if not students:
        bot.send_message(chat_id, "В выбранной группе нет студентов.")
        user_data[chat_id]["step"] = "authenticated"
        return

    markup = types.InlineKeyboardMarkup()
    for student in students:
        student_id, fullname = student
        markup.add(types.InlineKeyboardButton(text=fullname, callback_data=f"view_score_student_{student_id}"))

    bot.send_message(chat_id, "Выберите студента для просмотра оценок:", reply_markup=markup)

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("view_score_student_") and user_data.get(call.message.chat.id, {}).get(
        "step") == "select_student_for_view_score")
def view_score_student_selected(call):
    chat_id = call.message.chat.id
    student_id = int(call.data.split("_")[-1])
    user_data[chat_id]["selected_student_id_for_view_score"] = student_id
    user_data[chat_id]["step"] = "viewing_scores"

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    cursor = conn.cursor()

    cursor.execute("""
        SELECT elements.name, jump_scores.date, jump_scores.technical_score, jump_scores.overall_score, jump_scores.specific_criteria
        FROM jump_scores
        JOIN elements ON jump_scores.element_id = elements.element_id
        WHERE jump_scores.skate_student_id = %s
        ORDER BY jump_scores.date DESC
    """, (student_id,))

    scores = cursor.fetchall()
    cursor.close()
    conn.close()

    if not scores:
        bot.send_message(chat_id, "Нет оценок для отображения.")
        return

    # Получение имени студента
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT fullname FROM skating_students WHERE skate_student_id = %s", (student_id,))
    student_name = cursor.fetchone()
    student_name = student_name[0] if student_name else "Неизвестно"
    cursor.close()
    conn.close()

    result = f"📊 Оценки прыжков и вращений для *{student_name}*:\n\n"
    for score in scores:
        element_name, date, technical, overall, criteria = score
        # Предполагается, что 'criteria' хранится в формате JSON
        try:
            criteria_dict = json.loads(criteria)
            criteria_text = "\n".join([f"    - {k.capitalize()}: {v}" for k, v in criteria_dict.items()])
        except:
            criteria_text = "Нет данных."

        result += (f"📅 Дата: {date.strftime('%d.%m.%Y')}\n"
                   f"🔸 Элемент: {element_name}\n"
                   f"⭐ Техническая оценка: {technical}\n"
                   f"⭐ Общая оценка: {overall}\n"
                   f"🔍 Специфические критерии:\n{criteria_text}\n\n")

    bot.send_message(chat_id, result, parse_mode="Markdown")
    user_data[chat_id]["step"] = "authenticated"

@bot.message_handler(func=lambda message: message.text == 'Назад')
def go_back(message):
    chat_id = message.chat.id
    user_data[chat_id]["step"] = "authenticated"
    role = user_data[chat_id].get("role")
    coach_name = user_data[chat_id].get("coach_name")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == STUDENT_R:
        markup.add('Посещаемость и "оценки"', 'Расписание', 'Рейтинг', 'Документы', 'Оценки Прыжков')
    elif role == ADMIN_R:
        markup.add('Просмотр всех групп', 'Просмотр посещаемости', 'Переносы',
                   'Отметить пропуск/посещаемость', 'Расписание', 'Документы', 'Оценки Прыжков')
    elif role == COACH_R:
        if coach_name == 'Ясмин':
            markup.add('Расписание', 'Переносы', 'Отметить пропуск/посещаемость', 'Оценки Прыжков')
        else:
            markup.add('Расписание', 'Отметить пропуск/посещаемость', 'Оценки Прыжков')
    else:
        bot.send_message(chat_id, "Пожалуйста, введите /start для начала.")
        return
    bot.send_message(chat_id, "Вы вернулись в главное меню.", reply_markup=markup)

bot.infinity_polling()
