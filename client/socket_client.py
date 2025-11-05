import socket, json, threading, time

class SocketClient:
    def __init__(self, host, port, callback):
        self.host = host
        self.port = port
        self.callback = callback
        self.running = True

    def start(self):
        threading.Thread(target=self.connect_loop, daemon=True).start()

    def connect_loop(self):
        buffer = ""
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, self.port))
                print(f"[Connected] {self.host}:{self.port}")

                while self.running:
                    chunk = s.recv(4096)
                    if not chunk:
                        raise ConnectionError

                    buffer += chunk.decode()

                    # 🔹 서버가 '\n' 단위로 보냄
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                            print("[DEBUG] Event received:", event)
                            if "sensor_id" in event or "device" in event:
                                self.callback(event)
                        except json.JSONDecodeError as e:
                            print("[WARN] JSON decode error:", e, "line:", line)

            except Exception as e:
                print(f"[Reconnect in 5s] {e}")
                time.sleep(5)
