import logging
import os
import json
import sqlite3
from datetime import datetime
import telebot
from telebot import types
from telebot.types import ReplyKeyboardRemove

# Локальная функция экранирования Markdown / MarkdownV2, т.к. в установленной версии telebot нет util.escape_markdown
def escape_markdown(text: str, version: int = 2) -> str:
    if text is None:
        return ''
    if version == 2:
        # Спецсимволы Telegram MarkdownV2
        specials = r'_ * [ ] ( ) ~ ` > # + - = | { } . !'.split()
        # Объединяем без пробелов для проверки каждого символа
        chars = '_*[]()~`>#+-=|{}.!'
    else:
        chars = '_*`['
    escaped = []
    for ch in text:
        if ch in chars:
            escaped.append('\\' + ch)
        else:
            escaped.append(ch)
    return ''.join(escaped)

# Безопасное форматирование дат из SQLite (могут приходить как строки)
def format_date_for_display(value) -> str:
    """Возвращает дату в формате ДД.ММ.ГГГГ из значения SQLite (str/date/datetime)."""
    try:
        # Если уже date/datetime
        if hasattr(value, 'strftime'):
            return value.strftime('%d.%m.%Y')
        # Если строка — пробуем ISO 'YYYY-MM-DD' или 'YYYY-MM-DD HH:MM:SS'
        if isinstance(value, str):
            try:
                # Полная дата-время
                from datetime import datetime
                if ' ' in value:
                    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    return dt.strftime('%d.%m.%Y')
                # Только дата
                dt = datetime.strptime(value, '%Y-%m-%d')
                return dt.strftime('%d.%m.%Y')
            except Exception:
                return value  # оставляем как есть
        # Любой другой тип
        return str(value)
    except Exception:
        return str(value)

def send_long_message(chat_id: int, text: str, parse_mode: str | None = None):
    """Отправка длинного текста несколькими сообщениями, чтобы не упасть по лимиту Telegram (~4096)."""
    try:
        if not text:
            return
        limit = 4000  # запас от 4096
        idx = 0
        n = len(text)
        while idx < n:
            end = min(idx + limit, n)
            if end < n:
                # стараемся резать по границе абзаца/строки
                cut = text.rfind('\n\n', idx, end)
                if cut == -1:
                    cut = text.rfind('\n', idx, end)
                if cut == -1:
                    cut = end
            else:
                cut = end
            chunk = text[idx:cut]
            bot.send_message(chat_id, chunk, parse_mode=parse_mode)
            idx = cut
    except Exception as e:
        # на всякий случай fallback одним сообщением без parse_mode
        try:
            bot.send_message(chat_id, text)
        except Exception as ex:
            logging.error(f"Не удалось отправить сообщение: {ex}")

def connect_to_db():
    try:
        # Создаем подключение к SQLite базе данных
        conn = sqlite3.connect('zhuldyz.db')
        conn.execute("PRAGMA foreign_keys = ON")  # Включаем проверку внешних ключей
        return conn
    except Exception as e:
        print("Ошибка подключения к базе данных:", e)
        return None

