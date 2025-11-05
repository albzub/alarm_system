import socket, threading, json, time
from db import init_db, get_alarm_logs, check_user_credentials, add_user
from sensor_listener import start_listener

clients = []
clients_lock = threading.Lock()
unsent_events = []

def broadcast(event):
    """모든 클라이언트에게 이벤트 전송 (개행 포함)"""
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
            print("[🔁] Resending missed events...")
            for e in unsent_events[:]:
                broadcast(e)
                unsent_events.remove(e)

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

            # ✅ 회원가입 처리
            if cmd == "REGISTER":
                user, pw = msg.get("username"), msg.get("password")
                success = add_user(user, pw)
                response = {"type": "REGISTER_RESULT", "success": success}
                conn.send(json.dumps(response).encode())

            # ✅ 로그인 처리
            elif cmd == "LOGIN":
                user, pw = msg.get("username"), msg.get("password")
                success = check_user_credentials(user, pw)
                response = {"type": "LOGIN_RESULT", "success": success}
                conn.send(json.dumps(response).encode())

            # ✅ 로그 요청
            elif cmd == "GET_LOGS":
                logs = get_alarm_logs()
                conn.send(json.dumps({"type": "LOGS", "data": logs}).encode())

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
