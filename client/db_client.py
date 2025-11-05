import sqlite3

DB_FILE = "client_data.db"

def init_local_db():
    """클라이언트 로컬 DB 초기화"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alarm_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device TEXT NOT NULL,
        time_on TEXT,
        time_off TEXT,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

def insert_alarm(device, time_on, status):
    """새로운 알람 발생 기록 추가"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO alarm_logs (device, time_on, status)
        VALUES (?, ?, ?)
    """, (device, time_on, status))
    conn.commit()
    conn.close()

def update_alarm(device, time_off, status):
    """알람 해제 시 마지막 기록 갱신"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        UPDATE alarm_logs
        SET time_off = ?, status = ?
        WHERE device = ? AND time_off IS NULL
    """, (time_off, status, device))
    conn.commit()
    conn.close()