def initialize_database():
    """Создает базу данных и таблицы, если они не существуют"""
    conn = connect_to_db()
    if not conn:
        print("Не удалось создать базу данных")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Читаем SQL скрипт для создания таблиц
        with open('zhuldyz_sqlite.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        # Выполняем скрипт по частям
        cursor.executescript(sql_script)
        conn.commit()
        print("База данных успешно инициализирована")
        return True
        
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

token = '8154463207:AAFH6MRDWEcIjelNhaf80ZjOqEUka7SCDF8'
bot = telebot.TeleBot(token)

STUDENT_R = 'student'
COACH_R = 'coach'
ADMIN_R = 'admin'

if not os.path.exists('documents'):
    os.makedirs('documents')

# Инициализация базы данных при запуске
if not os.path.exists('zhuldyz.db'):
    print("База данных не найдена. Создаем новую базу данных...")
    initialize_database()
else:
    print("База данных найдена.")

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

def save_or_update_chat_id(skate_student_id, chat_id):
    conn = connect_to_db()
    if not conn:
        print("Ошибка подключения к базе данных.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE skate_student_id = ?", (skate_student_id,))
        result = cursor.fetchone()
        if result:
            cursor.execute("UPDATE stud_chat SET skate_chat_id = ? WHERE skate_student_id = ?", (chat_id, skate_student_id))
        else:
            cursor.execute("SELECT group_id FROM skating_students WHERE skate_student_id = ?", (skate_student_id,))
            group_id = cursor.fetchone()
            if group_id:
                group_id = group_id[0]
            else:
                group_id = None
            cursor.execute("INSERT INTO stud_chat (skate_student_id, group_id, skate_chat_id) VALUES (?, ?, ?)", (skate_student_id, group_id, chat_id))
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
        cursor.execute("SELECT skate_student_id FROM stud_login WHERE stud_login = ?", (login,))
        student = cursor.fetchone()

        # Проверяем тренера
        cursor.execute("SELECT coach_id FROM coach_login WHERE coach_login = ?", (login,))
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
        cursor.execute("SELECT stud_password FROM stud_login WHERE stud_login = ?", (login,))
        user = cursor.fetchone()
        if user and user[0] == password:
            # Студент авторизован
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            save_or_update_chat_id(user_data[chat_id]["skate_student_id"], chat_id)
            markup.add('Посещаемость и "оценки"', 'Расписание', 'Рейтинг', 'Документы')
            bot.send_message(chat_id, "Пароль верный! Добро пожаловать!", reply_markup=markup)
            user_data[chat_id]["step"] = "authenticated"
        else:
            bot.send_message(chat_id, "Неверный пароль. Попробуйте еще раз.")

    else:
        # Тренер или админ
        cursor.execute("SELECT coach_id, coach_password FROM coach_login WHERE coach_login = ?", (login,))
        coach_data = cursor.fetchone()
        if coach_data and coach_data[1] == password:
            coach_id = coach_data[0]
            user_data[chat_id]["coach_id"] = coach_id

            # Определяем роль тренера из таблицы roles
            cursor.execute("SELECT role FROM roles WHERE coach_id = ?", (coach_id,))
            r = cursor.fetchone()
            if r:
                user_role = r[0]
            else:
                user_role = COACH_R  # по умолчанию coach, если нет записи

            user_data[chat_id]["role"] = user_role

            # Получаем имя тренера
            cursor.execute("SELECT coach_name FROM coach WHERE coach_id = ?", (coach_id,))
            c_name = cursor.fetchone()
            c_name = c_name[0] if c_name else None
            user_data[chat_id]["coach_name"] = c_name

            # Формируем меню
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            if user_role == ADMIN_R:
                # Администратор
                markup.add('Управление студентами', 'Задания для тренеров')
                markup.add('Просмотр всех групп', 'Просмотр посещаемости', 'Переносы')
                markup.add('Отметить пропуск/посещаемость', 'Расписание', 'Документы')
                markup.add('Ежедневная оценка', 'Просмотр оценок тренеров')

            else:
                # Обычный тренер
                markup.add('Мои задания', 'Расписание', 'Отметить пропуск/посещаемость')
                markup.add('Просмотр оценок тренеров')
                # Если имя тренера Ясмин, даём доступ к переносам
                if c_name == 'Ясмин':
                    markup.add('Переносы')

            bot.send_message(chat_id, "Пароль верный! Добро пожаловать!", reply_markup=markup)
            user_data[chat_id]["step"] = "authenticated"
        else:
            bot.send_message(chat_id, "Неверный пароль. Попробуйте еще раз.")

    cursor.close()
    conn.close()

# Расписания групп по дням недели
stud_schedules = {
    1: {  # Старшая группа (Ясмин) - УТГ
        'ПН': ['16:30-17:30 СФП', '17:45-18:45 ЛЕД', '19:00-19:45 Хорео/ОФП'],
        'ВТ': ['09:15-10:00 СФП', '10:15-11:15 ЛЕД', '11:30-12:30 ОФП'],
        'СР': ['16:30-17:30 СФП', '17:45-18:45 ЛЕД', '19:00-19:45 Хорео/ОФП'],
        'ЧТ': ['09:15-10:00 СФП', '10:15-11:15 ЛЕД', '11:30-12:30 ОФП'],
        'ПТ': ['15:00-15:45 СФП', '16:00-17:45 ЛЕД', '18:00-19:00 Хорео'],
        'СБ': [],
        'ВС': ['15:30-16:30 СФП/хорео', '16:45-17:45 ЛЕД', '18:00-19:00 Хорео']
    },
    2: {  # Средняя группа
        'ПН': ['17:45-18:45 лед', '19:00-19:45 ОФП'],
        'ВТ': [],
        'СР': ['17:45-18:45 лед', '19:00-19:45 ОФП'],
        'ЧТ': [],
        'ПТ': ['17:15-18:15 лед', '18:30-19:15 ОФП'],
        'СБ': [],
        'ВС': ['15:45-16:00 ОФП', '16:45-17:45 лед']
    },
    3: {  # Младшая группа (Фатих)
        'ПН': ['17:45-18:45 лед', '19:00-19:45 ОФП'],
        'ВТ': [],
        'СР': ['17:45-18:45 лед', '19:00-19:45 ОФП'],
        'ЧТ': [],
        'ПТ': ['17:15-18:15 лед', '18:30-19:15 ОФП'],
        'СБ': [],
        'ВС': ['15:45-16:00 ОФП', '16:45-17:45 лед']
    },
    4: {  # Младшая группа (Салима)
        'ПН': ['17:45-18:45 лед', '19:00-19:45 ОФП'],
        'ВТ': [],
        'СР': ['17:45-18:45 лед', '19:00-19:45 ОФП'],
        'ЧТ': [],
        'ПТ': ['17:15-18:15 лед', '18:30-19:15 ОФП'],
        'СБ': [],
        'ВС': ['15:45-16:00 ОФП', '16:45-17:45 лед']
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
        cursor.execute("SELECT group_id FROM skating_students WHERE skate_student_id = ?", (skate_student_id,))
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
            cursor.execute("SELECT group_id FROM groups WHERE coach_id = ?", (coach_id,))
        groups = cursor.fetchall()
        cursor.close()
        conn.close()

        if not groups:
            bot.send_message(chat_id, "Нет прикрепленных групп.")
            return

        markup = types.InlineKeyboardMarkup()
        for g in groups:
            g_id = g[0]
            markup.add(types.InlineKeyboardButton(display_group(g_id), callback_data=f"coach_group_{g_id}"))
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
        WHERE attendance.skate_student_id = ?
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
    query = "SELECT name_file, path_file FROM docs WHERE skate_student_id = ?"
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
        query = "INSERT INTO docs (skate_student_id, name_file, path_file) VALUES(?, ?, ?)"
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
            group_name = groups_name[g_id - 1] if 0 < g_id <= len(groups_name) else display_group(g_id)
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
        cursor.execute("INSERT INTO skate_rescheldue (group_id, text_message) VALUES (?, ?)", (group_id, text_message))
        conn.commit()
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка записи в базу данных: {e}")
        cursor.close()
        conn.close()
        return

    try:
        cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE group_id = ?", (group_id,))
        students = cursor.fetchall()
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка получения списка студентов: {e}")
        cursor.close()
        conn.close()
        return

    cursor.execute("SELECT coach_name FROM coach WHERE coach_id = ?", (coach_id,))
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

def get_students_for_day(coach_id, date_obj, role):
    """Получает студентов, которые должны быть на занятии в указанный день"""
    day_of_week = date_obj.isoweekday()  # 1=Понедельник, 7=Воскресенье
    
    conn = connect_to_db()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        if role == ADMIN_R:
            # Админ видит всех студентов, у которых есть занятия в этот день
            cursor.execute("""
                SELECT DISTINCT s.skate_student_id, s.fullname, g.group_id, c.category_name
                FROM skating_students s
                JOIN groups g ON s.group_id = g.group_id
                JOIN category c ON g.id_category = c.id_category
                WHERE g.group_id IN (
                    SELECT DISTINCT group_id FROM groups
                    WHERE group_id IN (1, 2, 3, 4)
                )
                ORDER BY s.fullname
            """)
        else:
            # Тренер видит только своих студентов, у которых есть занятия в этот день
            cursor.execute("""
                SELECT DISTINCT s.skate_student_id, s.fullname, g.group_id, c.category_name
                FROM skating_students s
                JOIN groups g ON s.group_id = g.group_id
                JOIN category c ON g.id_category = c.id_category
                WHERE g.coach_id = ?
                ORDER BY s.fullname
            """, (coach_id,))
        
        all_students = cursor.fetchall()
        
        # Фильтруем студентов по расписанию
        filtered_students = []
        day_names = ['', 'ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
        current_day = day_names[day_of_week]
        
        for student_id, fullname, group_id, category_name in all_students:
            # Проверяем, есть ли у группы занятия в этот день
            group_schedule = stud_schedules.get(group_id, {})
            day_schedule = group_schedule.get(current_day, [])
            
            if day_schedule:  # Если есть занятия в этот день
                filtered_students.append((student_id, fullname, group_id, category_name))
        
        return filtered_students
        
    except Exception as e:
        print(f"Ошибка при получении студентов для дня: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

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
    role = user_data[chat_id]["role"]

    # Получаем студентов с учетом расписания на этот день
    students = get_students_for_day(coach_id, date_obj, role)

    if students:
        user_data[chat_id]["step"] = "date_selected_for_attendance"
        show_students_list_for_date_with_groups(chat_id, students, date_obj)
    else:
        day_names = ['', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        day_name = day_names[date_obj.isoweekday()]
        bot.send_message(chat_id, f"На {day_name} ({date_obj.strftime('%d.%m.%Y')}) нет студентов с запланированными занятиями.")
        user_data[chat_id]["step"] = "authenticated"

def show_students_list_for_date(chat_id, students):
    date_obj = user_data[chat_id]["attendance_date"]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for student_id, fio in students:
        markup.add(types.InlineKeyboardButton(text=fio, callback_data=f"attendance_student_{student_id}"))
    # Добавляем кнопку "Отметить всех"
    markup.add(types.InlineKeyboardButton(text="Отметить всех", callback_data="attendance_mark_all"))
    bot.send_message(chat_id, f"Дата: {date_obj.strftime('%d.%m.%Y')}\nВыберите студента для отметки посещаемости или отметьте всех:", reply_markup=markup)

def show_students_list_for_date_with_groups(chat_id, students, date_obj):
    """Отображает список студентов с указанием группы и расписания на день"""
    day_names = ['', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    day_name = day_names[date_obj.isoweekday()]
    day_short = ['', 'ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'][date_obj.isoweekday()]
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Группируем студентов по группам
    groups_dict = {}
    for student_id, fullname, group_id, category_name in students:
        if group_id not in groups_dict:
            groups_dict[group_id] = []
        groups_dict[group_id].append((student_id, fullname, category_name))
    
    message_text = f"📅 {day_name} ({date_obj.strftime('%d.%m.%Y')})\n"
    message_text += "👥 Студенты с занятиями:\n\n"
    
    for group_id, group_students in groups_dict.items():
        category_name = group_students[0][2]  # Получаем название категории
        group_schedule = stud_schedules.get(group_id, {}).get(day_short, [])

        message_text += f"🔸 {display_group(group_id)} ({category_name})\n"
        if group_schedule:
            schedule_text = ", ".join(group_schedule)
            message_text += f"   📋 Расписание: {schedule_text}\n"

        for student_id, fullname, _ in group_students:
            message_text += f"   👤 {fullname}\n"
            markup.add(types.InlineKeyboardButton(
                text=f"{fullname} ({display_group(group_id)})",
                callback_data=f"attendance_student_{student_id}"
            ))
        message_text += "\n"
    
    # Добавляем кнопки для массовых операций
    markup.add(types.InlineKeyboardButton(text="✅ Отметить всех присутствующими", callback_data="mark_all_2"))
    markup.add(types.InlineKeyboardButton(text="❌ Отметить всех отсутствующими", callback_data="mark_all_0"))
    markup.add(types.InlineKeyboardButton(text="⚙️ Выбрать значение для всех", callback_data="attendance_mark_all"))
    
    bot.send_message(chat_id, message_text, reply_markup=markup)

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
        "SELECT attendance FROM attendance WHERE skate_student_id = ? AND coach_id = ? AND date = ?",
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
            "INSERT INTO attendance (attendance, skate_student_id, coach_id, date) VALUES (?, ?, ?, ?)",
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
            "UPDATE attendance SET attendance = ? WHERE skate_student_id = ? AND coach_id = ? AND date = ?",
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
        cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE skate_student_id = ?", (student_id,))
        student_chat_id = cursor.fetchone()
        if student_chat_id:
            student_chat_id = student_chat_id[0]
            cursor.execute("SELECT coach_name FROM coach WHERE coach_id = ?", (coach_id,))
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
        "step") in ["awaiting_mark_all_value", "date_selected_for_attendance"])
def process_mark_all(call):
    chat_id = call.message.chat.id
    
    # Если вызван напрямую mark_all_0 или mark_all_2
    if user_data.get(chat_id, {}).get("step") == "date_selected_for_attendance":
        mark_value = call.data.split("_")[-1]  # Получаем значение: '0', '2'
    else:
        mark_value = call.data.split("_")[-1]  # Получаем значение: '0', '1', '2'
    
    date_obj = user_data[chat_id].get("attendance_date")
    coach_id = user_data[chat_id].get("coach_id")
    role = user_data[chat_id].get("role")

    # Получаем студентов с учетом расписания на этот день
    students = get_students_for_day(coach_id, date_obj, role)
    
    if not students:
        bot.send_message(chat_id, "Нет студентов для отметки посещаемости на этот день.")
        user_data[chat_id]["step"] = "date_selected_for_attendance"
        return

    # Обновляем посещаемость для всех студентов
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        user_data[chat_id]["step"] = "date_selected_for_attendance"
        return

    cursor = conn.cursor()
    try:
        marked_count = 0
        for student_id, fullname, group_id, category_name in students:
            # Проверяем, существует ли запись посещаемости
            cursor.execute(
                "SELECT attendance FROM attendance WHERE skate_student_id = ? AND coach_id = ? AND date = ?",
                (student_id, coach_id, date_obj)
            )
            existing_record = cursor.fetchone()
            if existing_record:
                cursor.execute(
                    "UPDATE attendance SET attendance = ? WHERE skate_student_id = ? AND coach_id = ? AND date = ?",
                    (mark_value, student_id, coach_id, date_obj)
                )
            else:
                cursor.execute(
                    "INSERT INTO attendance (attendance, skate_student_id, coach_id, date) VALUES (?, ?, ?, ?)",
                    (mark_value, student_id, coach_id, date_obj)
                )
            marked_count += 1
            
        conn.commit()
        
        status_emoji = {"0": "❌", "1": "⚠️", "2": "✅"}
        status_text = {"0": "Н-ка", "1": "Опоздал", "2": "Пришел"}
        
        bot.send_message(chat_id,
                         f"{status_emoji.get(mark_value, '')} Посещаемость отмечена для {marked_count} студентов как '{status_text.get(mark_value, mark_value)}'.")

        # Уведомляем студентов
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

        for student_id, fullname, group_id, category_name in students:
            # Получаем chat_id студента
            cursor.execute("SELECT skate_chat_id FROM stud_chat WHERE skate_student_id = ?", (student_id,))
            student_chat = cursor.fetchone()
            if student_chat:
                student_chat_id = student_chat[0]
                # Получаем имя тренера
                cursor.execute("SELECT coach_name FROM coach WHERE coach_id = ?", (coach_id,))
                coach_name = cursor.fetchone()
                coach_name = coach_name[0] if coach_name else "Тренер"

                # Отправляем сообщение студенту
                try:
                    bot.send_message(student_chat_id,
                                     f"📋 Ваша посещаемость обновлена:\n"
                                     f"📅 Дата: {date_obj.strftime('%d.%m.%Y')}\n"
                                     f"👨‍🏫 Тренер: {coach_name}\n"
                                     f"📊 Статус: {status_text.get(mark_value, mark_value)}\n"
                                     f"🕐 Время: {current_time}")
                except Exception as e:
                    print(f"Не удалось отправить уведомление студенту {student_id}: {e}")

    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при обновлении посещаемости: {e}")
        print(f"Ошибка при массовом обновлении посещаемости: {e}")
    finally:
        cursor.close()
        conn.close()
        user_data[chat_id]["step"] = "date_selected_for_attendance"

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
                WHERE groups.coach_id = ?
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
        result += f"{display_group(g_id)}, Категория {cat_id}, Тренер {c_id}\n"
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
        button_text = f"{display_group(group_id)} ({category_name}) - Тренер: {coach_name}"
        markup.add(types.InlineKeyboardButton(text=button_text, callback_data=f"admin_view_attendance_group_{group_id}"))

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
            # Исправлено: латинская m вместо кириллической м
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
            result += f"🔹 {display_group(grp_id)} ({category_name}) - Тренер: {coach_name}\n"

            cursor.execute("""
                SELECT skating_students.fullname, attendance.date, attendance.attendance, coach.coach_name
                FROM attendance
                JOIN skating_students ON attendance.skate_student_id = skating_students.skate_student_id
                JOIN coach ON attendance.coach_id = coach.coach_id
                WHERE attendance.date BETWEEN ? AND ? AND skating_students.group_id = ?
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
                    date_str = format_date_for_display(att[0])
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
            WHERE attendance.date BETWEEN ? AND ? AND skating_students.group_id = ?
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
            WHERE group_id = ?
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
                date_str = format_date_for_display(att[0])
                status = attendance_status_str(att[1])
                result += f"   📌 {date_str}: {status}\n"
            result += "\n"

    send_long_message(chat_id, result)
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

@bot.message_handler(func=lambda message: message.text == 'Назад')
def go_back(message):
    chat_id = message.chat.id
    user_data[chat_id]["step"] = "authenticated"
    role = user_data[chat_id].get("role")
    coach_name = user_data[chat_id].get("coach_name")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == STUDENT_R:
        markup.add('Посещаемость и "оценки"', 'Расписание', 'Рейтинг', 'Документы')
    elif role == ADMIN_R:
        markup.add('Управление студентами', 'Просмотр всех групп', 'Просмотр посещаемости', 'Переносы',
                   'Отметить пропуск/посещаемость', 'Расписание', 'Документы', 'Задания для тренеров')
        markup.add('Ежедневная оценка', 'Просмотр оценок тренеров')
    elif role == COACH_R:
        if coach_name == 'Ясмин':
            markup.add('Расписание', 'Переносы', 'Отметить пропуск/посещаемость', 'Мои задания')
            markup.add('Просмотр оценок тренеров')
        else:
            markup.add('Расписание', 'Отметить пропуск/посещаемость', 'Мои задания')
            markup.add('Просмотр оценок тренеров')
    else:
        bot.send_message(chat_id, "Пожалуйста, введите /start для начала.")
        return
    bot.send_message(chat_id, "Вы вернулись в главное меню.", reply_markup=markup)

# Функции для пагинации
def paginate_data(data, page=1, per_page=10):
    """Разбивает данные на страницы"""
    total = len(data)
    start = (page - 1) * per_page
    end = start + per_page
    
    has_prev = page > 1
    has_next = end < total
    total_pages = (total + per_page - 1) // per_page
    
    return {
        'items': data[start:end],
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': has_prev,
        'has_next': has_next
    }

def create_pagination_keyboard(prefix, current_page, total_pages, **extra_data):
    """Создает клавиатуру с пагинацией"""
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    buttons = []
    if current_page > 1:
        buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"{prefix}_page_{current_page-1}"))
    
    buttons.append(types.InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="page_info"))
    
    if current_page < total_pages:
        buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"{prefix}_page_{current_page+1}"))
    
    if buttons:
        markup.add(*buttons)
    
    return markup

# Функции для работы со студентами
def generate_login_candidate(fullname: str, existing: set) -> str:
    """Генерирует уникальный логин латиницей из ФИО.
    Схема: берем первые слова (до 3), транслитерируем, соединяем _ и добавляем число при конфликте.
    """
    if not fullname:
        return ""
    # Простая транслитерация (минимально необходимая)
    mapping = {
        'а':'a','б':'b','в':'v','г':'g','ғ':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','қ':'k','л':'l','м':'m','н':'n','ң':'n','о':'o','ө':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ұ':'u','ү':'u','ф':'f','х':'h','һ':'h','ц':'c','ч':'ch','ш':'sh','щ':'sh','ъ':'','ы':'y','і':'i','ь':'','э':'e','ю':'yu','я':'ya','А':'a','Б':'b','В':'v','Г':'g','Ғ':'g','Д':'d','Е':'e','Ё':'e','Ж':'zh','З':'z','И':'i','Й':'y','К':'k','Қ':'k','Л':'l','М':'m','Н':'n','Ң':'n','О':'o','Ө':'o','П':'p','Р':'r','С':'s','Т':'t','У':'u','Ұ':'u','Ү':'u','Ф':'f','Х':'h','Һ':'h','Ц':'c','Ч':'ch','Ш':'sh','Щ':'sh','Ъ':'','Ы':'y','І':'i','Ь':'','Э':'e','Ю':'yu','Я':'ya'
    }
    parts = fullname.split()
    core = parts[:3]
    def translit(word):
        return ''.join(mapping.get(ch, ch.lower()) for ch in word)[:12]
    base = '_'.join(translit(p) for p in core)
    base = ''.join(ch for ch in base if ch.isalnum() or ch=='_')
    if not base:
        base = 'stud'
    candidate = base
    suffix = 1
    while candidate in existing:
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate[:30]
def add_student_to_db(fullname, birthday, group_id, login, password):
    """Добавляет нового студента в базу данных"""
    conn = connect_to_db()
    if not conn:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = conn.cursor()
        
        # Проверяем, что логин не занят
        cursor.execute("SELECT COUNT(*) FROM stud_login WHERE stud_login = ?", (login,))
        if cursor.fetchone()[0] > 0:
            return False, "Логин уже занят"
        
        # Добавляем студента
        cursor.execute(
            "INSERT INTO skating_students (fullname, birthday, group_id) VALUES (?, ?, ?)",
            (fullname, birthday, group_id)
        )
        student_id = cursor.lastrowid
        
        # Добавляем логин
        cursor.execute(
            "INSERT INTO stud_login (skate_student_id, stud_login, stud_password) VALUES (?, ?, ?)",
            (student_id, login, password)
        )
        
        # Добавляем роль
        cursor.execute(
            "INSERT INTO roles (skate_student_id, coach_id, role) VALUES (?, NULL, 'student')",
            (student_id,)
        )
        
        conn.commit()
        return True, f"Студент {fullname} успешно добавлен"
        
    except Exception as e:
        return False, f"Ошибка при добавлении студента: {e}"
    finally:
        cursor.close()
        conn.close()

def remove_student_from_db(student_id):
    """Удаляет студента из базы данных"""
    conn = connect_to_db()
    if not conn:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = conn.cursor()
        
        # Удаляем связанные записи
        cursor.execute("DELETE FROM stud_chat WHERE skate_student_id = ?", (student_id,))
        cursor.execute("DELETE FROM stud_login WHERE skate_student_id = ?", (student_id,))
        cursor.execute("DELETE FROM attendance WHERE skate_student_id = ?", (student_id,))
        cursor.execute("DELETE FROM docs WHERE skate_student_id = ?", (student_id,))
        cursor.execute("DELETE FROM roles WHERE skate_student_id = ?", (student_id,))
        
        # Получаем имя студента для подтверждения
        cursor.execute("SELECT fullname FROM skating_students WHERE skate_student_id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            return False, "Студент не найден"
        
        # Удаляем самого студента
        cursor.execute("DELETE FROM skating_students WHERE skate_student_id = ?", (student_id,))
        
        conn.commit()
        return True, f"Студент {student[0]} успешно удален"
        
    except Exception as e:
        return False, f"Ошибка при удалении студента: {e}"
    finally:
        cursor.close()
        conn.close()

# Функции для работы с заданиями
def create_task(title, description, deadline, created_by, coach_ids=None):
    """Создает новое задание для тренеров"""
    conn = connect_to_db()
    if not conn:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = conn.cursor()
        
        # Создаем задание
        cursor.execute(
            "INSERT INTO coach_tasks (title, description, deadline, created_by) VALUES (?, ?, ?, ?)",
            (title, description, deadline, created_by)
        )
        task_id = cursor.lastrowid
        
        # Назначаем задание тренерам
        if coach_ids is None:
            # Назначаем всем тренерам (кроме админов)
            cursor.execute(
                "SELECT coach_id FROM roles WHERE role = 'coach'"
            )
            coach_ids = [row[0] for row in cursor.fetchall()]
        
        for coach_id in coach_ids:
            cursor.execute(
                "INSERT INTO task_assignments (task_id, coach_id) VALUES (?, ?)",
                (task_id, coach_id)
            )
        
        conn.commit()
        return True, f"Задание '{title}' создано и назначено тренерам"
        
    except Exception as e:
        return False, f"Ошибка при создании задания: {e}"
    finally:
        cursor.close()
        conn.close()

def send_task_notifications(task_id):
    """Отправляет уведомления тренерам о новом задании"""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Получаем информацию о задании
        cursor.execute(
            "SELECT title, description, deadline FROM coach_tasks WHERE task_id = ?",
            (task_id,)
        )
        task = cursor.fetchone()
        if not task:
            return
        
        title, description, deadline = task
        
        # Получаем тренеров, которым назначено задание
        cursor.execute("""
            SELECT ta.coach_id, c.coach_name 
            FROM task_assignments ta
            JOIN coach c ON ta.coach_id = c.coach_id
            WHERE ta.task_id = ?
        """, (task_id,))
        
        coaches = cursor.fetchall()
        
        # Отправляем уведомления
        message = f"📋 *Новое задание*\n\n*{title}*\n\n{description}\n\n⏰ Срок выполнения: {deadline}"
        
        for coach_id, coach_name in coaches:
            # Здесь можно добавить отправку уведомлений тренерам через Telegram
            # Пока просто логируем
            logging.info(f"Задание назначено тренеру {coach_name} (ID: {coach_id})")
        
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомлений о задании: {e}")
    finally:
        cursor.close()
        conn.close()

def check_task_deadlines():
    """Проверяет задания с дедлайном завтра и отправляет напоминания"""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Получаем задания с дедлайном завтра
        from datetime import date, timedelta
        tomorrow = date.today() + timedelta(days=1)
        
        cursor.execute("""
            SELECT ct.task_id, ct.title, ct.deadline, ta.coach_id, c.coach_name
            FROM coach_tasks ct
            JOIN task_assignments ta ON ct.task_id = ta.task_id
            JOIN coach c ON ta.coach_id = c.coach_id
            WHERE ct.deadline = ? AND ta.status = 0
        """, (tomorrow,))
        
        tasks = cursor.fetchall()
        
        for task_id, title, deadline, coach_id, coach_name in tasks:
            message = f"⚠️ *Напоминание о задании*\n\n*{title}*\n\nСрок выполнения: *завтра* ({deadline})\n\nНе забудьте выполнить задание!"
            # Здесь можно добавить отправку напоминаний
            logging.info(f"Напоминание о задании '{title}' для тренера {coach_name}")
        
    except Exception as e:
        logging.error(f"Ошибка при проверке дедлайнов заданий: {e}")
    finally:
        cursor.close()
        conn.close()

# ===== ОБРАБОТЧИКИ ДЛЯ СИСТЕМЫ ЗАДАНИЙ =====

@bot.message_handler(func=lambda message: message.text == 'Задания для тренеров')
def handle_coach_tasks_admin(message):
    """Администратор управляет заданиями тренеров"""
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)
    
    if role != ADMIN_R:
        bot.send_message(chat_id, "У вас нет прав для управления заданиями.")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Создать задание', 'Просмотр всех заданий')
    markup.add('Назад')
    bot.send_message(chat_id, "📋 Управление заданиями для тренеров:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Мои задания')
def handle_my_tasks_coach(message):
    """Тренер просматривает свои задания"""
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)
    
    if role != COACH_R:
        bot.send_message(chat_id, "У вас нет доступа к заданиям.")
        return
    
    coach_id = user_data[chat_id].get("coach_id")
    if not coach_id:
        bot.send_message(chat_id, "ID тренера не найден.")
        return
    
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ct.task_id, ct.title, ct.description, ct.deadline, ta.status, ta.completed_date
            FROM coach_tasks ct
            JOIN task_assignments ta ON ct.task_id = ta.task_id
            WHERE ta.coach_id = ?
            ORDER BY ct.deadline ASC
        """, (coach_id,))
        
        tasks = cursor.fetchall()
        
        if not tasks:
            bot.send_message(chat_id, "📋 У вас нет заданий.")
            return
        
        result = "📋 *Мои задания:*\n\n"
        for task_id, title, description, deadline, status, completed_date in tasks:
            status_emoji = "✅" if status == 1 else "⏳"
            status_text = "Выполнено" if status == 1 else "В процессе"
            
            result += f"{status_emoji} *{title}*\n"
            result += f"📝 {description}\n"
            result += f"📅 Срок: {deadline}\n"
            result += f"🔄 Статус: {status_text}\n"
            
            if completed_date:
                result += f"✅ Выполнено: {completed_date}\n"
            
            result += "\n"
        
        markup = types.InlineKeyboardMarkup()
        # Добавляем кнопки для отметки выполнения
        for task_id, title, description, deadline, status, completed_date in tasks:
            if status == 0:  # Не выполнено
                markup.add(types.InlineKeyboardButton(
                    f"✅ Отметить выполненным: {title[:20]}...", 
                    callback_data=f"complete_task_{task_id}"
                ))
        
        bot.send_message(chat_id, result, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при получении заданий: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.message_handler(func=lambda message: message.text == 'Просмотр всех заданий')
def handle_view_all_tasks_admin(message):
    """Администратор просматривает все задания"""
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)
    if role != ADMIN_R:
        bot.send_message(chat_id, "У вас нет прав.")
        return
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ct.task_id, ct.title, ct.description, ct.deadline, ct.created_date,
                   SUM(CASE WHEN ta.status=1 THEN 1 ELSE 0 END) as done_cnt,
                   COUNT(ta.assignment_id) as total_cnt
            FROM coach_tasks ct
            LEFT JOIN task_assignments ta ON ct.task_id = ta.task_id
            GROUP BY ct.task_id, ct.title, ct.description, ct.deadline, ct.created_date
            ORDER BY ct.created_date DESC
            LIMIT 50
        """)
        tasks = cursor.fetchall()
        if not tasks:
            bot.send_message(chat_id, "Заданий нет.")
            return
        text = "📋 *Все задания*\n\n"
        for task_id, title, description, deadline, created_date, done_cnt, total_cnt in tasks:
            safe_title = escape_markdown(title, version=2)
            safe_desc = escape_markdown(description or '', version=2)
            # Форматируем дату без дефисов, чтобы не нужно было экранировать '-'
            if deadline:
                try:
                    # deadline может быть строкой 'YYYY-MM-DD' -> конвертируем
                    dl_str = str(deadline)
                    if '-' in dl_str:
                        parts = dl_str.split('-')
                        if len(parts) == 3:
                            dl_fmt = f"{parts[2]}.{parts[1]}.{parts[0]}"
                        else:
                            dl_fmt = dl_str.replace('-', '.')
                    else:
                        dl_fmt = dl_str
                except Exception:
                    dl_fmt = str(deadline)
            else:
                dl_fmt = '—'
            safe_deadline = escape_markdown(dl_fmt, version=2)
            text += (f"*ID {task_id}: {safe_title}*\n"
                     f"📝 {safe_desc}\n"
                     f"📅 Дедлайн: {safe_deadline}\n"
                     f"👥 Выполнено: {done_cnt}/{total_cnt}\n\n")
        # Безопасная отправка
        try:
            bot.send_message(chat_id, text, parse_mode="MarkdownV2")
        except Exception as e:
            bot.send_message(chat_id, f"(plain) Ошибка форматирования MarkdownV2, показываю без форматирования:\n{text}\n\n{e}")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.message_handler(func=lambda message: message.text == 'Создать задание')
def create_task_start(message):
    """Начать создание нового задания"""
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)
    
    if role != ADMIN_R:
        bot.send_message(chat_id, "У вас нет прав для создания заданий.")
        return
    
    user_data[chat_id]["step"] = "awaiting_task_title"
    bot.send_message(chat_id, "📝 Введите название задания:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_task_title")
def receive_task_title(message):
    chat_id = message.chat.id
    title = message.text.strip()
    
    if len(title) < 3:
        bot.send_message(chat_id, "Название задания должно содержать минимум 3 символа. Попробуйте еще раз:")
        return
    
    user_data[chat_id]["task_title"] = title
    user_data[chat_id]["step"] = "awaiting_task_description"
    bot.send_message(chat_id, "📝 Введите описание задания:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_task_description")
def receive_task_description(message):
    chat_id = message.chat.id
    description = message.text.strip()
    
    if len(description) < 5:
        bot.send_message(chat_id, "Описание задания должно содержать минимум 5 символов. Попробуйте еще раз:")
        return
    
    user_data[chat_id]["task_description"] = description
    user_data[chat_id]["step"] = "awaiting_task_deadline"
    bot.send_message(chat_id, "📅 Введите срок выполнения в формате ДД.ММ.ГГГГ (например, 10.08.2025):")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_task_deadline")
def receive_task_deadline(message):
    chat_id = message.chat.id
    deadline_str = message.text.strip()
    
    try:
        from datetime import datetime
        deadline = datetime.strptime(deadline_str, "%d.%m.%Y").date()
        
        # Проверяем, что дата не в прошлом
        if deadline <= datetime.now().date():
            bot.send_message(chat_id, "Срок выполнения не может быть в прошлом. Введите корректную дату:")
            return
        
        user_data[chat_id]["task_deadline"] = deadline
        
        # Сохраняем задание в базе данных
        title = user_data[chat_id]["task_title"]
        description = user_data[chat_id]["task_description"]
        created_by = user_data[chat_id]["coach_id"]
        
        success, message_text = create_task(title, description, deadline, created_by)
        
        if success:
            bot.send_message(chat_id, f"✅ {message_text}")
            
            # Отправляем уведомления тренерам
            send_task_notifications_to_coaches(title, description, deadline)
            
        else:
            bot.send_message(chat_id, f"❌ {message_text}")
        
        # Возвращаемся в главное меню
        user_data[chat_id]["step"] = "authenticated"
        
    except ValueError:
        bot.send_message(chat_id, "Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например, 10.08.2025):")

@bot.callback_query_handler(func=lambda call: call.data.startswith("complete_task_"))
def complete_task(call):
    """Отметить задание как выполненное"""
    chat_id = call.message.chat.id
    task_id = int(call.data.split("_")[-1])
    coach_id = user_data[chat_id].get("coach_id")
    
    if not coach_id:
        bot.answer_callback_query(call.id, "Ошибка: ID тренера не найден")
        return
    
    conn = connect_to_db()
    if not conn:
        bot.answer_callback_query(call.id, "Ошибка подключения к базе данных")
        return
    
    try:
        cursor = conn.cursor()
        from datetime import datetime
        
        cursor.execute("""
            UPDATE task_assignments 
            SET status = 1, completed_date = ? 
            WHERE task_id = ? AND coach_id = ?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id, coach_id))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            bot.answer_callback_query(call.id, "✅ Задание отмечено как выполненное!")
            # Обновляем сообщение
            handle_my_tasks_coach(call.message)
        else:
            bot.answer_callback_query(call.id, "Ошибка при обновлении задания")
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        conn.close()

def send_task_notifications_to_coaches(title, description, deadline):
    """Отправляет уведомления всем тренерам о новом задании"""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        # Для отсутствия таблицы чатов тренеров пока просто логируем
        cursor.execute("""
            SELECT c.coach_id, c.coach_name
            FROM coach c
            JOIN roles r ON c.coach_id = r.coach_id
            WHERE r.role = 'coach'
        """)
        coaches = cursor.fetchall()

        # Экранируем markdown в пользовательских вводах
        safe_title = escape_markdown(title, version=2)
        safe_desc = escape_markdown(description, version=2)
        message = (
            f"📋 *Новое задание!*\n\n*{safe_title}*\n\n{safe_desc}\n\n"
            f"📅 Срок выполнения: {deadline.strftime('%d.%m.%Y')}\n\n"
            "Просмотрите задание в разделе 'Мои задания'"
        )
        for coach_id, coach_name in coaches:
            logging.info(f"(Notification placeholder) Отправка задания тренеру {coach_name} (ID {coach_id})")
        
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомлений о задании: {e}")
    finally:
        cursor.close()
        conn.close()

# ===== СИСТЕМА ЕЖЕДНЕВНЫХ ОЦЕНОК =====

@bot.message_handler(func=lambda message: message.text == 'Ежедневная оценка')
def handle_daily_evaluation(message):
    """Обработчик для создания ежедневной оценки (только для админов)"""
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)
    
    if role != ADMIN_R:
        bot.send_message(chat_id, "У вас нет прав для создания ежедневных оценок.")
        return
    
    # Получаем список тренеров
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.coach_id, c.coach_name 
            FROM coach c
            JOIN roles r ON c.coach_id = r.coach_id
            WHERE r.role = 'coach'
        """)
        coaches = cursor.fetchall()
        
        if not coaches:
            bot.send_message(chat_id, "Нет тренеров для оценки.")
            return
        
        markup = types.InlineKeyboardMarkup()
        for coach_id, coach_name in coaches:
            markup.add(types.InlineKeyboardButton(
                coach_name, 
                callback_data=f"eval_coach_{coach_id}"
            ))
        
        bot.send_message(chat_id, "📊 Выберите тренера для ежедневной оценки:", reply_markup=markup)
        
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("eval_coach_"))
def select_coach_for_evaluation(call):
    """Выбор тренера для оценки"""
    chat_id = call.message.chat.id
    coach_id = int(call.data.split("_")[-1])
    
    user_data[chat_id]["eval_coach_id"] = coach_id
    
    # Получаем группы тренера
    conn = connect_to_db()
    if not conn:
        bot.answer_callback_query(call.id, "Ошибка подключения к БД")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.group_id, c.category_name
            FROM groups g
            JOIN category c ON g.id_category = c.id_category
            WHERE g.coach_id = ?
        """, (coach_id,))
        groups = cursor.fetchall()
        
        if not groups:
            bot.answer_callback_query(call.id, "У тренера нет групп")
            return
        
        markup = types.InlineKeyboardMarkup()
        for group_id, category_name in groups:
            markup.add(types.InlineKeyboardButton(
                f"{display_group(group_id)} ({category_name})", 
                callback_data=f"eval_group_{group_id}"
            ))
        
        bot.edit_message_text(
            "📊 Выберите группу для оценки:",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=markup
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("eval_group_"))
def select_group_for_evaluation(call):
    """Выбор группы для оценки"""
    chat_id = call.message.chat.id
    group_id = int(call.data.split("_")[-1])
    
    user_data[chat_id]["eval_group_id"] = group_id
    user_data[chat_id]["step"] = "awaiting_performance_score"
    
    bot.edit_message_text(
        "📊 Введите оценку работы тренера (1-10):",
        chat_id=chat_id,
        message_id=call.message.message_id
    )

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_performance_score")
def receive_performance_score(message):
    """Получение оценки работы тренера"""
    chat_id = message.chat.id
    score_text = message.text.strip()
    
    try:
        score = int(score_text)
        if not (1 <= score <= 10):
            raise ValueError("Оценка должна быть от 1 до 10")
        
        user_data[chat_id]["performance_score"] = score
        user_data[chat_id]["step"] = "awaiting_group_progress"
        bot.send_message(chat_id, "📈 Введите оценку прогресса группы (1-10):")
        
    except ValueError:
        bot.send_message(chat_id, "❌ Неверная оценка. Введите число от 1 до 10:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_group_progress")
def receive_group_progress(message):
    """Получение оценки прогресса группы"""
    chat_id = message.chat.id
    score_text = message.text.strip()
    
    try:
        score = int(score_text)
        if not (1 <= score <= 10):
            raise ValueError("Оценка должна быть от 1 до 10")
        
        user_data[chat_id]["group_progress"] = score
        user_data[chat_id]["step"] = "awaiting_evaluation_notes"
        bot.send_message(chat_id, "📝 Введите дополнительные заметки (или напишите 'нет'):")
        
    except ValueError:
        bot.send_message(chat_id, "❌ Неверная оценка. Введите число от 1 до 10:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_evaluation_notes")
def receive_evaluation_notes(message):
    """Получение заметок и сохранение оценки"""
    chat_id = message.chat.id
    notes = message.text.strip()
    
    if notes.lower() == 'нет':
        notes = None
    
    # Сохраняем оценку в базе данных
    coach_id = user_data[chat_id]["eval_coach_id"]
    group_id = user_data[chat_id]["eval_group_id"]
    performance = user_data[chat_id]["performance_score"]
    progress = user_data[chat_id]["group_progress"]
    
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    
    try:
        cursor = conn.cursor()
        today = datetime.now().date()
        
        # Проверяем, есть ли уже оценка на сегодня
        cursor.execute("""
            SELECT evaluation_id FROM daily_evaluations 
            WHERE coach_id = ? AND group_id = ? AND evaluation_date = ?
        """, (coach_id, group_id, today))
        
        existing = cursor.fetchone()
        
        if existing:
            # Обновляем существующую оценку
            cursor.execute("""
                UPDATE daily_evaluations 
                SET performance_score = ?, group_progress = ?, notes = ?
                WHERE coach_id = ? AND group_id = ? AND evaluation_date = ?
            """, (performance, progress, notes, coach_id, group_id, today))
            message_text = "✅ Ежедневная оценка обновлена!"
        else:
            # Создаем новую оценку
            cursor.execute("""
                INSERT INTO daily_evaluations 
                (coach_id, group_id, evaluation_date, performance_score, group_progress, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (coach_id, group_id, today, performance, progress, notes))
            message_text = "✅ Ежедневная оценка сохранена!"

        conn.commit()
        bot.send_message(chat_id, message_text)
        
        # Получаем имя тренера для отчета
        cursor.execute("SELECT coach_name FROM coach WHERE coach_id = ?", (coach_id,))
        coach_name = cursor.fetchone()[0]
        
        # Отправляем краткий отчет
        # Экранируем markdown спецсимволы
        safe_notes = escape_markdown(notes, version=2) if notes else None
        safe_coach = escape_markdown(coach_name, version=2)
        report = "📊 *Оценка сохранена*\n\n"
        report += f"👨‍🏫 Тренер: {safe_coach}\n"
        report += f"👥 Группа: {group_id}\n"
        report += f"📅 Дата: {today.strftime('%d.%m.%Y')}\n\n"
        report += f"⭐ Работа тренера: {performance}/10\n"
        report += f"📈 Прогресс группы: {progress}/10\n"
        if safe_notes:
            report += f"📝 Заметки: {safe_notes}\n"
        bot.send_message(chat_id, report, parse_mode="MarkdownV2")
        
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при сохранении оценки: {e}")
    finally:
        cursor.close()
        conn.close()
        user_data[chat_id]["step"] = "authenticated"

@bot.message_handler(func=lambda message: message.text == 'Просмотр оценок тренеров')
def view_coach_evaluations(message):
    """Просмотр ежедневных оценок тренеров"""
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get("role", None)
    
    if role not in [ADMIN_R, COACH_R]:
        bot.send_message(chat_id, "У вас нет доступа к оценкам.")
        return
    
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    
    try:
        cursor = conn.cursor()
        
        if role == ADMIN_R:
            # Админ видит все оценки
            cursor.execute("""
                SELECT c.coach_name, de.group_id, de.evaluation_date, 
                       de.performance_score, de.group_progress, de.notes
                FROM daily_evaluations de
                JOIN coach c ON de.coach_id = c.coach_id
                ORDER BY de.evaluation_date DESC, c.coach_name
                LIMIT 20
            """)
        else:
            # Тренер видит только свои оценки
            coach_id = user_data[chat_id].get("coach_id")
            cursor.execute("""
                SELECT c.coach_name, de.group_id, de.evaluation_date, 
                       de.performance_score, de.group_progress, de.notes
                FROM daily_evaluations de
                JOIN coach c ON de.coach_id = c.coach_id
                WHERE de.coach_id = ?
                ORDER BY de.evaluation_date DESC
                LIMIT 10
            """, (coach_id,))
        
        evaluations = cursor.fetchall()
        
        if not evaluations:
            bot.send_message(chat_id, "📊 Оценок пока нет.")
            return
        
        result = "📊 *Ежедневные оценки тренеров:*\n\n"
        
        for coach_name, group_id, eval_date, performance, progress, notes in evaluations:
            avg_score = round((performance + progress) / 2, 1)
            result += f"👨‍🏫 *{coach_name}* ({display_group(group_id)})\n"
            result += f"📅 {eval_date}\n"
            result += f"⭐ Работа: {performance}/10\n"
            result += f"📈 Прогресс: {progress}/10\n"
            result += f"🎯 Средняя оценка: {avg_score}/10\n"
            if notes:
                result += f"📝 {notes}\n"
            result += "\n"
        
        bot.send_message(chat_id, result, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при получении оценок: {e}")
    finally:
        cursor.close()
        conn.close()

# ===== ОБРАБОТЧИКИ ДЛЯ УПРАВЛЕНИЯ СТУДЕНТАМИ =====

# Отображаемое имя группы / тренеров
GROUP_DISPLAY = {
    1: 'Ясмин',
    2: 'Майя/Алтынарай',
    3: 'Фатих',
    4: 'Салима',
    5: 'Ясмин-Фатих',
    6: 'Майя'
}

def display_group(group_id: int) -> str:
    return f"Группа: {GROUP_DISPLAY.get(group_id, str(group_id))}"

# ===== RESET STUDENTS (ADMIN) =====
@bot.message_handler(commands=['reset_students'])
def reset_students_cmd(message):
    chat_id = message.chat.id
    role = user_data.get(chat_id, {}).get('role')
    if role != ADMIN_R:
        bot.reply_to(message, 'Нет прав.')
        return
    # Подтверждение
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✅ Подтвердить сброс', callback_data='reset_students_confirm'),
               types.InlineKeyboardButton('❌ Отмена', callback_data='reset_students_cancel'))
    bot.reply_to(message, 'Стереть всех студентов и загрузить новый список? Это необратимо.', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['reset_students_confirm','reset_students_cancel'])
def reset_students_confirm_cb(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    if call.data == 'reset_students_cancel':
        bot.send_message(chat_id, 'Отменено.')
        return
    role = user_data.get(chat_id, {}).get('role')
    if role != ADMIN_R:
        bot.send_message(chat_id, 'Нет прав.')
        return
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, 'Ошибка подключения к базе данных.')
        return
    try:
        cur = conn.cursor()
        # Очистка студентов и логинов
        cur.execute('DELETE FROM stud_login')
        cur.execute('DELETE FROM skating_students')
        conn.commit()
        # Новый список (fullname, birthday(ДД.ММ.ГГГГ или ГГГГ), тренер-метка -> group_id)
        raw_students = [
            ('Сенiм Малик','09.11.2014','Ясмин'),
            ('Мариям Амиртай','16.04.2017','Ясмин'),
            ('Маржан Муратканова','17.07.2017','Ясмин'),
            ('Марат Аяру','31.03.2017','Майя/Алтынарай'),
            ('Марат Даяна','27.11.2018','Майя/Алтынарай'),
            ('Марат Мерей','21.03.2020','Майя/Алтынарай'),
            ('Амина Бектурганова','13.01.2018','Ясмин'),
            ('Амира Мейрамова','21.05.2017','Ясмин'),
            ('Асылым Еншібай','28.06.2017','Ясмин'),
            ('Адема Мурзанова','25.09.2017','Ясмин'),
            ('Салтанат Мурзанова','03.07.2019','Майя/Алтынарай'),
            ('Амина Мурзанова','14.04.2021','Майя/Алтынарай'),
            ('Зейнеп Азра Атай','14.12.2018','Ясмин'),
            ('Балауса Байтенова','13.11.2019','Майя/Алтынарай'),
            ('Касым Айтпек','19.01.2020','Майя/Алтынарай'),
            ('Марьям Айтпек','03.08.2016','Ясмин'),
            ('Сарыгюл Кайла','20.04.2018','Майя/Алтынарай'),
            ('Аяла Беембетова','27.07.2017','Ясмин'),
            ('Аиша Кабдушева','21.02.2020','Майя/Алтынарай'),
            ('Селин Науруз','10.01.2021','Майя/Алтынарай'),
            ('Ханшайын Ахматолла','25.12.2017','Майя/Алтынарай'),
            ('Амалия Бисатова','30.01.2017','Майя/Алтынарай'),
            ('Инкар Иралимова','09.09.2017','Майя/Алтынарай'),
            ('Сафия Ербулат','06.11.2018','Майя/Алтынарай'),
            ('Дарина Мурзабаева','23.02.2019','Майя/Алтынарай'),
            ('Жанайши Каржас','12.05.2017','Майя/Алтынарай'),
            ('Наркес Сейлбек','14.10.2017','Майя/Алтынарай'),
            ('Айару Есенова','29.03.2015','Ясмин'),
            ('Райлана Есенова','09.09.2017','Ясмин'),
            ('Айлана Адамзатова','04.06.2017','Майя/Алтынарай'),
            ('Зере Азаматкызы','08.05.2018','Майя/Алтынарай'),
            ('Радмила Dyyak','29.10.2019','Майя/Алтынарай'),
            ('Мажит Айдана','14.03.2019','Майя/Алтынарай'),
            ('Ербол Гулим','24.07.2019','Майя/Алтынарай'),
            ('Кайратбек Айшолпан','05.11.2020','Майя/Алтынарай'),
            ('Серik Аиша','18.06.2018','Майя'),
            ('Анарбек Томирис','01.07.2021','Салима'),
            ('Мукашева Зара','04.11.2017','Майя/Алтынарай'),
            ('Мурат Асыл','01.11.2019','Салима'),
            ('Арна','01.01.2021','Майя/Алтынарай'),
            ('Сейдахмет Аяулым','17.01.2020','Салима'),
            ('Шахматова София','31.08.2019','Салима'),
            ('Мұратбек Алина','26.01.2019','Салима'),
            ('Айша Бейсенбек','01.11.2012','Ясмин'),
            ('Даяна Нурлан','24.11.2016','Майя'),
            ('Сара Шамсутдинова','20.07.2016','Майя')
        ]
        label_to_group = {v:k for k,v in GROUP_DISPLAY.items()}
        # Сбор существующих логинов
        cur.execute('SELECT stud_login FROM stud_login')
        existing = {row[0] for row in cur.fetchall()}
        added = 0
        for fullname, date_raw, label in raw_students:
            group_id = label_to_group.get(label)
            if not group_id:
                continue
            # нормализуем дату DD.MM.YYYY
            if len(date_raw) == 4 and date_raw.isdigit():
                date_iso = f"{date_raw}-01-01"
            else:
                try:
                    d, m, y = date_raw.split('.')
                    date_iso = f"{y}-{m}-{d}"
                except Exception:
                    date_iso = None
            # вставка студента
            cur.execute('INSERT INTO skating_students(fullname,birthday,group_id) VALUES(?,?,?)', (fullname, date_iso, group_id))
            sid = cur.lastrowid
            # генерируем логин/пароль
            login = generate_login_candidate(fullname, existing)
            existing.add(login)
            password = login.split('_')[0]  # простой пароль
            cur.execute('INSERT INTO stud_login(skate_student_id, stud_login, stud_password) VALUES (?,?,?)', (sid, login, password))
            added += 1
        conn.commit()
        bot.send_message(chat_id, f'Сброс завершён. Загружено студентов: {added}.')
    except Exception as e:
        bot.send_message(chat_id, f'Ошибка сброса: {e}')
    finally:
        conn.close()

@bot.message_handler(func=lambda message: message.text == 'Управление студентами' and user_data.get(message.chat.id, {}).get("role") == ADMIN_R)
def manage_students(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👥 Просмотр всех студентов", callback_data="view_all_students"))
    markup.add(types.InlineKeyboardButton("➕ Добавить студента", callback_data="add_student"))
    markup.add(types.InlineKeyboardButton("✏️ Редактировать студента", callback_data="edit_student"))
    markup.add(types.InlineKeyboardButton("🗑️ Удалить студента", callback_data="delete_student"))
    markup.add(types.InlineKeyboardButton("🔄 Перевести студента", callback_data="transfer_student"))
    bot.send_message(chat_id, "Выберите действие для управления студентами:", reply_markup=markup)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ВЫБОРА СТУДЕНТОВ (С ФИЛЬТРОМ ПО ГРУППЕ) =====
def fetch_all_students(group_filter: str | int | None = None):
    conn = connect_to_db()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        if group_filter and str(group_filter).isdigit():
            cur.execute("SELECT skate_student_id, fullname FROM skating_students WHERE group_id = ? ORDER BY fullname", (int(group_filter),))
        else:
            cur.execute("SELECT skate_student_id, fullname FROM skating_students ORDER BY fullname")
        rows = cur.fetchall()
        return rows
    except Exception:
        return []
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

def build_student_select_markup(action: str, page: int, group_filter: str = 'all', per_page: int = 10):
    students = fetch_all_students(None if group_filter == 'all' else group_filter)
    total = len(students)
    if total == 0:
        return types.InlineKeyboardMarkup(), 0, 0, []
    total_pages = (total + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    subset = students[start:end]
    markup = types.InlineKeyboardMarkup()
    for sid, fio in subset:
        if action == 'edit':
            cb = f"edit_student_pick_{sid}"
        elif action == 'delete':
            cb = f"delete_student_pick_{sid}"
        elif action == 'transfer':
            cb = f"transfer_student_pick_{sid}"
        else:
            continue
        short = fio if len(fio) <= 28 else fio[:25] + '…'
        markup.add(types.InlineKeyboardButton(short, callback_data=cb))
    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"{action}_student_page_{group_filter}_{page-1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"{action}_student_page_{group_filter}_{page+1}"))
    if nav_buttons:
        markup.add(*nav_buttons)
    # Кнопка смены фильтра
    markup.add(types.InlineKeyboardButton("🔍 Фильтр по группе", callback_data=f"{action}_student_filter"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_manage_students"))
    return markup, page, total_pages, subset

def show_student_picker(chat_id, action: str, page: int = 1, group_filter: str = 'all'):
    user_data.setdefault(chat_id, {})
    user_data[chat_id][f"{action}_student_group_filter"] = group_filter
    markup, page, total_pages, subset = build_student_select_markup(action, page, group_filter)
    if not subset:
        bot.send_message(chat_id, "Список студентов пуст.")
        return
    if action == 'edit':
        title = "Выберите студента для редактирования:"
    elif action == 'delete':
        title = "Выберите студента для удаления:"
    elif action == 'transfer':
        title = "Выберите студента для перевода:"
    else:
        title = "Студенты:"
    gf_text = "Все группы" if group_filter == 'all' else display_group(int(group_filter))
    bot.send_message(chat_id, f"{title}\nФильтр: {gf_text}\nСтраница {page}/{total_pages}")
    bot.send_message(chat_id, "Нажмите на имя студента:", reply_markup=markup)

def show_group_filter(chat_id, action: str):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Все", callback_data=f"{action}_student_filter_set_all"),
        types.InlineKeyboardButton("1", callback_data=f"{action}_student_filter_set_1"),
        types.InlineKeyboardButton("2", callback_data=f"{action}_student_filter_set_2"),
        types.InlineKeyboardButton("3", callback_data=f"{action}_student_filter_set_3"),
        types.InlineKeyboardButton("4", callback_data=f"{action}_student_filter_set_4")
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data=f"{action}_student_filter_back"))
    bot.send_message(chat_id, "Выберите группу для фильтра:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "view_all_students")
def view_all_students(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.skate_student_id, s.fullname, s.birthday, g.group_id, c.category_name
            FROM skating_students s
            JOIN groups g ON s.group_id = g.group_id
            JOIN category c ON g.id_category = c.id_category
            ORDER BY s.fullname
        """)
        students = cursor.fetchall()
        
        if not students:
            bot.send_message(chat_id, "Студенты не найдены.")
            return
        
        result = "👥 *Все студенты:*\n\n"
        for student in students:
            student_id, fullname, birthday, group_id, category_name = student
            result += f"🆔 ID: {student_id}\n"
            result += f"👤 ФИО: {fullname}\n"
            result += f"🎂 Дата рождения: {birthday}\n"
            result += f"👥 Группа: {group_id} ({category_name})\n\n"
        
        # Разбиваем длинное сообщение на части
        if len(result) > 4096:
            for i in range(0, len(result), 4096):
                bot.send_message(chat_id, result[i:i+4096], parse_mode="Markdown")
        else:
            bot.send_message(chat_id, result, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при получении студентов: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "add_student")
def cb_add_student(call):
    chat_id = call.message.chat.id
    try:
        bot.answer_callback_query(call.id)
        role = user_data.get(chat_id, {}).get("role")
        print(f"[DEBUG] add_student pressed chat={chat_id} role={role}")
        if role != ADMIN_R:
            bot.send_message(chat_id, "Нет прав.")
            return
        user_data.setdefault(chat_id, {})
        user_data[chat_id]["step"] = "adding_student_fullname"
        bot.send_message(chat_id, "Введите ФИО студента (например: Иванов Иван):")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка обработчика add_student: {e}")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "adding_student_fullname")
def add_student_fullname_step(message):
    chat_id = message.chat.id
    user_data[chat_id]["new_student"] = {"fullname": message.text.strip()}
    user_data[chat_id]["step"] = "adding_student_birthday"
    bot.send_message(chat_id, "Введите дату рождения в формате ДД.ММ.ГГГГ:")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "adding_student_birthday")
