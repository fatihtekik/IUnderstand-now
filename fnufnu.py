import telebot
from pyexpat.errors import messages
from telebot import types
import psycopg2
from telebot.formatting import mspoiler
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove

token='7576683979:AAF3OwSTLwIA_AAnu0ZVOZUpCk3lIJWsQTQ'
bot=telebot.TeleBot(token)

STUDENT_R = 'student'
TEACHER_R = 'teacher'


login=""
#Подключение к БД
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname = "postgres",
            user = "postgres",
            password = "qweasd09id",
            host = "localhost",
            port = "5433"
        )
        return conn
    except Exception as e:
        print("Ошибка подключения к базе данных.")
        return None

user_data = {}
@bot.message_handler(commands=['start'])
def start_message(message):
  bot.send_message(message.chat.id,"Добро пожаловать в EVALIX, бот по учебной части!\n Введите ваш логин.", reply_markup=ReplyKeyboardRemove())
  user_data[message.chat.id] = {"step": "login"}  # Сохраняем, что находимся на шаге ввода логина

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == "login")
def process_login(message):
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
            user_data[message.chat.id]["role"] = STUDENT_R
            bot.send_message(message.chat.id, "Логин студента найден. Введите ваш пароль.")
        elif teacher:
            user_data[message.chat.id]["step"] = "password"
            user_data[message.chat.id]["login"] = login
            user_data[message.chat.id]["id_teacher"] = teacher[0]
            user_data[message.chat.id]["role"] = TEACHER_R
            bot.send_message(message.chat.id, "Логин преподавателя найден. Введите ваш пароль.")
        else:
            bot.send_message(message.chat.id, "Такого логина не существует. Попробуйте еще раз.")


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
                    types.KeyboardButton('оценки и GPA'),
                    types.KeyboardButton('Расписание'),
                    types.KeyboardButton('Переносы'),
                    types.KeyboardButton('Рейтинг'),
                    types.KeyboardButton('Документы'),
                    types.KeyboardButton('Оплата за учёбу')
                )
            elif role == TEACHER_R:
                markup.add(
                    types.KeyboardButton('Расписание'),
                    types.KeyboardButton('Переносы'),
                    types.KeyboardButton('Документы')
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

#РАСПИСАНИЕ
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

#Выбор группы
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



@bot.message_handler(func=lambda message: message.text == 'оценки и GPA')
def show_GPA(message):
    name_student = user_data[message.chat.id].get("id_student")
#вы забыли найти айдишку и получали ошибку вместо цифры
    conn = connect_to_db()

    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT id_student FROM login WHERE login = %s", (name_student,))

    id_student = cursor.fetchone()[0]

    cursor.execute(
        '''SELECT ocenki.ocenka, teachers.FIO_teacher, ocenki.date 
           FROM ocenki 
           JOIN students ON students.id_student = ocenki.id_student 
           JOIN teachers ON teachers.id_teacher = ocenki.id_teacher 
           WHERE students.id_student = %s 
           ORDER BY ocenki.date''', (id_student,)
    )

    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "Нет данных об оценках.")
        cursor.close()
        conn.close()
        return



    column_names = [desc[0] for desc in cursor.description]
    grades=[]

    result = ""
    for row in rows:
        ocenka, fio_teacher, date = row
        row_dict = {column_names[i]: row[i] for i in range(len(row))}
        result += f"Оценка: {row_dict['ocenka']}\nПреподаватель: {row_dict['fio_teacher']}\nДата: {row_dict['date']}\n\n"

        ocenka_int= int(ocenka)
        gpa= get_gpa_from_score(ocenka_int)
        grades.append(gpa)







    if grades:
        gpa = sum(grades)/ len(grades)
        result+= f"Ваш GPA: {gpa:.2f}"
    else:
        result+="Не удалость рассчитать GPA, так как нету оценок"
    if result:
        bot.send_message(message.chat.id, result)
    else:
        bot.send_message(message.chat.id, "Нет данных об оценках.")


@bot.message_handler(func=lambda message: message.text == 'Академическая успеваемость')
def akadem(message):
    name_student = user_data[message.chat.id].get("id_student")
    # вы забыли найти айдишку и получали ошибку вместо цифры
    conn = connect_to_db()

    if not conn:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT id_student FROM login WHERE login = %s", (name_student,))

    id_student = cursor.fetchone()[0]

    cursor.execute(
        '''SELECT ocenki.ocenka, teachers.FIO_teacher, ocenki.date 
           FROM ocenki 
           JOIN students ON students.id_student = ocenki.id_student 
           JOIN teachers ON teachers.id_teacher = ocenki.id_teacher 
           WHERE students.id_student = %s 
           ORDER BY ocenki.date''', (id_student,)
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
        grades.append(int(ocenka))

    if grades:
        cr = sum(grades) / len(grades)
        result += f"Ваш средний бал: {cr:.2f}"
    else:
        result += "Нету оценок"
    if result:
        bot.send_message(message.chat.id, result)
    else:
        bot.send_message(message.chat.id, "Нет данных об оценках.")


@bot.message_handler(func=lambda message: message.text == 'Переносы')
def insert_resheldue(message):
    if user_data[message.chat.id]['role'] == TEACHER_R:
        markup = types.InlineKeyboardMarkup()
        groups = ['ПО2301', 'ПО2302', 'ВТ2310']
        buttons = [types.InlineKeyboardButton(group, callback_data=f"choose_group_{group}") for group in groups]
        markup.add(*buttons)
        bot.send_message(message.chat.id, "Выберите группу для отправки сообщения о переносе:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Только преподаватели могут использовать эту функцию.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_group_"))
def choose_group(call):
    group_id = call.data.split("_")[2]
    user_data[call.message.chat.id]['selected_group'] = group_id
    bot.send_message(call.message.chat.id, f"Вы выбрали группу {group_id}. Напишите сообщение о переносе:")

@bot.message_handler(func=lambda message: message.chat.id in user_data and "selected_group" in user_data[message.chat.id])
def handle_reschedule_message(message):
    groupa = user_data[message.chat.id]["selected_group"]
    reschedule_message = message.text
    id_t = get_t_id(user_data[message.chat.id].get("login"))

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
                        INSERT INTO reschedule (id_teacher, nazvanie_gruppy, message)
                        VALUES (%s, %s, %s)
                        """, (id_t, groupa, reschedule_message))
        print(f"группы: {groupa}")
        conn.commit()

        # Выборка студентов
        cursor.execute(
            "SELECT id_student FROM students WHERE id_gruppy = (SELECT id_gruppy FROM gruppy WHERE nazvanie_gruppy = %s)",
            (groupa,))
        students = cursor.fetchall()

        if students:
            for student in students:
                student_id = student[0]
                bot.send_message(student_id, f"Важное сообщение от преподавателя:\n{reschedule_message}")
            bot.send_message(message.chat.id, f"Сообщение о переносе отправлено студентам группы {groupa}.")
        else:
            bot.send_message(message.chat.id, "Студенты в выбранной группе не найдены.")
        cursor.close()
        conn.close()
    else:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")


def get_t_id(name_teacher):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("Select id_teacher from teacher_login where login =%s", (name_teacher,))
    print(name_teacher)
    id_t = cursor.fetchone()[0]
    return id_t



bot.infinity_polling()
