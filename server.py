from flask import Flask, Response
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

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT ocenki.id_ocenki, ocenki.ocenka, students.FIO, teachers.FIO_teacher, ocenki.date FROM ocenki join students on students.id_student= ocenki.id_student join teachers on teachers.id_teacher=ocenki.id_teacher ORDER BY date')
        rows = cursor.fetchall()


        column_names = []
        for desc in cursor.description:
            column_names.append(desc[0])

        result = []
        for row in rows:
            row_dict = {}
            for i in range(len(row)):
                row_dict[column_names[i]] = row[i]
            result.append(row_dict)

        cursor.close()
        connection.close()
        return Response(json.dumps(result, default=json_serial), mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True)
