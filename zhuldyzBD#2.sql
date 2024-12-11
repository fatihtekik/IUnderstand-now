CREATE SCHEMA zhuldyz;
DROP SCHEMA zhuldyz CASCADE;

-- 1. Таблица категорий (зависимости отсутствуют)
CREATE TABLE category (
    id_category INT PRIMARY KEY,
    category_name VARCHAR(100)
);

-- 2. Таблица тренеров (зависимости отсутствуют)
CREATE TABLE coach (
    coach_id INT PRIMARY KEY,
    coach_name VARCHAR(100)
);

-- 3. Таблица групп (зависимости от категорий и тренеров)
CREATE TABLE groups (
    group_id INT PRIMARY KEY,
    id_category INT,
    coach_id INT,
    FOREIGN KEY (id_category) REFERENCES category(id_category),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);

-- 4. Таблица студентов (зависимость от групп)
CREATE TABLE skating_students (
    skate_student_id INT PRIMARY KEY,
    fullname VARCHAR(100),
    birthday DATE,
    group_id INT,
    FOREIGN KEY (group_id) REFERENCES groups(group_id)
);




-- 5. Таблица входа тренеров (зависимость от тренеров)
CREATE TABLE coach_login (
    coach_login_id INT PRIMARY KEY,
    coach_id INT, 
    coach_login VARCHAR(100),
    coach_password VARCHAR(100),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);

-- 6. Таблица входа студентов (зависимость от студентов)
CREATE TABLE stud_login (
    stud_login_id INT PRIMARY KEY,
    skate_student_id INT,
    stud_login VARCHAR(100),
    stud_password VARCHAR(100),
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id)
);

-- 7. Таблица чата студентов (зависимость от студентов и групп)
CREATE TABLE stud_chat (
    stud_chat_id SERIAL PRIMARY KEY,
    skate_student_id INT, 
    group_id INT,
    skate_chat_id INT,
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id),
    FOREIGN KEY (group_id) REFERENCES groups(group_id)
);

-- 8. Таблица расписания (зависимость от групп)
CREATE TABLE skate_rescheldue (
    reschedule_id SERIAL PRIMARY KEY,
    group_id INT,
    text_message TEXT,
    FOREIGN KEY (group_id) REFERENCES groups(group_id)
);

-- 9. Таблица посещаемости (зависимость от студентов и тренеров)
CREATE TABLE attendance (
    attendance_id SERIAL PRIMARY KEY,
    attendance VARCHAR(1),
    skate_student_id INT,
    coach_id INT,
    date DATE,
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);
-- 10. Таблица документов (зависимость от студентов)
CREATE TABLE docs (
    document_id SERIAL PRIMARY KEY,
    skate_student_id INT,
    name_file VARCHAR(255),
    path_file TEXT,
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id)
);

-- 11. Таблица ролей (зависимость от студентов и тренеров)
CREATE TABLE roles (
    role_id INT PRIMARY KEY,
    skate_student_id INT,
    coach_id INT,
    role VARCHAR(30),
    FOREIGN KEY (skate_student_id) REFERENCES skating_students(skate_student_id),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);
INSERT INTO category (id_category, category_name) VALUES
(1, 'Старшая'),
(2, 'Средняя'),
(3, 'Младшая');
INSERT INTO coach (coach_id, coach_name) VALUES
(5, 'Madina')
(1, 'Ясмин'),
(2, 'Майя'),
(3, 'Фатих'),
(4, 'Салима');

