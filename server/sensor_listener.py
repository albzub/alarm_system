import socket, json, threading, random, time
from datetime import datetime
from db import log_alarm

DEVICE_IDS = ["A1", "A2", "A3", "A4", "A5", "A6"]

def handle_sensor_connection(conn, addr, broadcast_callback):
    """실제 장비로부터 TCP 신호 수신"""
    try:
        data = conn.recv(1024)
        if not data:
            return
        event = json.loads(data.decode())

        if all(k in event for k in ("sensor_id", "status")):
            dev = event["sensor_id"]
            status = event["status"]
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            log_alarm(dev, now, status)
            event["time"] = now
            broadcast_callback(event)
            print(f"[→] Broadcasted {dev} = {status}")
        else:
            print("[WARN] Invalid event:", event)
    except Exception as e:
        print(f"[Error handling sensor TCP] {e}")
    finally:
        conn.close()

def tcp_listener(broadcast_callback):
    HOST = "0.0.0.0"
    PORT = 6000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"📡 Sensor listener started at {HOST}:{PORT}")

    while True:
        conn, addr = s.accept()
        threading.Thread(
            target=handle_sensor_connection, args=(conn, addr, broadcast_callback), daemon=True
        ).start()

def simulate_sensors(broadcast_callback):
    """시뮬레이터 (테스트용)"""
    while True:
        time.sleep(random.randint(8, 15))
        dev = random.choice(DEVICE_IDS)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_alarm(dev, now, "ALARM")
        broadcast_callback({"sensor_id": dev, "status": "ALARM", "time": now})
        print(f"[!] {dev} ALARM triggered")

        time.sleep(random.randint(5, 10))
        now2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_alarm(dev, now2, "OK")
        broadcast_callback({"sensor_id": dev, "status": "OK", "time": now2})
        print(f"[✓] {dev} cleared")

def start_listener(broadcast_callback):
    threading.Thread(target=tcp_listener, args=(broadcast_callback,), daemon=True).start()
    # threading.Thread(target=simulate_sensors, args=(broadcast_callback,), daemon=True).start()
