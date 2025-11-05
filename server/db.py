import sqlite3

def get_conn():
    return sqlite3.connect("server_data.db")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alarms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        on_time TEXT,
        off_time TEXT,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

def log_alarm(device_id, time, status):
    conn = get_conn()
    cur = conn.cursor()
    if status == "ALARM":
        cur.execute(
            "INSERT INTO alarms (device_id, on_time, status) VALUES (?, ?, ?)",
            (device_id, time, status)
        )
    elif status == "OK":
        cur.execute(
            "UPDATE alarms SET off_time=?, status='OK' WHERE device_id=? AND status='ALARM'",
            (time, device_id)
        )
    conn.commit()
    conn.close()

def get_alarm_logs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT device_id, on_time, off_time, status FROM alarms ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [{
        "device": r[0],
        "on_time": r[1],
        "off_time": r[2],
        "status": r[3]
    } for r in rows]
