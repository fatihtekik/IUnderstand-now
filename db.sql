drop schema public cascade;
create schema public;

CREATE TABLE spec (
    spec_id SERIAL PRIMARY KEY, 
    spec_name VARCHAR(255) NOT NULL
);

CREATE TABLE gruppy (
    id_gruppy SERIAL PRIMARY KEY,  
    nazvanie_gruppy VARCHAR(255) NOT NULL,     
    spec_id INT,
    CONSTRAINT fk_gruppy_spec FOREIGN KEY (spec_id) REFERENCES spec (spec_id)
);

CREATE TABLE students (
    id_student SERIAL PRIMARY KEY, 
    FIO VARCHAR(255) NOT NULL,               
    IIN CHAR(12) NOT NULL UNIQUE,            
    id_gruppy INT,
    CONSTRAINT fk_students_gruppy FOREIGN KEY (id_gruppy) REFERENCES gruppy (id_gruppy)
);

CREATE TABLE teachers (
    id_teacher SERIAL PRIMARY KEY, 
    FIO_teacher VARCHAR(255) NOT NULL, 
    IIN CHAR(12) NOT NULL UNIQUE, 
    nazvanie_predmeta VARCHAR(100)
);

CREATE TABLE ocenki (
    id_ocenki SERIAL PRIMARY KEY, 
    ocenka INT NOT NULL, 
    id_student INT, 
    id_teacher INT, 
    date DATE NOT NULL,
    CONSTRAINT fk_ocenki_student FOREIGN KEY (id_student) REFERENCES students (id_student),
    CONSTRAINT fk_ocenki_teacher FOREIGN KEY (id_teacher) REFERENCES teachers (id_teacher)
);

CREATE TABLE spec_teacher (
    spec_id INT, 
    teacher_id INT,
    PRIMARY KEY (spec_id, teacher_id),
    CONSTRAINT fk_spec_teacher_spec FOREIGN KEY (spec_id) REFERENCES spec (spec_id),
    CONSTRAINT fk_spec_teacher_teacher FOREIGN KEY (teacher_id) REFERENCES teachers (id_teacher)
);
INSERT INTO spec (spec_id, spec_name) VALUES
(1, 'Программное обеспечение'),
(2, 'Вычислительная техника');

INSERT INTO gruppy (id_gruppy, nazvanie_gruppy, spec_id) VALUES
(1, 'ПО2302', 1),
(2, 'ПО2301', 1),
(3, 'ВТ2310', 2);


INSERT INTO students (id_student, FIO, IIN, id_gruppy) 
VALUES 
    (1, 'Шугаева Анель Маратовна', '070324651515', 1),
    (2, 'Калиева Айдана Талгатовна', '070527651616', 1),
    (3, 'Текик Фатих Салих', '080203553557', 1),
	(4, 'Раймбекова Айым Максатовна', '080603245588', 1),
	(5, 'Жакупбекова Диана Бекайдаровна', '070616060509', 1),
	(6, 'Поперечный Данила Алексеевич ','959894656712',2),
	(7, 'Музиченко Юрий Юриевич','023152648721',2),
	(8, 'Прусикин Илья Владимирович','015489365879',2),
	(9, 'Габидуллин Руслан Ильсиярович','325489685247',2),
	(10, 'Куплинов Дмитрий Алексеевич','658915462357',2),
	(11, 'Павел Виктор Андреевич','315698745612',3),
	(12, 'Воля Павел Алексеевич','326587462598',3),
	(13, 'Быков Андрей Вячеславович','658947235489',3),
	(14, 'Лобанов Семен Семенович','654892453672',3),
	(15, 'Сабуров Нурлан Алибекович','312598762541',3);


INSERT INTO teachers (id_teacher, FIO_teacher, IIN, nazvanie_predmeta) VALUES
(1, 'Ахмадиева Арай Кайратовна', '060415651515', 'Информационно-коммуникационные технологии'),
(2, 'Шапигуллин Бекдаулет Алтынбекович', '051212651616', 'Организация обработки базы данных'),
(3, 'Музданов Бауыржан Темиртасович', '070327553577', 'Информатика');



