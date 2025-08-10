import sqlite3
from datetime import datetime

# Подключение к базе данных
conn = sqlite3.connect('zhuldyz.db')
cursor = conn.cursor()

# Новый список студентов из таблицы
new_students = [
    # Группа 1 (Ясмин) - старшая группа
    {"name": "Сенiм Малик", "birthday": "2014-11-09", "group": 1},
    {"name": "Мариям Амиртай", "birthday": "2017-04-16", "group": 1},
    {"name": "Маржан Муратканова", "birthday": "2017-07-17", "group": 1},
    {"name": "Амина Бектурганова", "birthday": "2018-01-13", "group": 1},
    {"name": "Амира Мейрамова", "birthday": "2017-05-21", "group": 1},
    {"name": "Асылым Еншібай", "birthday": "2017-06-28", "group": 1},
    {"name": "Адема Мурзанова", "birthday": "2017-09-25", "group": 1},
    {"name": "Зейнеп Азра Атай", "birthday": "2018-12-14", "group": 1},
    {"name": "Марьям Айтпек", "birthday": "2016-08-03", "group": 1},
    {"name": "Аяла Беембетова", "birthday": "2017-07-27", "group": 1},
    {"name": "Айару Есенова", "birthday": "2015-03-29", "group": 1},
    {"name": "Райлана Есенова", "birthday": "2017-09-09", "group": 1},
    {"name": "Айша Бейсенбек", "birthday": "2012-11-01", "group": 1},
    
    # Группа 2 (Майя) - средняя группа  
    {"name": "Марат Аяру", "birthday": "2017-03-31", "group": 2},
    {"name": "Марат Даяна", "birthday": "2018-11-27", "group": 2},
    {"name": "Марат Мерей", "birthday": "2020-03-21", "group": 2},
    {"name": "Салтанат Мурзанова", "birthday": "2019-07-03", "group": 2},
    {"name": "Амина Мурзанова", "birthday": "2021-04-14", "group": 2},
    {"name": "Балауса Байтенова", "birthday": "2019-11-13", "group": 2},
    {"name": "Касым Айтпек", "birthday": "2020-01-19", "group": 2},
    {"name": "Сарыгюль Кайла", "birthday": "2018-04-20", "group": 2},
    {"name": "Аиша Кабдушева", "birthday": "2020-02-21", "group": 2},
    {"name": "Селин Науруз", "birthday": "2021-01-10", "group": 2},
    {"name": "Ханшайын Ахматолла", "birthday": "2017-12-25", "group": 2},
    {"name": "Амалия Бисатова", "birthday": "2017-01-30", "group": 2},
    {"name": "Инкар Иралимова", "birthday": "2017-09-09", "group": 2},
    {"name": "Cафия Ербулат", "birthday": "2018-11-06", "group": 2},
    {"name": "Дарина Мурзабаева", "birthday": "2019-02-23", "group": 2},
    {"name": "Жанайши Каржас", "birthday": "2017-05-12", "group": 2},
    {"name": "Айлана Адамзатова", "birthday": "2017-06-04", "group": 2},
    {"name": "Зере Азаматкызы", "birthday": "2018-05-08", "group": 2},
    {"name": "Радмила Dyyak", "birthday": "2019-10-29", "group": 2},
    {"name": "Мажит Айдана", "birthday": "2019-03-14", "group": 2},
    {"name": "Ербол Гулим", "birthday": "2019-07-24", "group": 2},
    {"name": "Кайратбек Айшолпан", "birthday": "2020-11-05", "group": 2},
    {"name": "Мукашева Зара", "birthday": "2017-11-04", "group": 2},
    {"name": "Арна", "birthday": "2021-01-01", "group": 2},
    {"name": "Даяна Нурлан", "birthday": "2016-11-24", "group": 2},
    {"name": "Сара Шамсутдинова", "birthday": "2016-07-20", "group": 2},
    
    # Группа 3 (Фатих) - младшая группа
    {"name": "Наркес Сейлбек", "birthday": "2017-10-14", "group": 3},
    {"name": "Аяла Сестренка Дамели", "birthday": "2018-06-26", "group": 3},
    {"name": "Сардар", "birthday": "2020-01-01", "group": 3},
    {"name": "Дина", "birthday": "2021-01-01", "group": 3},
    {"name": "Серик Аиша", "birthday": "2018-06-18", "group": 3},
    
    # Группа 4 (Салима) - младшая группа
    {"name": "Анарбек Томирис", "birthday": "2021-07-01", "group": 4},
    {"name": "Мурат Асыл", "birthday": "2019-11-01", "group": 4},
    {"name": "Сейдахмет Аяулым", "birthday": "2020-01-17", "group": 4},
    {"name": "Шахматова София", "birthday": "2019-08-31", "group": 4},
    {"name": "Мұратбек Алина", "birthday": "2019-01-26", "group": 4}
]

print("🔄 Начинаем обновление базы данных студентов...")

# 1. Сначала удаляем всех существующих студентов и связанные данные
print("\n🗑️ Удаляем старых студентов и связанные данные...")

# Удаляем данные в правильном порядке (из-за внешних ключей)
cursor.execute("DELETE FROM attendance")
cursor.execute("DELETE FROM stud_chat")
cursor.execute("DELETE FROM docs")
cursor.execute("DELETE FROM roles WHERE skate_student_id IS NOT NULL")
cursor.execute("DELETE FROM stud_login")
cursor.execute("DELETE FROM skating_students")

print("✅ Старые студенты и связанные данные удалены")

# 2. Добавляем новых студентов
print("\n➕ Добавляем новых студентов...")
student_id = 1
for student in new_students:
    try:
        # Добавляем студента
        cursor.execute("""
            INSERT INTO skating_students (skate_student_id, fullname, birthday, group_id) 
            VALUES (?, ?, ?, ?)
        """, (student_id, student["name"], student["birthday"], student["group"]))
        
        # Создаем логин (простой формат: имя_id)
        login = f"{student['name'].replace(' ', '_').lower()}_{student_id}"
        password = f"pass_{student_id}"
        
        cursor.execute("""
            INSERT INTO stud_login (stud_login_id, skate_student_id, stud_login, stud_password) 
            VALUES (?, ?, ?, ?)
        """, (student_id, student_id, login, password))
        
        # Добавляем роль студента
        cursor.execute("""
            INSERT INTO roles (skate_student_id, coach_id, role) 
            VALUES (?, NULL, 'student')
        """, (student_id,))
        
        print(f"✅ Добавлен: {student['name']} (Группа {student['group']})")
        student_id += 1
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении {student['name']}: {e}")

# Сохраняем изменения
conn.commit()

# 3. Проверяем результат
cursor.execute("""
    SELECT s.fullname, s.birthday, s.group_id, c.category_name, co.coach_name
    FROM skating_students s
    JOIN groups g ON s.group_id = g.group_id
    JOIN category c ON g.id_category = c.id_category
    JOIN coach co ON g.coach_id = co.coach_id
    ORDER BY s.group_id, s.fullname
""")

updated_students = cursor.fetchall()

print(f"\n📊 Итого добавлено студентов: {len(updated_students)}")
print("\n👥 Список студентов по группам:")

current_group = None
for student in updated_students:
    name, birthday, group_id, category, coach = student
    if group_id != current_group:
        current_group = group_id
        print(f"\n🔸 Группа {group_id} ({category}) - Тренер: {coach}")
    print(f"  • {name} ({birthday})")

conn.close()
print("\n✅ Обновление базы данных завершено!")
