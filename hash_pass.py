import bcrypt
import psycopg2 as psycopg
import logging

# Настройка логирования
logging.basicConfig(
    filename='hash_passwords.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def connect_to_db():
    try:
        conn = psycopg.connect(
            dbname="postgres",
            user="postgres",
            password="Aidana2007",
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return None

def hash_existing_passwords():
    conn = connect_to_db()
    if not conn:
        logger.error("Не удалось подключиться к базе данных.")
        return
    try:
        cursor = conn.cursor()

        # Хэширование паролей студентов
        cursor.execute("SELECT id_user, password FROM login")
        users = cursor.fetchall()
        for user in users:
            id_user, plain_password = user
            if plain_password.startswith("$2b$") or plain_password.startswith("$2a$") or plain_password.startswith("$2y$"):
                # Пароль уже захэширован
                continue
            hashed = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE login SET password = %s WHERE id_user = %s", (hashed.decode('utf-8'), id_user))
            logger.info(f"Пароль для студента ID {id_user} успешно захэширован.")

        # Хэширование паролей преподавателей
        cursor.execute("SELECT teacher_login_id, password FROM teacher_login")
        teachers = cursor.fetchall()
        for teacher in teachers:
            teacher_login_id, plain_password = teacher
            if plain_password.startswith("$2b$") or plain_password.startswith("$2a$") or plain_password.startswith("$2y$"):
                # Пароль уже захэширован
                continue
            hashed = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE teacher_login SET password = %s WHERE teacher_login_id = %s",
                           (hashed.decode('utf-8'), teacher_login_id))
            logger.info(f"Пароль для преподавателя ID {teacher_login_id} успешно захэширован.")

        conn.commit()
        logger.info("Все пароли успешно захэшированы.")
    except Exception as e:
        logger.error(f"Ошибка при хэшировании паролей: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    hash_existing_passwords()
