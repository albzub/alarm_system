import customtkinter as ctk
import json, socket

HOST = "172.16.1.160"
PORT = 5000

class AlarmListPage(ctk.CTkFrame):
    def __init__(self, master, username, server):
        super().__init__(master)
        self.master = master
        self.username = username
        self.server = server
        
        ctk.CTkLabel(self, text="📋 Alarm History", font=("Arial", 18, "bold")).pack(pady=10)
        self.table = ctk.CTkTextbox(self, width=700, height=400)
        self.table.pack(pady=10)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="🔄 Refresh", command=self.load_data).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="⬅ Back", command=self.go_back).pack(side="left", padx=10)

        self.load_data()

    def go_back(self):
        self.master.show_dashboard(self.username, self.server)

    def load_data(self):
        """서버로부터 로그를 요청하고 테이블에 표시"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            s.send(json.dumps({"command": "GET_LOGS"}).encode())

            raw = b""
            s.settimeout(2)
            while True:
                try:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    raw += chunk
                except socket.timeout:
                    break
            s.close()

            # ✅ 여러 JSON 덩어리가 와도 첫 번째만 처리
            text = raw.decode(errors="ignore")
            first_json = text.split("}{")[0] + "}" if "}{" in text else text.strip()
            response = json.loads(first_json)

            if response.get("type") == "LOGS":
                self.display_logs(response["data"])

        except Exception as e:
            self.table.delete("1.0", "end")
            self.table.insert("end", f"❌ Error: {e}\n")

        self.after(5000, self.load_data)

    def display_logs(self, logs):
        self.table.delete("1.0", "end")
        self.table.insert("end", f"{'Device':<10}{'Time On':<22}{'Time Off':<22}{'Status':<10}\n")
        self.table.insert("end", "-" * 70 + "\n")

        for row in logs:
            device = str(row.get("device") or row.get("sensor_id") or "")
            time_on = str(row.get("on_time") or "")
            time_off = str(row.get("off_time") or "")
            status = str(row.get("status") or "")
            status_icon = "🟥 ALARM" if status.upper() == "ALARM" else "🟩 OK"
            self.table.insert("end", f"{device:<10}{time_on:<22}{time_off:<22}{status_icon:<10}\n")