INSERT INTO groups (group_id, id_category, coach_id) VALUES
(1, 1, 1),
(2, 2, 2),
(3, 3, 3),
(4, 3, 4);
INSERT INTO skating_students (skate_student_id, fullname, birthday, group_id) VALUES
(1, 'Адема Мурзанова', '2017-09-25', 1),
(2, 'Амина Бектурганова', '2018-01-13', 1),
(3, 'Амира Мейрамова', '2017-05-21', 1),
(4, 'Aсылым Еншібай', '2017-06-28', 1),
(5, 'Даяня Нурлан', '2016-11-24', 1),
(6, 'Маржан Муратканова', '2017-07-17', 1),
(7, 'Мариям Амиртай', '2017-04-16', 1),
(8, 'Марьям Айтпек', '2016-08-03', 1),
(9, 'Сенiм Малик', '2014-11-09', 1),
(10, 'Айару Есенова', '2015-05-29', 1),
(11, 'Марат Аяру', '2017-03-31', 1),
(12, 'Марат Даяня', '2018-11-27', 1),
(13, 'Есенова Райлана', '2017-09-09', 1),
(14, 'Аиша Кабдушева', '2020-02-21', 2),
(15, 'Балауса Байтенова', '2019-11-13', 2),
(16, 'Зейнеп Атай Азра', '2018-12-14', 2),
(17, 'Мариям Жеттiс', '2019-05-28', 2),
(18, 'Салтанат Мурзанова', '2019-07-03', 2),
(19, 'Селин Науруз', '2021-01-10', 2),
(20, 'Ланика Аринанда', '2018-04-20', 2),
(21, 'Сара Шамсутдинова', '2016-07-20', 2),
(22, 'Амина Жадраева', '2015-06-25', 2),
(23, 'Марат Мерей', '2020-03-21', 2),
(24, 'Амаль Ерлан', '2017-03-11', 2),
(25, 'Аяла Беембетова', '2017-07-27', 2),
(26, 'Сарыгюль Кайла', '2018-04-20', 2),
(27, 'Амалия Бисатова', '2017-01-30', 3),
(28, 'Инкар Иралимова', '2017-09-09', 3),
(29, 'Ханшайын Ахматолла', '2017-12-25', 3),
(30, 'Зейiн Ахматолла', '2020-10-07', 3),
(31, 'Жанайши Каржас', '2020-10-07', 3),
(32, 'Жанбота Толеген', '2017-09-27', 3),
(33, 'Касым Айтпек', '2020-01-19', 3),
(34, 'Зере Азаматкызы', '2018-05-08', 3),
(35, 'Сафия Ербулат', '2018-11-06', 4),
(36, 'Дарина Мурзабаева', '2019-02-23', 4),
(37, 'Наркес Сейлбек', '2017-10-14', 4),
(38, 'Айлана Адамзатбова', '2017-06-04', 4),
(39, 'Radmila Dyyak', '2019-10-29', 4),
(40, 'Альма Садыкова', '2021-04-04', 4),
(41, 'Дания Ерлан', '2020-01-28', 2);


