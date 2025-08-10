-- SQLite версия базы данных zhuldyz
-- Без INSERT операций, кроме ролей, тренеров и категорий

PRAGMA foreign_keys = ON;

-- 1. Таблица категорий (зависимости отсутствуют)
CREATE TABLE category (
    id_category INTEGER PRIMARY KEY,
    category_name TEXT
);

-- 2. Таблица тренеров (зависимости отсутствуют)
CREATE TABLE coach (
    coach_id INTEGER PRIMARY KEY,
    coach_name TEXT
);

-- 3. Таблица групп (зависимости от категорий и тренеров)
CREATE TABLE groups (
    group_id INTEGER PRIMARY KEY,
    id_category INTEGER,
    coach_id INTEGER,
    FOREIGN KEY (id_category) REFERENCES category(id_category),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);

-- 4. Таблица студентов (зависимость от групп)
CREATE TABLE skating_students (
    skate_student_id INTEGER PRIMARY KEY,
    fullname TEXT,
    birthday DATE,
    group_id INTEGER,
    FOREIGN KEY (group_id) REFERENCES groups(group_id)
);

-- 5. Таблица входа тренеров (зависимость от тренеров)
CREATE TABLE coach_login (
    coach_login_id INTEGER PRIMARY KEY,
    coach_id INTEGER, 
    coach_login TEXT,
    coach_password TEXT,
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);

-- 6. Таблица входа студентов (зависимость от студентов)
CREATE TABLE stud_login (
    stud_login_id INTEGER PRIMARY KEY,
    skate_student_id INTEGER,
    stud_login TEXT,
    stud_password TEXT,
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id)
);

-- 7. Таблица чата студентов (зависимость от студентов и групп)
CREATE TABLE stud_chat (
    stud_chat_id INTEGER PRIMARY KEY,
    skate_student_id INTEGER, 
    group_id INTEGER,
    skate_chat_id INTEGER,
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id),
    FOREIGN KEY (group_id) REFERENCES groups(group_id)
);

-- 8. Таблица расписания (зависимость от групп)
CREATE TABLE skate_rescheldue (
    reschedule_id INTEGER PRIMARY KEY,
    group_id INTEGER,
    text_message TEXT,
    FOREIGN KEY (group_id) REFERENCES groups(group_id)
);

-- 9. Таблица посещаемости (зависимость от студентов и тренеров)
CREATE TABLE attendance (
    attendance_id INTEGER PRIMARY KEY,
    attendance TEXT,
    skate_student_id INTEGER,
    coach_id INTEGER,
    date DATE,
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);

-- 10. Таблица документов (зависимость от студентов)
CREATE TABLE docs (
    document_id INTEGER PRIMARY KEY,
    skate_student_id INTEGER,
    name_file TEXT,
    path_file TEXT,
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id)
);

-- 11. Таблица ролей (зависимость от студентов и тренеров)
CREATE TABLE roles (
    role_id INTEGER PRIMARY KEY,
    skate_student_id INTEGER,
    coach_id INTEGER,
    role TEXT,
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);

-- 12. Таблица элементов
CREATE TABLE elements (
    element_id INTEGER PRIMARY KEY,
    group_id INTEGER,
    coach_id INTEGER,
    element_type TEXT, -- 'Прыжок', 'Вращение', 'Скольжение'
    name TEXT,
    FOREIGN KEY (group_id) REFERENCES groups(group_id),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);

-- 13. Таблица заданий для тренеров
CREATE TABLE coach_tasks (
    task_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    deadline DATE NOT NULL,
    created_by INTEGER, -- ID админа который создал задание
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_completed INTEGER DEFAULT 0, -- 0 = не выполнено, 1 = выполнено
    FOREIGN KEY (created_by) REFERENCES coach(coach_id)
);

