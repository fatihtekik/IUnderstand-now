import sqlite3
import sys

# Подключаемся к базе данных
conn = sqlite3.connect('zhuldyz.db')
cursor = conn.cursor()

# Читаем и выполняем SQL файл
with open('zhuldyzBD#2.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()
    
# Разбиваем на отдельные команды
sql_commands = sql_content.split(';')

for command in sql_commands:
    command = command.strip()
    if command:
        try:
            cursor.execute(command)
            print(f'Выполнено: {command[:50]}...')
        except Exception as e:
            print(f'Ошибка при выполнении команды: {e}')
            print(f'Команда: {command}')

conn.commit()
conn.close()
print('База данных создана успешно!')
