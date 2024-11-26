import telebot
from telebot import types

token='7576683979:AAF3OwSTLwIA_AAnu0ZVOZUpCk3lIJWsQTQ'
bot=telebot.TeleBot(token)

#приветсвие. пофикшу!!1!
@bot.message_handler(commands=['start'])
def start_message(message):
  bot.send_message(message.chat.id,"Добро пожаловать в бот по учебной части! ")

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
#КОНЕЦ РАСПИСАНИЯ



bot.infinity_polling()