-- 14. Таблица назначения заданий тренерам
CREATE TABLE task_assignments (
    assignment_id INTEGER PRIMARY KEY,
    task_id INTEGER,
    coach_id INTEGER,
    assigned_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_date DATETIME NULL,
    status INTEGER DEFAULT 0, -- 0 = не выполнено, 1 = выполнено
    FOREIGN KEY (task_id) REFERENCES coach_tasks(task_id),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);

-- 15. Таблица расписания групп по дням недели
CREATE TABLE group_schedule (
    schedule_id INTEGER PRIMARY KEY,
    group_id INTEGER,
    day_of_week INTEGER, -- 1=ПН, 2=ВТ, 3=СР, 4=ЧТ, 5=ПТ, 6=СБ, 7=ВС
    start_time TEXT, -- время начала "17:45"
    end_time TEXT,   -- время окончания "18:45"
    activity_type TEXT, -- тип занятия "лед", "ОФП", "акробатика" и т.д.
    is_active INTEGER DEFAULT 1, -- 1 = активно, 0 = отменено
    FOREIGN KEY (group_id) REFERENCES groups(group_id)
);

-- 16. Таблица индивидуального расписания студентов (если студент пропускает определенные дни)
CREATE TABLE student_schedule_exceptions (
    exception_id INTEGER PRIMARY KEY,
    skate_student_id INTEGER,
    day_of_week INTEGER, -- день недели, который студент пропускает
    exception_type TEXT, -- 'skip' = не приходит в этот день, 'custom' = особое расписание
    notes TEXT,
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id)
);

-- 15. Таблица оценок по дате для тренеров и их групп
CREATE TABLE daily_evaluations (
    evaluation_id INTEGER PRIMARY KEY,
    coach_id INTEGER,
    group_id INTEGER,
    evaluation_date DATE NOT NULL,
    performance_score INTEGER CHECK(performance_score >= 1 AND performance_score <= 10), -- Оценка работы
    group_progress INTEGER CHECK(group_progress >= 1 AND group_progress <= 10), -- Прогресс группы
    attendance_quality INTEGER CHECK(attendance_quality >= 1 AND attendance_quality <= 10), -- Качество посещаемости
    notes TEXT, -- Дополнительные заметки
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id),
    FOREIGN KEY (group_id) REFERENCES groups(group_id),
    UNIQUE(coach_id, group_id, evaluation_date) -- Одна оценка в день для тренера и группы
);

-- INSERT данных для групп (нужно создать группы перед расписанием)
INSERT INTO groups (group_id, id_category, coach_id) VALUES
(1, 1, 1), -- Старшая группа, тренер Ясмин
(2, 2, 2), -- Средняя группа, тренер Майя  
(3, 3, 3), -- Младшая группа, тренер Фатих
(4, 3, 4); -- Младшая группа, тренер Салима

-- INSERT расписания для групп
-- Группа 1 (Старшая - УТГ, тренер Ясмин): ПН, ВТ, СР, ЧТ, ПТ, ВС
INSERT INTO group_schedule (group_id, day_of_week, start_time, end_time, training_type) VALUES
-- Понедельник
(1, 1, '16:30', '17:30', 'СФП'),
(1, 1, '17:45', '18:45', 'лед'),
(1, 1, '19:00', '19:45', 'хорео/ОФП'),
-- Вторник
(1, 2, '09:15', '10:00', 'СФП'),
(1, 2, '10:15', '11:15', 'лед'),
(1, 2, '11:30', '12:30', 'ОФП'),
-- Среда
(1, 3, '16:30', '17:30', 'СФП'),
(1, 3, '17:45', '18:45', 'лед'),
(1, 3, '19:00', '19:45', 'хорео/ОФП'),
-- Четверг
(1, 4, '09:15', '10:00', 'СФП'),
(1, 4, '10:15', '11:15', 'лед'),
(1, 4, '11:30', '12:30', 'ОФП'),
-- Пятница
(1, 5, '15:00', '15:45', 'СФП'),
(1, 5, '16:00', '17:45', 'лед'),
(1, 5, '18:00', '19:00', 'хорео'),
-- Воскресенье
(1, 7, '15:30', '16:30', 'СФП/хорео'),
(1, 7, '16:45', '17:45', 'лед'),
(1, 7, '18:00', '19:00', 'хорео');

