from flask import Flask, Response, request
from flask_cors import CORS
import psycopg2
import json
from datetime import date, datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

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
    """Преобразует объекты типа date или datetime в строковый формат"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()  # Преобразуем дату или datetime в строку
    raise TypeError(f"Type {type(obj)} not serializable")

@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Flask API. Use /api/data to access the data."

@app.route('/api/login', methods=['POST'])
def login():
    """Endpoint для авторизации пользователей."""
    try:
        data = request.get_json()
        login = data.get('login')
        password = data.get('password')

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            'SELECT id_user, id_student FROM login WHERE login = %s AND password = %s',
            (login, password)
        )
        user = cursor.fetchone()

        if not user:
            return Response(json.dumps({"error": "Неверный логин или пароль"}), status=401, mimetype='application/json')

        return Response(json.dumps({"id_user": user[0], "id_student": user[1]}), mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')

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
                teachers.FIO_teacher, 
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

if __name__ == '__main__':
    app.run(debug=True)
