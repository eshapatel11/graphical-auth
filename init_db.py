from db import get_db_connection

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt TEXT,
            pattern_hash TEXT NOT NULL,
            totp_secret TEXT,
            last_ip TEXT,
            last_browser TEXT,
            failed_attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Login events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip TEXT,
            browser TEXT,
            risk_score INTEGER,
            otp_required INTEGER,
            success INTEGER,
            mode TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            registration_time REAL,
            login_time REAL,
            graphical_attempts INTEGER,
            incorrect_images INTEGER,
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