-- Группа 2 (Средняя): ПН, СР, ПТ, ВС
INSERT INTO group_schedule (group_id, day_of_week, start_time, end_time, training_type) VALUES
-- Понедельник
(2, 1, '17:45', '18:45', 'лед'),
(2, 1, '19:00', '19:45', 'ОФП'),
-- Среда
(2, 3, '17:45', '18:45', 'лед'),
(2, 3, '19:00', '19:45', 'ОФП'),
-- Пятница
(2, 5, '17:15', '18:15', 'лед'),
(2, 5, '18:30', '19:15', 'ОФП'),
-- Воскресенье
(2, 7, '15:45', '16:00', 'ОФП'),
(2, 7, '16:45', '17:45', 'лед');

-- Группа 3 (Младшая - Фатих): ПН, СР, ПТ, ВС
INSERT INTO group_schedule (group_id, day_of_week, start_time, end_time, training_type) VALUES
-- Понедельник
(3, 1, '17:45', '18:45', 'лед'),
(3, 1, '19:00', '19:45', 'ОФП'),
-- Среда
(3, 3, '17:45', '18:45', 'лед'),
(3, 3, '19:00', '19:45', 'ОФП'),
-- Пятница
(3, 5, '17:15', '18:15', 'лед'),
(3, 5, '18:30', '19:15', 'ОФП'),
-- Воскресенье
(3, 7, '15:45', '16:00', 'ОФП'),
(3, 7, '16:45', '17:45', 'лед');

-- Группа 4 (Младшая - Салима): ПН, СР, ПТ, ВС
INSERT INTO group_schedule (group_id, day_of_week, start_time, end_time, training_type) VALUES
-- Понедельник
(4, 1, '17:45', '18:45', 'лед'),
(4, 1, '19:00', '19:45', 'ОФП'),
-- Среда
(4, 3, '17:45', '18:45', 'лед'),
(4, 3, '19:00', '19:45', 'ОФП'),
-- Пятница
(4, 5, '17:15', '18:15', 'лед'),
(4, 5, '18:30', '19:15', 'ОФП'),
-- Воскресенье
(4, 7, '15:45', '16:00', 'ОФП'),
(4, 7, '16:45', '17:45', 'лед');

-- INSERT данных для категорий
INSERT INTO category (id_category, category_name) VALUES
(1, 'Старшая'),
(2, 'Средняя'),
(3, 'Младшая');

-- INSERT данных для тренеров
INSERT INTO coach (coach_id, coach_name) VALUES
(1, 'Ясмин'),
(2, 'Майя'),
(3, 'Фатих'),
(4, 'Салима'),
(5, 'Madina');

-- INSERT данных для логинов тренеров
INSERT INTO coach_login (coach_login_id, coach_id, coach_login, coach_password) VALUES
(1, 1, 'Yasmin_coach1', 'yasmin_t'),
(2, 2, 'Maya_coach2', 'maya_1'),
(3, 3, 'Fatih_coach3', 'fatkik'),
(4, 4, 'Salima_coach4', 'salima_a'),
(5, 5, 'Madina_admin76', 'admin76');

-- INSERT данных для групп
INSERT INTO groups (group_id, id_category, coach_id) VALUES
(1, 1, 1), -- Старшая группа с тренером Ясмин
(2, 2, 2), -- Средняя группа с тренером Майя
(3, 3, 3), -- Младшая группа с тренером Фатих
(4, 3, 4); -- Младшая группа с тренером Салима

