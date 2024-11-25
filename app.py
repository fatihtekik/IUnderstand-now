from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)



def get_db_connection():
    connection = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="Aidana2007",
        port="5000"
    )
    return connection
@app.route('/api/data', methods=['GET'])
def get_data():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM your_table')  # Замените на ваш запрос
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(rows)


if __name__ == '__main__':
    app.run(debug=True)
