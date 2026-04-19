from db import get_db_connection

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            pattern_hash TEXT NOT NULL,
            failed_attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            registration_time REAL,
            login_time REAL,
            graphical_attempts INTEGER,
            recall_attempts INTEGER,
            recall_time REAL,
            otp_attempts INTEGER,
            otp_time REAL,
            total_auth_time REAL,
            login_success INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialised successfully.")


if __name__ == "__main__":
    init_db()
