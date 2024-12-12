import os
import logging
from datetime import datetime
import telebot
from telebot import types
import psycopg2 as psycopg
from telebot.types import ReplyKeyboardRemove
import bcrypt

# Настройка логирования
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
TOKEN = '8154463207:AAGRK4G288WXsWcARiPpHujaZVIoYhn9vtY'
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не установлен в переменных окружения.")
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения.")

bot = telebot.TeleBot(TOKEN)

STUDENT_R = 'student'
TEACHER_R = 'teacher'

# Создание директории для документов, если она не существует
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
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return None

def save_or_update_chat_id(id_student, chat_id):
    conn = connect_to_db()
    if not conn:
        logger.error("Ошибка подключения к базе данных при сохранении chat_id.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM student_chat_id WHERE id_student = %s", (id_student,))
        result = cursor.fetchone()
        if result:
            cursor.execute("UPDATE student_chat_id SET chat_id = %s WHERE id_student = %s", (chat_id, id_student))
            logger.info(f"Обновлён chat_id для студента {id_student}.")
        else:
            cursor.execute("INSERT INTO student_chat_id (id_student, chat_id) VALUES (%s, %s)", (id_student, chat_id))
            logger.info(f"Сохранён новый chat_id для студента {id_student}.")
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении chat_id: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def hash_existing_passwords():
    conn = connect_to_db()
    if not conn:
        logger.error("Ошибка подключения к базе данных для хэширования паролей.")
        return
    try:
        cursor = conn.cursor()

        # Хэширование паролей студентов
        cursor.execute("SELECT id_user, password FROM login")
        users = cursor.fetchall()
        for user in users:
            id_user, plain_password = user
            if plain_password.startswith("$2b$") or plain_password.startswith("$2a$") or plain_password.startswith("$2y$"):
                # Пароль уже захэширован
                continue
            hashed = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE login SET password = %s WHERE id_user = %s", (hashed.decode('utf-8'), id_user))
            logger.info(f"Пароль для студента {id_user} успешно захэширован.")

        # Хэширование паролей преподавателей
        cursor.execute("SELECT teacher_login_id, password FROM teacher_login")
        teachers = cursor.fetchall()
        for teacher in teachers:
            teacher_login_id, plain_password = teacher
            if plain_password.startswith("$2b$") or plain_password.startswith("$2a$") or plain_password.startswith("$2y$"):
                # Пароль уже захэширован
                continue
            hashed = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE teacher_login SET password = %s WHERE teacher_login_id = %s",
                           (hashed.decode('utf-8'), teacher_login_id))
            logger.info(f"Пароль для преподавателя {teacher_login_id} успешно захэширован.")

        conn.commit()
        logger.info("Все пароли успешно захэшированы.")
    except Exception as e:
        logger.error(f"Ошибка при хэшировании паролей: {e}")
    finally:
        cursor.close()
        conn.close()

