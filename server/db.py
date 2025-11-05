import sqlite3, bcrypt, re

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
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
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

def valid_password(password: str):
    if not password or len(password) < 6:
        return False, "암호는 최소 6자이상이여야 합니다."
    return True, ""

# ----------------------------
# ✅ Add user
# ----------------------------
def add_user(username, password):
    if not username or not username.strip():
        return False, "사용자이름을 입력하십시오."

    ok, msg = valid_password(password)
    if not ok:
        return False, msg

    try:
        conn = get_conn()
        cur = conn.cursor()
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed))
        conn.commit()
        return True, "✅ 사용자등록이 성공하였습니다."
    except sqlite3.IntegrityError:
        return False, "❌ 이미 존재하는 사용자입니다."
    except Exception as e:
        return False, f"❌ 자료기지 오유: {e}"
    finally:
        try:
            conn.close()
        except:
            pass

# ----------------------------
# ✅ Check Log in
# ----------------------------
def check_user_credentials(username, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return False, "❌ Cannot find user."

    stored_hash = row[0]
    if bcrypt.checkpw(password.encode(), stored_hash.encode()):
        return True, "✅ Login successfully"
    return False, "❌ Incorrect Password."

def activate_user(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_active=1 WHERE username=?", (username,))
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated

def deactivate_user(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_active=0 WHERE username=?", (username,))
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated

def change_user_password(username: str, old_pw: str, new_pw: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return False, "Cannot find user."

    stored_hash = row[0]
    if not bcrypt.checkpw(old_pw.encode(), stored_hash.encode()):
        conn.close()
        return False, "Incorrect old password."

    ok, msg = valid_password(new_pw)
    if not ok:
        conn.close()
        return False, msg

    new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
    cur.execute("UPDATE users SET password_hash=? WHERE username=?", (new_hash, username))
    conn.commit()
    conn.close()
    return True, "Password changed successfully."

def get_active_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE is_active=1")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def deactivate_account(username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_active=0 WHERE username=?", (username,))
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    if updated:
        return True, "사용자정보가 비활성화되였습니다."
    else:
        return False, "사용자가 존재하지 않습니다."