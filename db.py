import sqlite3
import os


DB_PATH = os.path.join("data", "app.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_auth_metrics(data):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO auth_metrics (
            user_id,
            registration_time,
            login_time,
            graphical_attempts,
            incorrect_images,
            recall_attempts,
            recall_time,
            otp_attempts,
            otp_time,
            total_auth_time,
            login_success
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("user_id"),
        data.get("registration_time"),
        data.get("login_time"),
        data.get("graphical_attempts"),
        data.get("incorrect_images", 0),
        data.get("recall_attempts", 0),
        data.get("recall_time"),
        data.get("otp_attempts", 0),
        data.get("otp_time"),
        data.get("total_auth_time"),
        data.get("login_success")
    ))

    conn.commit()
    conn.close()