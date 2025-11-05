# signal_sender.py
import socket
import time
import json
from datetime import datetime

HOST = "172.16.1.160"  # 서버(경보기용장치) IP
PORT = 6000            # 센서신호 수신용 포트 (listener용)

def send_signal(sensor_id, status):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        event = {
            "sensor_id": sensor_id,
            "time": datetime.now().strftime("%m/%d/%y %H:%M"),
            "status": status
        }
        s.sendall(json.dumps(event).encode())
        s.close()
        print(f"[Sent] {sensor_id} → {status}")
    except Exception as e:
        print(f"[Error] {e}")

if __name__ == "__main__":
    while True:
        # A1 → ALARM → OK 반복
        send_signal("A1", "ALARM")
        time.sleep(10)
        send_signal("A1", "OK")
        time.sleep(10)

        send_signal("A2", "ALARM")
        time.sleep(10)
        send_signal("A2", "OK")
        time.sleep(10)

        send_signal("A3", "ALARM")
        time.sleep(10)
        send_signal("A3", "OK")
        time.sleep(10)

        send_signal("A4", "ALARM")
        time.sleep(10)
        send_signal("A4", "OK")
        time.sleep(10)

        send_signal("A5", "ALARM")
        time.sleep(10)
        send_signal("A5", "OK")
        time.sleep(10)

        send_signal("A6", "ALARM")
        time.sleep(10)
        send_signal("A6", "OK")
        time.sleep(10)