-- INSERT данных для ролей тренеров
INSERT INTO roles (role_id, skate_student_id, coach_id, role) VALUES
(42, NULL, 1, 'coach'),
(43, NULL, 2, 'coach'),
(44, NULL, 3, 'coach'),
(45, NULL, 4, 'coach'),
(46, NULL, 5, 'admin');

-- INSERT данных для расписания групп
-- Группа 1 (Старшая)
INSERT INTO group_schedule (group_id, day_of_week, start_time, end_time, activity_type) VALUES
(1, 1, '17:45', '18:45', 'лед'),      -- ПН
(1, 1, '18:55', '19:55', 'ОФП'),      -- ПН
(1, 3, '17:45', '18:45', 'лед'),      -- СР
(1, 3, '18:55', '19:55', 'ОФП'),      -- СР
(1, 5, '17:15', '18:15', 'лед'),      -- ПТ
(1, 5, '18:30', '19:30', 'ОФП/акробатика'), -- ПТ
(1, 7, '15:30', '16:30', 'СФП/растяжка'), -- ВС
(1, 7, '16:45', '17:45', 'лед');      -- ВС

-- Группа 2 (Средняя)
INSERT INTO group_schedule (group_id, day_of_week, start_time, end_time, activity_type) VALUES
(2, 1, '17:45', '18:45', 'лед'),      -- ПН
(2, 1, '18:55', '19:55', 'ОФП'),      -- ПН
(2, 3, '17:45', '18:45', 'лед'),      -- СР
(2, 3, '18:55', '19:55', 'ОФП'),      -- СР
(2, 5, '17:15', '18:15', 'лед'),      -- ПТ
(2, 5, '18:30', '19:30', 'ОФП/акробатика'), -- ПТ
(2, 7, '15:30', '16:30', 'СФП/растяжка'), -- ВС
(2, 7, '16:45', '17:45', 'лед');      -- ВС

-- Группа 3 (Младшая Фатих)
INSERT INTO group_schedule (group_id, day_of_week, start_time, end_time, activity_type) VALUES
(3, 1, '17:45', '18:45', 'лед'),      -- ПН
(3, 1, '18:55', '19:55', 'ОФП'),      -- ПН
(3, 2, '16:00', '17:00', 'тренировка'), -- ВТ
(3, 2, '17:15', '18:15', 'отработка элементов'), -- ВТ
(3, 2, '18:30', '19:30', 'растяжка'), -- ВТ
(3, 3, '17:45', '18:45', 'лед'),      -- СР
(3, 3, '18:55', '19:55', 'ОФП'),      -- СР
(3, 4, '16:00', '17:00', 'тренировка'), -- ЧТ
(3, 4, '17:15', '18:15', 'растяжка'), -- ЧТ
(3, 4, '18:30', '19:30', 'отработка элементов'), -- ЧТ
(3, 5, '17:15', '18:15', 'лед'),      -- ПТ
(3, 5, '18:30', '19:30', 'ОФП/акробатика'), -- ПТ
(3, 7, '15:30', '16:30', 'СФП/растяжка'), -- ВС
(3, 7, '16:45', '17:45', 'лед');      -- ВС

-- Группа 4 (Младшая Салима)
INSERT INTO group_schedule (group_id, day_of_week, start_time, end_time, activity_type) VALUES
(4, 1, '17:45', '18:45', 'лед'),      -- ПН
(4, 1, '18:55', '19:55', 'ОФП'),      -- ПН
(4, 3, '17:45', '18:45', 'лед'),      -- СР
(4, 3, '18:55', '19:55', 'ОФП'),      -- СР
(4, 5, '17:15', '18:15', 'лед'),      -- ПТ
(4, 5, '18:30', '19:30', 'ОФП/акробатика'), -- ПТ
(4, 7, '15:30', '16:30', 'СФП/растяжка'), -- ВС
(4, 7, '16:45', '17:45', 'лед');      -- ВС