def add_student_birthday_step(message):
    chat_id = message.chat.id
    date_txt = message.text.strip()
    try:
        dt = datetime.strptime(date_txt, "%d.%m.%Y").date()
    except ValueError:
        bot.send_message(chat_id, "Неверный формат. Введите дату в формате ДД.ММ.ГГГГ:")
        return
    user_data[chat_id]["new_student"]["birthday"] = dt.isoformat()
    user_data[chat_id]["step"] = "adding_student_group"
    bot.send_message(chat_id, "Введите ID группы (1-4):")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "adding_student_group")
def add_student_group_step(message):
    chat_id = message.chat.id
    grp = message.text.strip()
    if grp not in ['1','2','3','4']:
        bot.send_message(chat_id, "Только 1-4. Введите снова:")
        return
    user_data[chat_id]["new_student"]["group_id"] = int(grp)
    # Генерируем логин автоматически
    try:
        conn = connect_to_db()
        existing = set()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT stud_login FROM stud_login")
            existing = {r[0] for r in cur.fetchall()}
            cur.close(); conn.close()
        fullname = user_data[chat_id]["new_student"].get("fullname", "")
        candidate = generate_login_candidate(fullname, existing)
        user_data[chat_id]["new_student"]["login_candidate"] = candidate
    except Exception:
        candidate = ""
    user_data[chat_id]["step"] = "adding_student_login"
    if candidate:
        bot.send_message(chat_id, f"Сгенерирован логин: {candidate}\nОтправьте '+' чтобы принять или введите другой логин:")
    else:
        bot.send_message(chat_id, "Введите логин студента (латиницей):")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "adding_student_login")
