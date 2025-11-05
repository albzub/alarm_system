import socket, threading, json, time
from db import init_db, get_alarm_logs, check_user_credentials, add_user, deactivate_user, change_user_password, activate_user
from sensor_listener import start_listener
import bcrypt

clients = []
clients_lock = threading.Lock()
unsent_events = []

def broadcast(event):
    msg = (json.dumps(event) + "\n").encode()
    disconnected = []
    with clients_lock:
        for c in clients:
            try:
                c.send(msg)
            except:
                disconnected.append(c)
        for d in disconnected:
            clients.remove(d)
    if not clients:
        unsent_events.append(event)

def resend_unsent():
    while True:
        time.sleep(10)
        if unsent_events and clients:
            print("[🔁] There are unsent events, but they won't be resent to new users.")
            # ❌ 기존처럼 실제로 재전송하지 않음
            # 단순히 남아있는 리스트는 1분 단위로 정리만
            if len(unsent_events) > 50:
                unsent_events.clear()

def client_handler(conn, addr):
    print(f"[+] Client {addr} connected")
    with clients_lock:
        clients.append(conn)
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            msg = json.loads(data.decode())
            cmd = msg.get("command")

            if cmd == "REGISTER":
                user, pw = msg.get("username"), msg.get("password")
                success, message = add_user(user, pw)
                conn.send(json.dumps({"type": "REGISTER_RESULT", "success": success, "message": message}).encode())
                break

            elif cmd == "LOGIN":
                user, pw = msg.get("username"), msg.get("password")
                success, message = check_user_credentials(user, pw)
                if success:
                    activate_user(user)
                    if unsent_events:
                        notice = {
                            "type": "NOTICE",
                            "message": f"로그인 이전에 발생한 {len(unsent_events)}건의 알람을 확인하지 못했습니다."
                        }
                        conn.send(json.dumps(notice).encode())
                conn.send(json.dumps({"type": "LOGIN_RESULT", "success": success, "message": message}).encode())
                break
            
            elif cmd == "GET_ACTIVE_USERS":
                from db import get_active_users
                users = get_active_users()
                conn.send(json.dumps({
                    "type": "ACTIVE_USERS",
                    "users": users
                }).encode())
                break

            elif cmd == "LOGOUT":
                user = msg.get("username")
                success = deactivate_user(user)
                conn.send(json.dumps({
                    "type": "LOGOUT_RESULT",
                    "success": success,
                    "message": f"Logout succcessfully." if success else "Cannot find user."
                }).encode())
                break

            elif cmd == "GET_LOGS":
                logs = get_alarm_logs()
                conn.send(json.dumps({"type": "LOGS", "data": logs}).encode())
                break
            
            elif cmd == "CHANGE_PASSWORD":
                user = msg.get("username")
                old_pw = msg.get("old_pw")
                new_pw = msg.get("new_pw")
                success, message = change_user_password(user, old_pw, new_pw)
                conn.send(json.dumps({
                    "type": "CHANGE_PASSWORD_RESULT",
                    "success": success,
                    "message": message
                }).encode())
                break

    except Exception as e:
        print(f"[!] Client error {addr}: {e}")
    finally:
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()
        print(f"[-] Client {addr} disconnected")


def start_server(host="0.0.0.0", port=5000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen()
    print(f"🚀 Server started at {host}:{port}")
    threading.Thread(target=resend_unsent, daemon=True).start()
    threading.Thread(target=start_listener, args=(broadcast,), daemon=True).start()

    while True:
        conn, addr = s.accept()
        threading.Thread(target=client_handler, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    init_db()
    start_server()