INSERT INTO stud_login (stud_login_id, skate_student_id, stud_login, stud_password) VALUES
(1, 1, 'adema_murz_1', 'adema_1'),
(2, 2, 'amina_bekt_2', 'amina_2'),
(3, 3, 'amira_meir_3', 'amira_3'),
(4, 4, 'asylim_yensh_4', 'asylym_4!'),
(5, 5, 'dayanya_nurl_5', 'dayana_5'),
(6, 6, 'marzhan_mur_6', 'marzhan_6'),
(7, 7, 'mariyam_amir_7', 'mariyam_7'),
(8, 8, 'maryam_aitp_8', 'mariyam_8'),
(9, 9, 'senim_mal_9', 'malik_9'),
(10, 10, 'ayaru_esen_10', 'ayaru_10'),
(11, 11, 'marat_ayaru_11', 'marat_aya_11'),
(12, 12, 'marat_dayan_12', 'dayan_12'),
(13, 13, 'esenova_rail_13', 'esenova_aya_13'),
(14, 14, 'aisha_kabd_14', 'aisha_14'),
(15, 15, 'balausa_bai_15', 'balausa_15'),
(16, 16, 'zeynep_atay_16', 'zeynep_16'),
(17, 17, 'mariyam_jeti_17', 'mariyam_jeti_17'),
(18, 18, 'saltanat_mur_18', 'saltanat_18'),
(19, 19, 'selin_naur_19', 'selin_19'),
(20, 20, 'lanika_arin_20', 'lanika_20'),
(21, 21, 'sara_shams_21', 'sara_21'),
(22, 22, 'amina_jadr_22', 'amina_22'),
(23, 23, 'marat_merey_23', 'merey_23'),
(24, 24, 'amal_erlan_24', 'erlan_24'),
(25, 25, 'ayala_beem_25', 'ayala_25'),
(26, 26, 'sarygul_kay_26', 'sarygyl_26'),
(27, 27, 'amaliya_bis_27', 'amaliya_27'),
(28, 28, 'inkar_iral_28', 'inkar_28'),
(29, 29, 'khanshayn_akh_29', 'khansayan_29'),
(30, 30, 'zeyin_akh_30', 'zeiyn_31'),
(31, 31, 'zhanaishy_kar_31', 'zhanaishy_32'),
(32, 32, 'zhanbota_tol_32', 'zhanbota_33'),
(33, 33, 'kasym_aitp_33', 'kasym_33'),
(34, 34, 'zere_azam_34', 'zere_34'),
(35, 35, 'safiya_erbu_35', 'safiya_35'),
(36, 36, 'darina_murz_36', 'darina_36'),
(37, 37, 'narkes_seil_37', 'narkes_37'),
(38, 38, 'ailana_adam_38', 'ailana_38'),
(39, 39, 'radmila_dyy_39', 'radmila_39'),
(40, 40, 'alma_sadyk_40', 'alma_40'),
(41, 41, 'daniya_erlan_41', 'daniya_41');
INSERT INTO roles (role_id, skate_student_id, coach_id, role) VALUES
(46,null,5,'admin')
(1, 1, null, 'student'),
(2, 2, null, 'student'),
(3, 3, null, 'student'),
(4, 4, null, 'student'),
(5, 5, null, 'student'),
(6, 6, null, 'student'),
(7, 7, null, 'student'),
(8, 8, null, 'student'),
(9, 9, null, 'student'),
(10, 10, null, 'student'),
(11, 11, null, 'student'),
(12, 12, null, 'student'),
(13, 13, null, 'student'),
(14, 14, null, 'student'),
(15, 15, null, 'student'),
(16, 16, null, 'student'),
(17, 17, null, 'student'),
(18, 18, null, 'student'),
(19, 19, null, 'student'),
(20, 20, null, 'student'),
(21, 21, null, 'student'),
(22, 22, null, 'student'),
(23, 23, null, 'student'),
(24, 24, null, 'student'),
(25, 25, null, 'student'),
(26, 26, null, 'student'),
(27, 27, null, 'student'),
(28, 28, null, 'student'),
(29, 29, null, 'student'),
(30, 30, null, 'student'),
(31, 31, null, 'student'),
(32, 32, null, 'student'),
(33, 33, null, 'student'),
(34, 34, null, 'student'),
(35, 35, null, 'student'),
(36, 36, null, 'student'),
(37, 37, null, 'student'),
(38, 38, null, 'student'),
(39, 39, null, 'student'),
(40, 40, null, 'student'),
(41, 41, null, 'student'),
(42, null, 1, 'coach'),
(43, null, 2, 'coach'),
(44, null, 3, 'coach'),
(45, null, 4, 'coach');

INSERT INTO coach_login (coach_login_id, coach_id, coach_login, coach_password) VALUES
(5,5,'Madina_admin76','admin76')
(1, 1, 'Yasmin_coach1', 'yasmin_t'),
(2, 2, 'Maya_coach2', 'maya_1'),
(3, 3, 'Fatih_coach3', 'fatkik'),
(4, 4, 'Salima_coach4', 'salima_a');
select *from stud_chat 
-- Перемещаем Марат Аяру (id=11) и Марат Даяня (id=12) в группу 2 (Средняя)
UPDATE skating_students SET group_id = 2 WHERE skate_student_id = 11;
UPDATE skating_students SET group_id = 2 WHERE skate_student_id = 12;

-- Перемещаем Аяла Беембетова (id=25) в группу 1 (Старшая)
UPDATE skating_students SET group_id = 1 WHERE skate_student_id = 25;
