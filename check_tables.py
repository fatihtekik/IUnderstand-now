import sqlite3

conn = sqlite3.connect('zhuldyz.db')
cursor = conn.cursor()

# Проверяем все таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = cursor.fetchall()
print('Все таблицы в базе данных:')
for table in all_tables:
    print(f"- {table[0]}")

# Ищем таблицы с daily в названии
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%daily%'")
daily_tables = cursor.fetchall()
print('\nТаблицы с "daily" в названии:')
for table in daily_tables:
    print(f"- {table[0]}")

# Ищем таблицы с evaluation в названии  
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%evaluation%'")
eval_tables = cursor.fetchall()
print('\nТаблицы с "evaluation" в названии:')
for table in eval_tables:
    print(f"- {table[0]}")

conn.close()