def add_student_login_step(message):
    chat_id = message.chat.id
    login_input = message.text.strip()
    cand = user_data[chat_id]["new_student"].get("login_candidate")
    if login_input in ['+','/ok','ok','OK','да','Да'] and cand:
        chosen = cand
    else:
        chosen = login_input
    # Проверка дубликата
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных, попробуйте снова ввести логин:")
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM stud_login WHERE stud_login = ?", (chosen,))
        if cur.fetchone():
            bot.send_message(chat_id, "Такой логин уже существует. Введите другой:")
            return
    finally:
        conn.close()
    user_data[chat_id]["new_student"]["login"] = chosen
    user_data[chat_id]["step"] = "adding_student_password"
    bot.send_message(chat_id, "Введите пароль студента:")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "adding_student_password")
def add_student_password_step(message):
    chat_id = message.chat.id
    pwd = message.text.strip()
    data = user_data[chat_id]["new_student"]
    ok, msg = add_student_to_db(data["fullname"], data["birthday"], data["group_id"], data["login"], pwd)
    user_data[chat_id]["step"] = "authenticated"
    user_data[chat_id].pop("new_student", None)
    bot.send_message(chat_id, msg)

# ===== УДАЛЕНИЕ СТУДЕНТА =====
@bot.callback_query_handler(func=lambda call: call.data == "delete_student")
def cb_delete_student(call):
    chat_id = call.message.chat.id
    try:
        bot.answer_callback_query(call.id)
        role = user_data.get(chat_id, {}).get("role")
        print(f"[DEBUG] delete_student pressed chat={chat_id} role={role}")
        if role != ADMIN_R:
            bot.send_message(chat_id, "Нет прав.")
            return
        # Показываем такой же список с пагинацией как для редактирования
        show_student_picker(chat_id, 'delete', 1, 'all')
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка обработчика delete_student: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_student_pick_"))
def delete_student_pick_inline(call):
    """Выбор студента из списка (аналогично редактированию) -> подтверждение удаления."""
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    try:
        sid = int(call.data.split('_')[-1])
    except Exception:
        bot.send_message(chat_id, "Некорректный выбор.")
        return
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных")
        return
    cur = conn.cursor()
    cur.execute("SELECT fullname FROM skating_students WHERE skate_student_id=?", (sid,))
    row = cur.fetchone(); conn.close()
    if not row:
        bot.send_message(chat_id, "Студент не найден.")
        return
    user_data.setdefault(chat_id, {})
    user_data[chat_id]["pending_delete_student_id"] = sid
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да", callback_data="confirm_delete_student"),
               types.InlineKeyboardButton("❌ Нет", callback_data="cancel_delete_student"))
    bot.send_message(chat_id, f"Удалить студента: {row[0]} (ID {sid})?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_delete_student","cancel_delete_student"])