# Рекомендуется запускать эту функцию только один раз или при необходимости
# hash_existing_passwords()

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
    logger.info(f"Пользователь {chat_id} начал работу с ботом.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "login")
def process_login(message):
    chat_id = message.chat.id
    login = message.text.strip()

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        try:
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
                logger.info(f"Пользователь {chat_id} вошёл как студент: {login}.")
            elif teacher:
                user_data[chat_id]["step"] = "password"
                user_data[chat_id]["login"] = login
                user_data[chat_id]["id_teacher"] = teacher[0]
                user_data[chat_id]["role"] = TEACHER_R
                bot.send_message(chat_id, "Логин преподавателя найден. Введите ваш пароль.")
                logger.info(f"Пользователь {chat_id} вошёл как преподаватель: {login}.")
            else:
                bot.send_message(chat_id, "Такого логина не существует. Попробуйте еще раз.")
                logger.warning(f"Пользователь {chat_id} ввёл несуществующий логин: {login}.")

        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при обработке логина.")
            logger.error(f"Ошибка при обработке логина для пользователя {chat_id}: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        logger.error(f"Пользователь {chat_id} не смог подключиться к базе данных при попытке логина.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "password")
def process_password(message):
    chat_id = message.chat.id
    password = message.text.strip()
    login = user_data[chat_id].get("login")
    role = user_data[chat_id].get("role")

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        try:
            if role == STUDENT_R:
                cursor.execute("SELECT password FROM login WHERE login = %s", (login,))
            elif role == TEACHER_R:
                cursor.execute("SELECT password FROM teacher_login WHERE login = %s", (login,))
            else:
                bot.send_message(chat_id, "Неизвестная роль пользователя.")
                logger.warning(f"Пользователь {chat_id} имеет неизвестную роль: {role}.")
                return

            user = cursor.fetchone()

            if user:
                stored_hash = user[0]
                try:
                    # Проверка формата хэша
                    if not (stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$") or stored_hash.startswith("$2y$")):
                        raise ValueError("Хэш пароля не начинается с допустимого префикса bcrypt.")

                    stored_hash_bytes = stored_hash.encode('utf-8')
                    password_bytes = password.encode('utf-8')

                    if bcrypt.checkpw(password_bytes, stored_hash_bytes):
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                        if role == STUDENT_R:
                            # Сохраняем или обновляем chat_id для студента
                            save_or_update_chat_id(user_data[chat_id]["id_student"], chat_id)
                            markup.add('Академическая успеваемость', 'оценки и GPA', 'Расписание', 'Рейтинг', 'Документы')
                        elif role == TEACHER_R:
                            markup.add('Расписание', 'Переносы', 'Ввод оценок и Н-ок')

                        bot.send_message(chat_id, "Пароль верный! Добро пожаловать!", reply_markup=markup)
                        user_data[chat_id]["step"] = "authenticated"
                        logger.info(f"Пользователь {chat_id} успешно аутентифицирован.")
                    else:
                        bot.send_message(chat_id, "Неверный пароль. Попробуйте еще раз.")
                        logger.warning(f"Пользователь {chat_id} ввёл неверный пароль.")
                except ValueError as ve:
                    bot.send_message(chat_id, "Произошла ошибка при проверке пароля. Пожалуйста, обратитесь к администратору.")
                    logger.error(f"ValueError при проверке пароля для пользователя {chat_id}: {ve}")
                except Exception as e:
                    bot.send_message(chat_id, "Произошла ошибка при проверке пароля. Пожалуйста, обратитесь к администратору.")
                    logger.error(f"Неизвестная ошибка при проверке пароля для пользователя {chat_id}: {e}")
            else:
                bot.send_message(chat_id, "Ошибка получения данных пользователя.")
                logger.error(f"Пользователь {chat_id} не найден в базе данных при проверке пароля.")

        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при подключении к базе данных.")
            logger.error(f"Ошибка подключения к базе данных при проверке пароля для пользователя {chat_id}: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        logger.error(f"Пользователь {chat_id} не смог подключиться к базе данных при проверке пароля.")

# Определение расписаний студентов и преподавателей
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
        logger.warning(f"Пользователь {chat_id} имеет неопределённую роль при выборе расписания.")

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
    logger.info(f"Пользователь {chat_id} выбрал группу: {group_id}.")

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
    logger.info(f"Пользователь {chat_id} выбрал предмет: {subject}.")

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
                logger.info(f"Пользователь {chat_id} запросил расписание для группы {group_id} на {day}.")
            else:
                bot.send_message(chat_id, f'На {day} для группы {group_id} нет занятий.')
                logger.info(f"Пользователь {chat_id} запросил расписание для группы {group_id} на {day}, но занятий нет.")
        else:
            bot.send_message(chat_id, "Группа не найдена в расписании.")
            logger.error(f"Пользователь {chat_id} запросил расписание для несуществующей группы: {group_id}.")

    elif role == TEACHER_R:
        subject = user_data[chat_id].get("subject")
        if subject in teach_schedules:
            schedule = teach_schedules[subject].get(day, [])
            if schedule:
                schedule_text = '\n'.join([f'{i+1}. {g}' for i, g in enumerate(schedule) if g.strip()])
                if schedule_text:
                    bot.send_message(chat_id,
                                     f'Расписание на {day} для предмета {subject}:\n{schedule_text}')
                    logger.info(f"Пользователь {chat_id} запросил расписание для предмета {subject} на {day}.")
                else:
                    bot.send_message(chat_id, f'На {day} для предмета {subject} нет занятий.')
                    logger.info(f"Пользователь {chat_id} запросил расписание для предмета {subject} на {day}, но занятий нет.")
            else:
                bot.send_message(chat_id, f'На {day} для предмета {subject} нет занятий.')
                logger.info(f"Пользователь {chat_id} запросил расписание для предмета {subject} на {day}, но занятий нет.")
        else:
            bot.send_message(chat_id, "Расписание для вашего предмета не найдено.")
            logger.error(f"Пользователь {chat_id} запросил расписание для несуществующего предмета: {subject}.")

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
        logger.warning(f"Пользователь {chat_id} попытался получить GPA без ID студента.")
        return

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        logger.error(f"Пользователь {chat_id} не смог подключиться к базе данных для получения GPA.")
        return
    cursor = conn.cursor()
    try:
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
            logger.info(f"Пользователь {chat_id} не имеет оценок.")
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
        logger.info(f"Пользователь {chat_id} запросил GPA.")
    except Exception as e:
        bot.send_message(chat_id, "Произошла ошибка при получении GPA.")
        logger.error(f"Ошибка при получении GPA для пользователя {chat_id}: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.message_handler(func=lambda message: message.text == 'Академическая успеваемость')
def akadem(message):
    chat_id = message.chat.id
    id_stud = user_data[chat_id].get("id_student")
    if not id_stud:
        bot.send_message(chat_id, "ID студента не найден. Перезапустите бота.")
        logger.warning(f"Пользователь {chat_id} попытался получить академическую успеваемость без ID студента.")
        return

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        logger.error(f"Пользователь {chat_id} не смог подключиться к базе данных для получения академической успеваемости.")
        return
    cursor = conn.cursor()
    try:
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
            logger.info(f"Пользователь {chat_id} не имеет данных об академической успеваемости.")
            return

        markup = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(subject[0], callback_data=f"subject_{subject[0]}") for subject in subjects]
        markup.add(*buttons)
        bot.send_message(chat_id, "Выберите предмет для просмотра успеваемости:", reply_markup=markup)
        logger.info(f"Пользователь {chat_id} выбрал просмотр академической успеваемости.")
    except Exception as e:
        bot.send_message(chat_id, "Произошла ошибка при получении академической успеваемости.")
        logger.error(f"Ошибка при получении академической успеваемости для пользователя {chat_id}: {e}")
    finally:
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
        logger.error(f"Пользователь {chat_id} не смог подключиться к базе данных для просмотра оценок по предмету {subject}.")
        return
    cursor = conn.cursor()
    try:
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
            logger.info(f"Пользователь {chat_id} запросил успеваемость по предмету {subject}, но данных нет.")
            return

        count_z = 0
        result = f"Предмет: *{subject}*\nПреподаватель: *{rows[0][1]}*\nОценки:\n"
        for row in rows:
            nazv, fio_t, ocenka, date = row
            if ocenka > 0:
                result += f" - Оценка: {ocenka}, дата: {date}\n"
            else:
                count_z += 1
                result += f" - Н-ка: {date}\n"
        result += f"\nКоличество Н-ок: {count_z}"

        bot.send_message(chat_id, result, parse_mode="Markdown")
        logger.info(f"Пользователь {chat_id} просмотрел успеваемость по предмету {subject}.")
    except Exception as e:
        bot.send_message(chat_id, "Произошла ошибка при получении успеваемости.")
        logger.error(f"Ошибка при получении успеваемости для пользователя {chat_id} по предмету {subject}: {e}")
    finally:
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
    logger.info(f"Пользователь {chat_id} выбрал управление документами.")

def get_docs(stud):
    conn = connect_to_db()
    if not conn:
        logger.error(f"Ошибка подключения к базе данных при получении документов для студента {stud}.")
        return []
    cursor = conn.cursor()
    try:
        query = "SELECT file_name, file_path FROM documents WHERE stud = %s"
        cursor.execute(query, (stud,))
        documents = cursor.fetchall()
        document_list = [{'file_name': doc[0], 'file_path': doc[1]} for doc in documents]
        logger.info(f"Получено {len(document_list)} документов для студента {stud}.")
        return document_list
    except Exception as e:
        logger.error(f"Ошибка при получении документов для студента {stud}: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def save_file_db(stud, file_name, file_path):
    conn = connect_to_db()
    if not conn:
        logger.error(f"Ошибка подключения к базе данных при сохранении файла {file_name} для студента {stud}.")
        return
    cursor = conn.cursor()
    try:
        query = "INSERT INTO documents (stud, file_name, file_path) VALUES(%s, %s, %s)"
        cursor.execute(query, (stud, file_name, file_path))
        conn.commit()
        logger.info(f"Файл {file_name} сохранён для студента {stud}.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла {file_name} для студента {stud}: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("docs_"))
def handle_docs_callback(call):
    chat_id = call.message.chat.id
    action = call.data
    role = user_data.get(chat_id, {}).get("role")
    id_stud = user_data.get(chat_id, {}).get("id_student")
    id_teach = user_data.get(chat_id, {}).get("id_teacher")

    if action == "docs_add":
        bot.send_message(chat_id, "Отправьте файл вашего документа")

        @bot.message_handler(content_types=['document'])
        def handle_file(message):
            c_id = message.chat.id
            stud_id = user_data.get(c_id, {}).get("id_student")
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
                    logger.info(f"Пользователь {c_id} загрузил документ: {file_name}.")
                except Exception as e:
                    bot.send_message(c_id, "Произошла ошибка при сохранении файла.")
                    logger.error(f"Ошибка при сохранении файла от пользователя {c_id}: {e}")
            else:
                bot.send_message(c_id, "Документ должен быть в виде файла.")
                logger.warning(f"Пользователь {c_id} отправил не файл при попытке загрузить документ.")

    elif action == "docs_show":
        # Показать документы для студента или преподавателя
        if id_stud is not None:
            docum = get_docs(id_stud)
        else:
            # Если есть функционал для преподавателя, можно добавить при необходимости
            docum = []
        if docum:
            for doc in docum:
                try:
                    with open(doc['file_path'], 'rb') as file:
                        bot.send_message(chat_id, f"Документ: {doc['file_name']}")
                        bot.send_document(chat_id, file)
                        logger.info(f"Пользователь {chat_id} получил документ: {doc['file_name']}.")
                except Exception as e:
                    bot.send_message(chat_id, f"Ошибка при отправке документа {doc['file_name']}.")
                    logger.error(f"Ошибка при отправке документа {doc['file_name']} пользователю {chat_id}: {e}")
        else:
            bot.send_message(chat_id, "Вы не загрузили ни один документ.")
            logger.info(f"Пользователь {chat_id} запросил документы, но они отсутствуют.")

@bot.message_handler(func=lambda message: message.text == 'Рейтинг')
def reiting(message):
    chat_id = message.chat.id
    id_stud = user_data[chat_id].get("id_student")
    if not id_stud:
        bot.send_message(chat_id, "ID студента не найден. Перезапустите бота.")
        logger.warning(f"Пользователь {chat_id} попытался получить рейтинг без ID студента.")
        return

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        logger.error(f"Пользователь {chat_id} не смог подключиться к базе данных для получения рейтинга.")
        return
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT students.id_student, ocenki.ocenka
            FROM ocenki 
            JOIN students ON students.id_student = ocenki.id_student  
            ORDER BY students.id_student
        ''')
        rows = cursor.fetchall()
        if not rows:
            bot.send_message(chat_id, "Нет данных об оценках.")
            logger.info(f"Пользователь {chat_id} не имеет данных для рейтинга.")
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

        # Сортировка по среднему баллу (по убыванию)
        students_avg.sort(key=lambda x: x["avg_grade"], reverse=True)

        result = ""
        for index, student in enumerate(students_avg):
            rank = index + 1
            avg_grade = student["avg_grade"]
            count_zeros = student["count_zeros"]
            result += f"Место: {rank}.\nСредний балл: {avg_grade:.2f}.   Н-ок: {count_zeros}\n\n"

        # Поиск места текущего пользователя
        user_rank = next((index + 1 for index, student in enumerate(students_avg) if student["id_student"] == id_stud), None)
        if user_rank:
            user_avg = students_avg[user_rank - 1]['avg_grade']
            user_zeros = students_avg[user_rank - 1]['count_zeros']
            result += f"\nВаше место: {user_rank}.\nСредний балл: {user_avg:.2f}\nКоличество Н-ок: {user_zeros}"
            logger.info(f"Пользователь {chat_id} получил свой рейтинг: место {user_rank}.")
        else:
            result += "\nНе удалось найти ваше место в рейтинге."
            logger.warning(f"Пользователь {chat_id} не найден в рейтинге.")

        bot.send_message(chat_id, result)
    except Exception as e:
        bot.send_message(chat_id, "Произошла ошибка при получении рейтинга.")
        logger.error(f"Ошибка при получении рейтинга для пользователя {chat_id}: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.message_handler(func=lambda message: message.text == 'Переносы')
def vvod(message):
    chat_id = message.chat.id
    role = user_data[chat_id].get("role")
    id_teach = user_data[chat_id].get("id_teacher")
    if role == STUDENT_R:
        bot.send_message(chat_id, "Этой функцией могут пользоваться только учителя.")
        logger.warning(f"Студент {chat_id} попытался использовать функцию переноса.")
    elif role == TEACHER_R:
        conn = connect_to_db()
        if not conn:
            bot.send_message(chat_id, "Ошибка подключения к базе данных.")
            logger.error(f"Преподаватель {chat_id} не смог подключиться к базе данных для переноса.")
            return
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT gruppy.nazvanie_gruppy 
                FROM gruppy
                JOIN spec_teacher ON spec_teacher.spec_id = gruppy.spec_id
                WHERE spec_teacher.teacher_id = %s
            ''', (id_teach,))
            rows = cursor.fetchall()
            if not rows:
                bot.send_message(chat_id, "Нет данных о группах.")
                logger.info(f"Преподаватель {chat_id} не имеет связанных групп.")
                return
            markup = types.InlineKeyboardMarkup()
            for row in rows:
                nazvanie_gruppy = row[0]
                button = types.InlineKeyboardButton(text=nazvanie_gruppy, callback_data=f"perenos_{nazvanie_gruppy}")
                markup.add(button)
            bot.send_message(chat_id, "Выберите группу:", reply_markup=markup)
            logger.info(f"Преподаватель {chat_id} выбрал управление переносами для групп.")
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при получении групп.")
            logger.error(f"Ошибка при получении групп для преподавателя {chat_id}: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        bot.send_message(chat_id, "Ваша роль не определена. Обратитесь к администратору.")
        logger.warning(f"Пользователь {chat_id} имеет неопределённую роль при попытке использования переноса.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("perenos_"))
def choose_group_pzh(call):
    chat_id = call.message.chat.id
    group_name = call.data.split("_")[1]
    user_data[chat_id]["perenos"] = {
        "group_name": group_name,
        "process_completed": False
    }
    bot.send_message(chat_id, "Напишите сообщение студентам группы.")
    logger.info(f"Преподаватель {chat_id} выбрал группу {group_name} для переноса.")

@bot.message_handler(func=lambda message: "perenos" in user_data.get(message.chat.id, {}) and not user_data[message.chat.id]["perenos"]["process_completed"])
def handle_group_message(message):
    chat_id = message.chat.id
    text_message = message.text
    group_name = user_data[chat_id]["perenos"]["group_name"]
    id_teach = user_data[chat_id].get("id_teacher")

    conn = connect_to_db()
    if not conn:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        logger.error(f"Преподаватель {chat_id} не смог подключиться к базе данных для отправки сообщения.")
        return
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_gruppy FROM gruppy WHERE nazvanie_gruppy = %s", (group_name,))
        group_id = cursor.fetchone()
        if group_id:
            group_id = group_id[0]
        else:
            bot.send_message(chat_id, "Группа не найдена в базе данных.")
            logger.error(f"Преподаватель {chat_id} выбрал несуществующую группу: {group_name}.")
            cursor.close()
            conn.close()
            return

        cursor.execute("SELECT fio_teacher FROM teachers WHERE id_teacher = %s", (id_teach,))
        teacher_name = cursor.fetchone()
        teacher_name = teacher_name[0] if teacher_name else "Преподаватель"

        # Сохраняем сообщение о переносе в БД
        try:
            cursor.execute("INSERT INTO reschedule (id_gruppy, text_message) VALUES (%s, %s)", (group_id, text_message))
            conn.commit()
            logger.info(f"Преподаватель {chat_id} сохранил сообщение о переносе для группы {group_id}.")
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка записи в базу данных: {e}")
            logger.error(f"Ошибка записи сообщения о переносе от преподавателя {chat_id} для группы {group_id}: {e}")
            cursor.close()
            conn.close()
            return

        # Отправляем сообщение студентам
        try:
            cursor.execute("SELECT chat_id FROM student_chat_id WHERE id_gruppy = %s", (group_id,))
            students = cursor.fetchall()
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка получения списка студентов: {e}")
            logger.error(f"Ошибка при получении списка студентов для группы {group_id}: {e}")
            cursor.close()
            conn.close()
            return

        cursor.close()
        conn.close()

        if not students:
            bot.send_message(chat_id, "В этой группе нет зарегистрированных учеников.")
            logger.info(f"Группа {group_id} не имеет зарегистрированных студентов.")
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
                logger.info(f"Студент {student_id} получил сообщение от преподавателя {chat_id}.")
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения студенту {student_id}: {e}")

        bot.send_message(chat_id, "Сообщение отправлено всем ученикам группы.")
        user_data[chat_id]["perenos"]["process_completed"] = True
    except Exception as e:
        bot.send_message(chat_id, "Произошла ошибка при обработке сообщения.")
        logger.error(f"Ошибка при обработке сообщения о переносе для преподавателя {chat_id}: {e}")
    finally:
        cursor.close()
        conn.close()

# Функция для получения chat_id студента
def get_student_chat_id(student_id):
    conn = connect_to_db()
    if not conn:
        logger.error(f"Ошибка подключения к базе данных при получении chat_id для студента {student_id}.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM student_chat_id WHERE id_student = %s", (student_id,))
        result = cursor.fetchone()
        if result:
            logger.info(f"Получен chat_id для студента {student_id}: {result[0]}.")
            return result[0]
        else:
            logger.warning(f"chat_id не найден для студента {student_id}.")
            return None
    except Exception as e:
        logger.error(f"Ошибка при получении chat_id для студента {student_id}: {e}")
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
    logger.info(f"Преподаватель {chat_id} открыл меню ввода оценок и Н-ок.")

@bot.message_handler(func=lambda message: message.text == 'Выставить оценку' and user_data.get(message.chat.id, {}).get("role") == TEACHER_R)
def ask_student_for_grade(message):
    chat_id = message.chat.id
    id_teach = user_data[chat_id].get("id_teacher")
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT students.id_student, students.fio
                FROM spec_teacher
                JOIN gruppy ON gruppy.spec_id = spec_teacher.spec_id
                JOIN students ON students.id_gruppy = gruppy.id_gruppy
                WHERE spec_teacher.teacher_id = %s
            ''', (id_teach,))
            students = cursor.fetchall()
            if students:
                markup = types.InlineKeyboardMarkup(row_width=1)
                for student in students:
                    student_id, fio = student
                    markup.add(types.InlineKeyboardButton(text=fio, callback_data=f"select_student_grade_{student_id}"))
                bot.send_message(chat_id, "Выберите студента из списка:", reply_markup=markup)
                user_data[chat_id]["step"] = "selecting_student_for_grade"
                logger.info(f"Преподаватель {chat_id} выбрал выставление оценки.")
            else:
                bot.send_message(chat_id, "Список студентов пуст.")
                logger.info(f"Преподаватель {chat_id} попытался выставить оценку, но список студентов пуст.")
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при получении списка студентов.")
            logger.error(f"Ошибка при получении списка студентов для преподавателя {chat_id}: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")
        logger.error(f"Преподаватель {chat_id} не смог подключиться к базе данных для выставления оценок.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_student_grade_"))
def receive_student_for_grade(call):
    chat_id = call.message.chat.id
    student_id = int(call.data.split("_")[-1])
    user_data[chat_id]["student_id_for_grade"] = student_id
    user_data[chat_id]["step"] = "awaiting_grade_date"
    bot.send_message(chat_id, "Введите дату в формате ДД.ММ.ГГГГ:")
    logger.info(f"Преподаватель {chat_id} выбрал студента {student_id} для выставления оценки.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "awaiting_grade_date")
def receive_grade_date(message):
    chat_id = message.chat.id
    date_text = message.text.strip()
    try:
        date_obj = datetime.strptime(date_text, "%d.%m.%Y").date()
        user_data[chat_id]["grade_date"] = date_obj
        user_data[chat_id]["step"] = "awaiting_grade_value"
        bot.send_message(chat_id, "Введите оценку (от 0 до 100):")
        logger.info(f"Преподаватель {chat_id} ввёл дату оценки: {date_obj}.")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ.")
        logger.warning(f"Преподаватель {chat_id} ввёл неверный формат даты: {date_text}.")

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
                logger.error(f"Преподаватель {chat_id} не смог подключиться к базе данных для выставления оценки.")
                return
            cursor = conn.cursor()
            try:
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
                        f"У этого студента уже есть оценка на {grade_date.strftime('%d.%m.%Y')}: {existing_grade[0]}.\nОбновить её?",
                        reply_markup=markup
                    )
                    user_data[chat_id]["step"] = "confirming_update_grade"
                    user_data[chat_id]["new_grade"] = grade
                    logger.info(f"Преподаватель {chat_id} запросил обновление оценки для студента {student_id} на дату {grade_date}.")
                else:
                    # Вставляем новую оценку
                    cursor.execute(
                        "INSERT INTO ocenki (id_student, id_teacher, ocenka, date) VALUES (%s, %s, %s, %s)",
                        (student_id, id_teach, grade, grade_date)
                    )
                    conn.commit()
                    logger.info(f"Преподаватель {chat_id} выставил оценку {grade} для студента {student_id} на дату {grade_date}.")

                    # Уведомляем студента о новой оценке
                    cursor.execute("SELECT chat_id FROM student_chat_id WHERE id_student = %s", (student_id,))
                    student_chat_id = cursor.fetchone()
                    if student_chat_id:
                        student_chat_id = student_chat_id[0]
                        cursor.execute("SELECT fio_teacher FROM teachers WHERE id_teacher = %s", (id_teach,))
                        teacher_fio = cursor.fetchone()
                        teacher_fio = teacher_fio[0] if teacher_fio else "Преподаватель"
                        bot.send_message(
                            student_chat_id,
                            f"Вам выставлена новая оценка {grade} от преподавателя {teacher_fio} на дату {grade_date.strftime('%d.%m.%Y')}."
                        )
                        logger.info(f"Студент {student_id} уведомлён о новой оценке {grade} от преподавателя {id_teach}.")
                    bot.send_message(chat_id, "Оценка успешно сохранена и студент уведомлён.")
                    user_data[chat_id]["step"] = "authenticated"
            except Exception as e:
                bot.send_message(chat_id, "Произошла ошибка при сохранении оценки.")
                logger.error(f"Ошибка при сохранении оценки для студента {student_id} преподавателем {chat_id}: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            bot.send_message(chat_id, "Введите корректную оценку от 0 до 100.")
            logger.warning(f"Преподаватель {chat_id} ввёл некорректную оценку: {grade}.")
    except ValueError:
        bot.send_message(chat_id, "Введите числовое значение для оценки.")
        logger.warning(f"Преподаватель {chat_id} ввёл нечисловое значение для оценки: {message.text}.")

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
            logger.error(f"Преподаватель {chat_id} не смог подключиться к базе данных для обновления оценки.")
            return
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE ocenki SET ocenka = %s WHERE id_student = %s AND id_teacher = %s AND date = %s",
                (new_grade, student_id, id_teach, grade_date)
            )
            conn.commit()
            logger.info(f"Преподаватель {chat_id} обновил оценку для студента {student_id} на дату {grade_date} до {new_grade}.")

            # Уведомляем студента о новой оценке
            cursor.execute("SELECT chat_id FROM student_chat_id WHERE id_student = %s", (student_id,))
            student_chat_id = cursor.fetchone()
            if student_chat_id:
                student_chat_id = student_chat_id[0]
                cursor.execute("SELECT fio_teacher FROM teachers WHERE id_teacher = %s", (id_teach,))
                teacher_fio = cursor.fetchone()
                teacher_fio = teacher_fio[0] if teacher_fio else "Преподаватель"
                bot.send_message(
                    student_chat_id,
                    f"Вам выставлена новая оценка {new_grade} от преподавателя {teacher_fio} на дату {grade_date.strftime('%d.%m.%Y')}."
                )
                logger.info(f"Студент {student_id} уведомлён об обновлении оценки до {new_grade}.")
            bot.send_message(chat_id, "Оценка успешно обновлена и студент уведомлён.")
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при обновлении оценки.")
            logger.error(f"Ошибка при обновлении оценки для студента {student_id} преподавателем {chat_id}: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        bot.send_message(chat_id, "Операция отменена. Оценка не была изменена.")
        logger.info(f"Преподаватель {chat_id} отменил обновление оценки.")

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
    role = user_data.get(chat_id, {}).get("role")
    user_data[chat_id]["step"] = "authenticated"
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
        logger.warning(f"Пользователь {chat_id} с неопределённой ролью попытался вернуться назад.")
        return
    bot.send_message(chat_id, "Вы вернулись в главное меню.", reply_markup=markup)
    logger.info(f"Пользователь {chat_id} вернулся в главное меню.")

@bot.message_handler(func=lambda message: message.text == 'Ввод оценок и Н-ок' and user_data.get(message.chat.id, {}).get("role") == TEACHER_R)
def teacher_menu(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Выставить оценку', 'Отметить пропуск', 'Назад')
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)
    logger.info(f"Преподаватель {chat_id} открыл меню ввода оценок и Н-ок.")

# Запуск бота
try:
    bot.infinity_polling()
except Exception as e:
    logger.critical(f"Бот неожиданно завершил работу: {e}")