INSERT INTO ocenki (id_ocenki, ocenka, id_student, id_teacher, date) VALUES
(1, 85, 1, 1, '2023-09-10'),
(2, 90, 1, 2, '2023-10-15'),
(3, 80, 1, 3, '2023-11-20'),
(4, 78, 1, 1, '2024-01-05'),
(5, 88, 1, 2, '2024-02-18'),

(6, 92, 2, 1, '2023-09-12'),
(7, 85, 2, 2, '2023-10-18'),
(8, 75, 2, 3, '2023-11-22'),
(9, 78, 2, 1, '2024-01-07'),
(10, 95, 2, 2, '2024-02-20'),

(11, 70, 3, 1, '2023-09-14'),
(12, 85, 3, 2, '2023-10-20'),
(13, 88, 3, 3, '2023-11-25'),
(14, 80, 3, 1, '2024-01-10'),
(15, 90, 3, 2, '2024-02-22'),

(16, 75, 4, 1, '2023-09-16'),
(17, 80, 4, 2, '2023-10-22'),
(18, 90, 4, 3, '2023-11-27'),
(19, 85, 4, 1, '2024-01-12'),
(20, 95, 4, 2, '2024-02-24'),

(21, 88, 5, 1, '2023-09-18'),
(22, 92, 5, 2, '2023-10-25'),
(23, 75, 5, 3, '2023-11-29'),
(24, 78, 5, 1, '2024-01-15'),
(25, 85, 5, 2, '2024-03-01'),

(26, 70, 6, 1, '2023-09-20'),
(27, 95, 6, 2, '2023-10-30'),
(28, 80, 6, 3, '2023-12-01'),
(29, 90, 6, 1, '2024-01-17'),
(30, 85, 6, 2, '2024-03-05'),

(31, 83, 7, 1, '2023-09-22'),
(32, 76, 7, 2, '2023-10-02'),
(33, 89, 7, 3, '2023-11-05'),
(34, 91, 7, 1, '2024-01-22'),
(35, 74, 7, 2, '2024-03-10'),

(36, 93, 8, 1, '2023-09-24'),
(37, 80, 8, 2, '2023-10-04'),
(38, 78, 8, 3, '2023-11-07'),
(39, 85, 8, 1, '2024-01-24'),
(40, 91, 8, 2, '2024-03-12'),

(41, 88, 9, 1, '2023-09-26'),
(42, 95, 9, 2, '2023-10-06'),
(43, 80, 9, 3, '2023-11-09'),
(44, 92, 9, 1, '2024-01-26'),
(45, 77, 9, 2, '2024-03-14'),

(46, 79, 10, 1, '2023-09-28'),
(47, 86, 10, 2, '2023-10-08'),
(48, 83, 10, 3, '2023-11-11'),
(49, 81, 10, 1, '2024-01-28'),
(50, 93, 10, 2, '2024-03-16'),

(51, 77, 11, 1, '2023-10-01'),
(52, 79, 11, 2, '2023-10-10'),
(53, 90, 11, 3, '2023-11-13'),
(54, 82, 11, 1, '2024-02-01'),
(55, 84, 11, 2, '2024-03-18'),

(56, 91, 12, 1, '2023-10-03'),
(57, 87, 12, 2, '2023-10-12'),
(58, 79, 12, 3, '2023-11-15'),
(59, 92, 12, 1, '2024-02-03'),
(60, 75, 12, 2, '2024-03-20'),

(61, 85, 13, 1, '2023-10-05'),
(62, 80, 13, 2, '2023-10-14'),
(63, 87, 13, 3, '2023-11-17'),
(64, 79, 13, 1, '2024-02-05'),
(65, 91, 13, 2, '2024-03-22'),

(66, 84, 14, 1, '2023-10-07'),
(67, 90, 14, 2, '2023-10-16'),
(68, 77, 14, 3, '2023-11-19'),
(69, 82, 14, 1, '2024-02-07'),
(70, 75, 14, 2, '2024-03-24'),

(71, 79, 15, 1, '2023-10-09'),
(72, 88, 15, 2, '2023-10-18'),
(73, 93, 15, 3, '2023-11-21'),
(74, 86, 15, 1, '2024-02-09'),
(75, 80, 15, 2, '2024-03-26');

INSERT INTO spec_teacher (spec_id, teacher_id) VALUES
(1, 1), 
(1, 2), 
(1, 3), 
(2, 1),  
(2, 3); 