def confirm_delete_student_cb(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    if call.data == "cancel_delete_student":
        user_data[chat_id].pop("pending_delete_student_id", None)
        user_data[chat_id]["step"] = "authenticated"
        bot.send_message(chat_id, "Удаление отменено.")
        return
    sid = user_data[chat_id].get("pending_delete_student_id")
    if not sid:
        bot.send_message(chat_id, "Нет ID для удаления.")
        user_data[chat_id]["step"] = "authenticated"
        return
    ok, msg = remove_student_from_db(sid)
    user_data[chat_id].pop("pending_delete_student_id", None)
    user_data[chat_id]["step"] = "authenticated"
    bot.send_message(chat_id, msg)

# ===== РЕДАКТИРОВАНИЕ СТУДЕНТА =====
@bot.callback_query_handler(func=lambda call: call.data == "edit_student")
def cb_edit_student(call):
    chat_id = call.message.chat.id
    try:
        bot.answer_callback_query(call.id)
        role = user_data.get(chat_id, {}).get("role")
        print(f"[DEBUG] edit_student pressed chat={chat_id} role={role}")
        if role != ADMIN_R:
            bot.send_message(chat_id, "Нет прав.")
            return
        show_student_picker(chat_id, 'edit', 1, 'all')
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка обработчика edit_student: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_student_page_"))
def edit_student_pagination(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    parts = call.data.split('_')
    # edit_student_page_{groupFilter}_{page}
    try:
        group_filter = parts[-2]
        page = int(parts[-1])
    except Exception:
        group_filter = 'all'
        page = 1
    show_student_picker(chat_id, 'edit', page, group_filter)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_student_page_"))
def delete_student_pagination(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    parts = call.data.split('_')
    # delete_student_page_{groupFilter}_{page}
    try:
        group_filter = parts[-2]
        page = int(parts[-1])
    except Exception:
        group_filter = 'all'
        page = 1
    show_student_picker(chat_id, 'delete', page, group_filter)

@bot.callback_query_handler(func=lambda call: call.data == 'transfer_student')
def transfer_student_start(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    role = user_data.get(chat_id, {}).get('role')
    if role != ADMIN_R:
        bot.send_message(chat_id, 'Нет прав.')
        return
    show_student_picker(chat_id, 'transfer', 1, 'all')

@bot.callback_query_handler(func=lambda call: call.data.startswith('transfer_student_page_'))
def transfer_student_pagination(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    parts = call.data.split('_')
    try:
        group_filter = parts[-2]
        page = int(parts[-1])
    except Exception:
        group_filter = 'all'; page = 1
    show_student_picker(chat_id, 'transfer', page, group_filter)

@bot.callback_query_handler(func=lambda call: call.data.startswith('transfer_student_pick_'))
def transfer_student_pick(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    try:
        sid = int(call.data.split('_')[-1])
    except Exception:
        bot.send_message(chat_id, 'Некорректный выбор.')
        return
    # Получаем текущую группу
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, 'Ошибка подключения к базе данных')
        return
    cur = conn.cursor()
    cur.execute('SELECT fullname, group_id FROM skating_students WHERE skate_student_id=?', (sid,))
    row = cur.fetchone(); conn.close()
    if not row:
        bot.send_message(chat_id, 'Студент не найден.')
        return
    fullname, cur_group = row
    user_data.setdefault(chat_id, {})
    user_data[chat_id]['transfer_student_id'] = sid
    # Предлагаем целевые группы
    markup = types.InlineKeyboardMarkup()
    for g in [1,2,3,4]:
        if g == cur_group:
            continue
        markup.add(types.InlineKeyboardButton(f'В группу {g}', callback_data=f'transfer_student_target_{g}'))
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='transfer_student_back'))
    bot.send_message(chat_id, f'Студент: {fullname}\nТекущая группа: {cur_group}\nВыберите новую группу:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'transfer_student_back')
def transfer_student_back(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    show_student_picker(chat_id, 'transfer', 1, user_data.get(chat_id, {}).get('transfer_student_group_filter','all'))

@bot.callback_query_handler(func=lambda call: call.data.startswith('transfer_student_target_'))
def transfer_student_target(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    sid = user_data.get(chat_id, {}).get('transfer_student_id')
    if not sid:
        bot.send_message(chat_id, 'Сначала выберите студента.')
        return
    try:
        new_group = int(call.data.split('_')[-1])
    except Exception:
        bot.send_message(chat_id, 'Некорректная группа.')
        return
    # Подтверждение
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✅ Подтвердить', callback_data=f'transfer_student_confirm_{new_group}'))
    markup.add(types.InlineKeyboardButton('❌ Отмена', callback_data='transfer_student_cancel'))
    bot.send_message(chat_id, f'Перевести студента ID {sid} в группу {new_group}?', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'transfer_student_cancel')
def transfer_student_cancel(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    user_data.get(chat_id, {}).pop('transfer_student_id', None)
    bot.send_message(chat_id, 'Перевод отменён.')
    show_student_picker(chat_id, 'transfer', 1, 'all')

@bot.callback_query_handler(func=lambda call: call.data.startswith('transfer_student_confirm_'))
def transfer_student_confirm(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    sid = user_data.get(chat_id, {}).get('transfer_student_id')
    if not sid:
        bot.send_message(chat_id, 'Студент не выбран.')
        return
    try:
        new_group = int(call.data.split('_')[-1])
    except Exception:
        bot.send_message(chat_id, 'Некорректная группа.')
        return
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, 'Ошибка подключения к базе данных.')
        return
    try:
        cur = conn.cursor()
        cur.execute('UPDATE skating_students SET group_id=? WHERE skate_student_id=?', (new_group, sid))
        conn.commit()
        bot.send_message(chat_id, f'Студент {sid} переведён в группу {new_group}.')
    except Exception as e:
        bot.send_message(chat_id, f'Ошибка перевода: {e}')
    finally:
        conn.close()
        user_data.get(chat_id, {}).pop('transfer_student_id', None)

@bot.callback_query_handler(func=lambda call: call.data in ["edit_student_student_filter","delete_student_student_filter"])  # fallback (не используется)
def deprecated_filter_fallback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Используйте новые кнопки фильтра.")

@bot.callback_query_handler(func=lambda call: call.data in ["edit_student_student_filter_back","delete_student_student_filter_back"])  # fallback
def deprecated_filter_back(call):
    bot.answer_callback_query(call.id)
    manage_students(call.message)

@bot.callback_query_handler(func=lambda call: call.data in ["edit_student_student_filter","delete_student_student_filter"])  # backward compat
def old_filter_handler(call):
    bot.answer_callback_query(call.id)
    action = 'edit' if call.data.startswith('edit') else 'delete'
    show_group_filter(call.message.chat.id, action)

@bot.callback_query_handler(func=lambda call: call.data in ["edit_student_student_filter","delete_student_student_filter","edit_student_student_filter_back","delete_student_student_filter_back"])  # redundancy guard
def old_back_guard(call):
    bot.answer_callback_query(call.id)
    if call.data.endswith('_back'):
        manage_students(call.message)

@bot.callback_query_handler(func=lambda call: call.data in ["edit_student_student_filter","delete_student_student_filter"])  # duplicate guard
def dup_guard(call):
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data in ["edit_student_student_filter","delete_student_student_filter"])  # extra guard
def extra_guard(call):
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data in ["edit_student_student_filter","delete_student_student_filter"])  # final guard
def final_guard(call):
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data in ["edit_student_student_filter","delete_student_student_filter","edit_student_filter","delete_student_filter","edit_student_student_filter_set"])  # broad guard
def broad_guard(call):
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data in ["edit_student_filter","delete_student_filter"])
def open_filter(call):
    bot.answer_callback_query(call.id)
    action = 'edit' if call.data.startswith('edit') else 'delete'
    show_group_filter(call.message.chat.id, action)

@bot.callback_query_handler(func=lambda call: call.data in ["edit_student_filter","delete_student_filter","edit_student_student_filter"])  # unify
def open_filter_unify(call):
    bot.answer_callback_query(call.id)
    action = 'edit' if call.data.startswith('edit') else 'delete'
    show_group_filter(call.message.chat.id, action)

@bot.callback_query_handler(func=lambda call: call.data.endswith('_student_filter'))
def open_filter_new(call):
    bot.answer_callback_query(call.id)
    action = 'edit' if call.data.startswith('edit') else 'delete'
    show_group_filter(call.message.chat.id, action)

@bot.callback_query_handler(func=lambda call: '_student_filter_set_' in call.data)
def set_group_filter(call):
    bot.answer_callback_query(call.id)
    parts = call.data.split('_')
    # pattern: {action}_student_filter_set_{value}
    try:
        action = parts[0]
        group_val = parts[-1]
    except Exception:
        action = 'edit'; group_val = 'all'
    if group_val == 'all':
        gf = 'all'
    else:
        gf = group_val
    show_student_picker(call.message.chat.id, action, 1, gf)

@bot.callback_query_handler(func=lambda call: call.data.endswith('_student_filter_back'))
def group_filter_back(call):
    bot.answer_callback_query(call.id)
    action = 'edit' if call.data.startswith('edit') else 'delete'
    # Возвращаемся к первой странице текущего фильтра (или all)
    show_student_picker(call.message.chat.id, action, 1, user_data.get(call.message.chat.id, {}).get(f"{action}_student_group_filter", 'all'))

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_student_pick_"))
def edit_student_pick(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    try:
        sid = int(call.data.split('_')[-1])
    except Exception:
        bot.send_message(chat_id, "Некорректный выбор.")
        return
    # Имитируем то, что раньше делалось после ввода ID
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных")
        return
    cur = conn.cursor()
    cur.execute("SELECT fullname, birthday, group_id FROM skating_students WHERE skate_student_id=?", (sid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        bot.send_message(chat_id, "Студент не найден.")
        return
    user_data.setdefault(chat_id, {})
    user_data[chat_id]["edit_student"] = {"id": sid, "fullname": row[0], "birthday": row[1], "group_id": row[2]}
    user_data[chat_id]["step"] = "editing_student_field"
    bot.send_message(chat_id, "Что изменить? Введите одно из: fio, date, group. Или 'отмена'")

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_student_pick_"))
def delete_student_pick(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    parts = call.data.split('_')
    try:
        group_filter = parts[-2]
        page = int(parts[-1])
    except Exception:
        group_filter = 'all'
        page = 1
    show_student_picker(chat_id, 'delete', page, group_filter)

@bot.callback_query_handler(func=lambda call: call.data == 'back_manage_students')
def back_to_manage_students(call):
    bot.answer_callback_query(call.id)
    manage_students(call.message)

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "editing_student_id")
def edit_student_id_step(message):
    chat_id = message.chat.id
    if not message.text.isdigit():
        bot.send_message(chat_id, "ID должен быть числом. Введите снова:")
        return
    sid = int(message.text)
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных")
        user_data[chat_id]["step"] = "authenticated"
        return
    cur = conn.cursor()
    cur.execute("SELECT fullname, birthday, group_id FROM skating_students WHERE skate_student_id=?", (sid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        bot.send_message(chat_id, "Студент не найден.")
        user_data[chat_id]["step"] = "authenticated"
        return
    user_data[chat_id]["edit_student"] = {"id": sid, "fullname": row[0], "birthday": row[1], "group_id": row[2]}
    user_data[chat_id]["step"] = "editing_student_field"
    bot.send_message(chat_id, "Что изменить? Введите одно из: fio, date, group. Или 'отмена'")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "editing_student_field")
def edit_student_field_step(message):
    chat_id = message.chat.id
    field = message.text.strip().lower()
    if field == 'отмена':
        user_data[chat_id]["step"] = "authenticated"
        user_data[chat_id].pop("edit_student", None)
        bot.send_message(chat_id, "Редактирование отменено.")
        return
    if field not in ['fio','date','group']:
        bot.send_message(chat_id, "Только fio, date или group. Или 'отмена'")
        return
    user_data[chat_id]["edit_student"]["field"] = field
    user_data[chat_id]["step"] = "editing_student_value"
    prompt = {
        'fio': 'Введите новое ФИО:',
        'date': 'Введите новую дату рождения (ДД.ММ.ГГГГ):',
        'group': 'Введите новый ID группы (1-4):'
    }[field]
    bot.send_message(chat_id, prompt)

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "editing_student_value")
def edit_student_value_step(message):
    chat_id = message.chat.id
    data = user_data[chat_id].get("edit_student")
    field = data.get("field")
    val = message.text.strip()
    if field == 'fio':
        data['fullname'] = val
    elif field == 'date':
        try:
            dt = datetime.strptime(val, "%d.%m.%Y").date()
            data['birthday'] = dt.isoformat()
        except ValueError:
            bot.send_message(chat_id, "Неверная дата. Повторите:")
            return
    elif field == 'group':
        if val not in ['1','2','3','4']:
            bot.send_message(chat_id, "Только 1-4. Повторите:")
            return
        data['group_id'] = int(val)
    # Сохраняем
    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных")
        return
    try:
        cur = conn.cursor()
        cur.execute("UPDATE skating_students SET fullname=?, birthday=?, group_id=? WHERE skate_student_id=?", (data['fullname'], data['birthday'], data['group_id'], data['id']))
        conn.commit()
        bot.send_message(chat_id, "Изменения сохранены.")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при сохранении: {e}")
    finally:
        conn.close()
        user_data[chat_id]["step"] = "authenticated"
        user_data[chat_id].pop("edit_student", None)
# Запуск бота
print("Запуск бота...")
bot.infinity_polling()
