import telebot
from telebot import types
import psycopg2

token='7576683979:AAF3OwSTLwIA_AAnu0ZVOZUpCk3lIJWsQTQ'
bot=telebot.TeleBot(token)

login=""
#Подключение к БД
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname = "postgres",
            user = "postgres",
            password = "Aidana2007",
            host = "localhost",
            port = "5432"
        )
        return conn
    except Exception as e:
        print("Ошибка подключения к базе данных.")
        return None

user_data = {}
@bot.message_handler(commands=['start'])
def start_message(message):
  bot.send_message(message.chat.id,"Добро пожаловать в EVALIX, бот по учебной части!\n Введите ваш логин.")

  user_data[message.chat.id] = {"step": "login"}  # Сохраняем, что находимся на шаге ввода логина


@bot.message_handler(
    func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == "login")
def process_login(message):
    login = message.text.strip()

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT login FROM login WHERE login = %s", (login,))
        user = cursor.fetchone()

        if user:
            user_data[message.chat.id]["step"] = "password"  # Переводим пользователя на шаг ввода пароля
            user_data[message.chat.id]["login"] = login  # Сохраняем логин для дальнейшей проверки пароля
            user_data[message.chat.id]["id_student"] = user[0]
            bot.send_message(message.chat.id, "Логин найден. Введите ваш пароль.")
        else:
            bot.send_message(message.chat.id, "Такого логина не существует. Попробуйте еще раз.")

        cursor.close()
        conn.close()

    else:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")


@bot.message_handler(
    func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == "password")
def process_password(message):
    password = message.text.strip()
    login = user_data[message.chat.id].get("login")

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM login WHERE login = %s", (login,))
        user = cursor.fetchone()

        if user and user[0] == password:  # Проверка пароля
            bot.send_message(message.chat.id, "Пароль верный! Добро пожаловать!")
            user_data[message.chat.id]["step"] = "authenticated"  # Пользователь успешно аутентифицирован
        else:
            bot.send_message(message.chat.id, "Неверный пароль. Попробуйте еще раз.")

        cursor.close()
        conn.close()

    else:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")

#основные кнопки
@bot.message_handler(commands=['command'])
def command_message(message):
  markup = types.ReplyKeyboardMarkup()
  btn_akadem = types.KeyboardButton(text='Академическая успеваемость')
  btn_gpa = types.KeyboardButton(text='оценки и GPA')
  btn_scheldue = types.KeyboardButton(text='Расписание')
  btn_perenosi = types.KeyboardButton(text='Переносы')
  btn_vvod = types.KeyboardButton(text='Ввод оценок и N-ок')
  btn_srav = types.KeyboardButton(text='Рейтинг')
  btn_docs = types.KeyboardButton(text= 'Документы')
  btn_pay = types.KeyboardButton(text='Оплата за учёбу')
  markup.add(btn_akadem, btn_gpa, btn_scheldue, btn_perenosi, btn_vvod, btn_srav, btn_docs, btn_pay)
  bot.send_message(message.chat.id, 'Список услуг.', reply_markup= markup)

#РАСПИСАНИЕ
week_schedule = {
    'ПН': ['ИКТ', 'ИКТ', 'Алгоритмы'],
    'ВТ': ['Алгоритмы', 'БД', 'ИКТ'],
    'СР': ['БД', 'БД', 'Алгоритмы'],
    'ЧТ': ['Алгоритмы', 'Алгоритмы', 'БД'],
    'ПТ': ['БД', 'БД', 'БД']
}


@bot.message_handler(func=lambda message: message.text == 'Расписание')
def show_schedule_buttons(message):
    markup = types.InlineKeyboardMarkup()
    week = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']
    buttons = [types.InlineKeyboardButton(day, callback_data=day) for day in week]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Выберите день недели:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def show_day_schedule(call):
    day = call.data
    schedule = '\n'.join([f'{i + 1}. {lesson}' for i, lesson in enumerate(week_schedule.get(day, []))])
    bot.send_message(call.message.chat.id, f'Расписание на {day}:\n{schedule}')


@bot.message_handler(func=lambda message: message.text == 'оценки и GPA')
def show_GPA(message):
    name_student = user_data[message.chat.id].get("id_student")

    conn = connect_to_db()

    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT id_student FROM login WHERE login = %s", (name_student,))

    id_student = cursor.fetchone()[0]

    cursor.execute(
        '''SELECT ocenki.id_ocenki, ocenki.ocenka, students.FIO, teachers.FIO_teacher, ocenki.date 
           FROM ocenki 
           JOIN students ON students.id_student = ocenki.id_student 
           JOIN teachers ON teachers.id_teacher = ocenki.id_teacher 
           WHERE students.id_student = %s 
           ORDER BY ocenki.date''', (id_student,)
    )

    rows = cursor.fetchall()


    column_names = [desc[0] for desc in cursor.description]

    result = ""
    for row in rows:
        row_dict = {column_names[i]: row[i] for i in range(len(row))}
        result += f"Оценка: {row_dict['ocenka']}, Студент: {row_dict['fio']}, Преподаватель: {row_dict['fio_teacher']}, Дата: {row_dict['date']}\n"

    if result:
        bot.send_message(message.chat.id, result)
    else:
        bot.send_message(message.chat.id, "Нет данных об оценках.")


bot.infinity_polling()