select * from  spec_teacher;
select * from ocenki;
select * from teachers;
select * from students;
select * from gruppy;
select * from spec;

CREATE TABLE login (
    id_user SERIAL PRIMARY KEY,
    id_student INT UNIQUE,
    login VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    CONSTRAINT fk_login_student FOREIGN KEY (id_student) REFERENCES students (id_student)
);


INSERT INTO login (id_student, login, password) VALUES
(1, 'shugaeva_anel', 'Anel2008'),
(2, 'kalieva_aidana', 'Aidana2007'),
(3, 'tekik_fatih', 'Fatih2008'),
(4, 'raimbekova_ayim', 'Aiym2008'),
(5, 'zhakupbekova_diana', 'Diana2007'),
(6, 'poperechniy_danila', 'Danil2024'),
(7, 'muzichenko_yuriy', 'Yuriy2024'),
(8, 'prusikin_ilya', 'Ilya2024'),
(9, 'gabidullin_ruslan', 'Ruslan2024'),
(10, 'kuplinov_dmitriy', 'Dmitriy2024'),
(11, 'pavel_viktor', 'Viktor2024'),
(12, 'volya_pavel', 'Pavel2024'),
(13, 'bykov_andrey', 'Andrey2024'),
(14, 'lobanov_semen', 'Semen2024'),
(15, 'saburov_nurlan', 'Nurlan2024');

select * from login

CREATE OR REPLACE FUNCTION update_login(
    p_id_student INT,
    o_login VARCHAR(50),
    o_password VARCHAR(255),
    n_login VARCHAR(50) DEFAULT NULL,
    n_password VARCHAR(255) DEFAULT NULL
)
RETURNS TEXT AS $$
DECLARE
    current_login VARCHAR(50);
    current_password VARCHAR(255);
BEGIN
    
    SELECT login, password
    INTO current_login, current_password
    FROM login
    WHERE id_student = p_id_student;

    
    IF current_login != o_login OR current_password != o_password THEN
        RAISE EXCEPTION 'Неверный текущий логин или пароль';
    END IF;

    
    IF n_login IS NULL AND n_password IS NULL THEN
        RAISE EXCEPTION 'Необходимо указать новый логин или новый пароль';
    END IF;

    
    IF n_login IS NOT NULL THEN
        UPDATE login
        SET login = p_new_login
        WHERE id_student = p_id_student;
    END IF;

    
    IF n_password IS NOT NULL THEN
        UPDATE login
        SET password = n_password
        WHERE id_student = p_id_student;
    END IF;

    RETURN 'Логин и/или пароль успешно обновлены';
END;
$$ LANGUAGE plpgsql;


SELECT update_login(
    1, 
    'shugaeva_anel', 
    'Anel2008', 
    NULL, 
    'New2008'
);

insert into teachers(id_teacher, fio_teacher, iin, nazvanie_predmeta) values
(4, 'Жолдықараева Еркеайым Бағланқызы', '972345678912', ' Составление алгоритма и создание блок схемы на основе спецификации программного обеспечения');

create table teacher_login(
	teacher_login_id serial primary key,
	id_teacher int not null unique,
	login VARCHAR(100),
	password VARCHAR(100),
	foreign key (id_teacher) references teachers(id_teacher)
);

insert into teacher_login(teacher_login_id, id_teacher, login, password) values
(1, 1, 'ahmadieva_arai', 'arai88'),
(2, 2, 'shapiggulin_bekdaulet', 'plake_plake1'),
(3, 3, 'muzdanov_bayirzhan', 'muzdanov_boba1101'),
(4, 4, 'zholdyrkaeva_erkeaiym', 'erke23_32');

select * from teacher_login;

create table user_roles(
	id_role serial primary key,
	id_student int,
	id_teacher int,
	role_name VARCHAR(30),
	foreign key (id_student) references login(id_student),
	foreign key (id_teacher) references teacher_login(id_teacher)
);

insert into user_roles(id_role, id_student, id_teacher, role_name) values
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
(16, null, 1, 'teacher'),
(17, null, 2, 'teacher'),
(18, null, 3, 'teacher'),
(19, null, 4, 'teacher');

select * from user_roles;


