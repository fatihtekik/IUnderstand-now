from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import psycopg2
import json
from datetime import date, datetime
def newSEmestr(year,semestr):
    print(f"{semestr} этого {year}")
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
newSEmestr(2024,1)
def get_db_connection():
    connection = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="Aidana2007",
        port="5432"
    )
    return connection

def json_serial(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Flask API. Use /api/data to access the data."

@app.route('/api/login', methods=['POST'])
def login():
    """Endpoint для авторизации пользователей с поддержкой ролей."""
    try:
        data = request.get_json()
        login = data.get('login')
        password = data.get('password')

        # Проверка наличия логина и пароля
        if not login or not password:
            return jsonify({"error": "Необходимо указать логин и пароль"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        # Сначала проверяем таблицу студентов
        cursor.execute(
            'SELECT id_user, id_student FROM login WHERE login = %s AND password = %s',
            (login, password)
        )
        student = cursor.fetchone()

        if student:
            id_user, id_student = student
            response_data = {
                "id_user": id_user,
                "id_student": id_student,
                "role": "student"
            }
            return Response(json.dumps(response_data), mimetype='application/json'), 200

        # Если не найдено среди студентов, проверяем таблицу преподавателей
        cursor.execute(
            'SELECT id_teacher FROM teacher_login WHERE login = %s AND password = %s',
            (login, password)
        )
        teacher = cursor.fetchone()

        if teacher:
            id_teacher = teacher[0]
            response_data = {
                "id_user": id_teacher,
                "role": "teacher"
            }
            return Response(json.dumps(response_data), mimetype='application/json'), 200

        # Если не найдено ни в одной таблице
        return Response(json.dumps({"error": "Неверный логин или пароль"}), status=401, mimetype='application/json')

    except Exception as e:
        # Логирование ошибки на сервере (можно расширить для полноценного логирования)
        print(f"Ошибка при авторизации: {e}")
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass

@app.route('/api/data', methods=['GET'])
def get_data():
    """Endpoint для получения данных об оценках."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''
            SELECT 
                ocenki.id_ocenki, 
                ocenki.ocenka, 
                students.FIO, 
                teachers.nazvanie_predmeta, 
                ocenki.date 
            FROM ocenki 
            JOIN students ON students.id_student = ocenki.id_student 
            JOIN teachers ON teachers.id_teacher = ocenki.id_teacher 
            ORDER BY date
        ''')
        rows = cursor.fetchall()

        column_names = [desc[0] for desc in cursor.description]

        result = []
        for row in rows:
            row_dict = {column_names[i]: row[i] for i in range(len(row))}
            result.append(row_dict)

        cursor.close()
        connection.close()
        return Response(json.dumps(result, default=json_serial), mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')


@app.route('/api/dataById', methods=['GET'])
def get_data_by_id():
    try:
        # Получаем id студента из запроса (например, через параметр ?id_student=1)
        id_student = request.args.get('id_student')

        if not id_student:
            return Response(json.dumps({"error": "Не указан id студента"}), status=400, mimetype='application/json')

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute('''
            SELECT 
                ocenki.id_ocenki, 
                ocenki.ocenka, 
                students.FIO, 
                teachers.nazvanie_predmeta, 
                ocenki.date 
            FROM ocenki 
            JOIN students ON students.id_student = ocenki.id_student 
            JOIN teachers ON teachers.id_teacher = ocenki.id_teacher 
            WHERE students.id_student = %s 
            ORDER BY ocenki.date
        ''', (id_student,))

        rows = cursor.fetchall()


        column_names = [desc[0] for desc in cursor.description]
        result = [{column_names[i]: row[i] for i in range(len(row))} for row in rows]


        cursor.close()
        connection.close()

        return Response(json.dumps(result, default=json_serial), mimetype='application/json')
    finally:
        print("hello")


@app.route('/api/studentWithGroup', methods=['GET'])
def get_student_with_group():
    student_id = request.args.get('id_student')
    if not student_id:
        return jsonify({"error": "ID студента не указан"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''
            SELECT 
                s.FIO AS "fio",
                s.IIN AS "iin",
                g.nazvanie_gruppy AS "group"
            FROM 
                students s
            JOIN 
                gruppy g
            ON 
                s.id_gruppy = g.id_gruppy
            WHERE 
                s.id_student = %s;
        ''', (student_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            column_names = ["fio", "iin", "group"]
            return jsonify(dict(zip(column_names, result)))
        else:
            return jsonify({"error": "Студент не найден"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/grades', methods=['GET'])
def get_all_grades():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''
            SELECT 
                ocenki.id_ocenki, 
                ocenki.ocenka, 
                students.FIO AS student_fio, 
                teachers.nazvanie_predmeta, 
                ocenki.date 
            FROM ocenki 
            JOIN students ON students.id_student = ocenki.id_student 
            JOIN teachers ON teachers.id_teacher = ocenki.id_teacher 
            ORDER BY ocenki.date DESC
        ''')
        rows = cursor.fetchall()

        column_names = [desc[0] for desc in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]

        cursor.close()
        connection.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/grades/<int:id_ocenki>', methods=['PUT'])
def edit_grade(id_ocenki):
    try:
        data = request.get_json()
        new_grade = data.get('ocenka')

        if new_grade is None:
            return jsonify({"error": "Отсутствует поле 'ocenka'"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        # Обновление оценки
        cursor.execute(
            "UPDATE ocenki SET ocenka = %s WHERE id_ocenki = %s RETURNING id_ocenki, ocenka, id_student, id_teacher, date",
            (new_grade, id_ocenki)
        )
        updated_grade = cursor.fetchone()

        if not updated_grade:
            cursor.close()
            connection.close()
            return jsonify({"error": "Оценка не найдена"}), 404

        connection.commit()

        # Получение полной информации об обновлённой оценке
        cursor.execute('''
            SELECT 
                ocenki.id_ocenki, 
                ocenki.ocenka, 
                students.FIO AS student_fio, 
                teachers.nazvanie_predmeta, 
                ocenki.date 
            FROM ocenki 
            JOIN students ON students.id_student = ocenki.id_student 
            JOIN teachers ON teachers.id_teacher = ocenki.id_teacher 
            WHERE ocenki.id_ocenki = %s
        ''', (id_ocenki,))
        full_grade = cursor.fetchone()

        cursor.close()
        connection.close()

        column_names = [desc[0] for desc in cursor.description]
        grade_dict = dict(zip(column_names, full_grade))

        return jsonify(grade_dict), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Эндпоинт для удаления оценки
@app.route('/api/grades/<int:id_ocenki>', methods=['DELETE'])
def delete_grade(id_ocenki):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM ocenki WHERE id_ocenki = %s RETURNING *", (id_ocenki,))
        deleted_grade = cursor.fetchone()

        if not deleted_grade:
            cursor.close()
            connection.close()
            return jsonify({"error": "Оценка не найдена"}), 404

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"message": "Оценка удалена"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

