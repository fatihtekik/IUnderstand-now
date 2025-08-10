import sqlite3

conn = sqlite3.connect('zhuldyz.db')
cursor = conn.cursor()

# Проверяем структуру таблицы daily_evaluations
cursor.execute("PRAGMA table_info(daily_evaluations)")
columns = cursor.fetchall()
print("Текущие столбцы в daily_evaluations:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

# Создаем новую таблицу без attendance_quality
cursor.execute("""
CREATE TABLE daily_evaluations_new (
    evaluation_id INTEGER PRIMARY KEY,
    coach_id INTEGER,
    group_id INTEGER,
    evaluation_date DATE NOT NULL,
    performance_score INTEGER CHECK(performance_score >= 1 AND performance_score <= 10),
    group_progress INTEGER CHECK(group_progress >= 1 AND group_progress <= 10),
    notes TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id),
    FOREIGN KEY (group_id) REFERENCES groups(group_id),
    UNIQUE(coach_id, group_id, evaluation_date)
)
""")

# Копируем данные (исключая attendance_quality)
cursor.execute("""
INSERT INTO daily_evaluations_new 
(evaluation_id, coach_id, group_id, evaluation_date, performance_score, group_progress, notes, created_date)
SELECT evaluation_id, coach_id, group_id, evaluation_date, performance_score, group_progress, notes, created_date
FROM daily_evaluations
""")

# Удаляем старую таблицу
cursor.execute("DROP TABLE daily_evaluations")

# Переименовываем новую таблицу
cursor.execute("ALTER TABLE daily_evaluations_new RENAME TO daily_evaluations")

conn.commit()
print("Таблица daily_evaluations обновлена - удален столбец attendance_quality")

# Проверяем новую структуру
cursor.execute("PRAGMA table_info(daily_evaluations)")
columns = cursor.fetchall()
print("\nНовые столбцы в daily_evaluations:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

conn.close()
