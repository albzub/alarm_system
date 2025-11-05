import customtkinter as ctk
import pygame
from socket_client import SocketClient
from PIL import Image, ImageTk
from datetime import datetime

HOST = "172.16.1.160"   # server IP
PORT = 5000

DEVICES = {
    "A1": (80, 100), "A2": (200, 150),
    "A3": (350, 180), "A4": (500, 100),
    "A5": (250, 300), "A6": (450, 280)
}

class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, username):
        super().__init__(master)
        self.master = master
        self.username = username
        self.pack(fill="both", expand=True)

        # === Sound Setup ===
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound("assets/alarm.wav")
        self.sound_playing = False

        # === UI Header ===
        ctk.CTkLabel(self, text=f"👤 {username}", font=("Arial", 14)).pack(anchor="ne", padx=15, pady=5)

        # === Canvas + Map ===
        self.canvas = ctk.CTkCanvas(self, width=900, height=500, bg="white", highlightthickness=0)
        self.canvas.pack(pady=20)

        self.bg_img_raw = Image.open("assets/map.png").resize((900, 500))
        self.map_img = ImageTk.PhotoImage(self.bg_img_raw)
        self.map_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.map_img)
        self.canvas.image_ref = self.map_img  # keep ref

        # === Markers (Green default) ===
        self.markers = {}
        for d, (x, y) in DEVICES.items():
            self.markers[d] = self.canvas.create_oval(x, y, x+40, y+40, fill="green")
            self.canvas.create_text(x+20, y-10, text=d)

        # === Buttons ===
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="📋 View Alarm List", command=self.open_list).pack(side="left", padx=10)

        # === Socket client ===
        self.client = SocketClient(HOST, PORT, self.update_alarm)
        self.client.start()


    # -------------------------------
    # 🔔 Alarm update handler
    # -------------------------------
    def update_alarm(self, event):
        """서버에서 받은 알람 이벤트를 UI에 반영"""
        d = event.get("sensor_id") or event.get("device")
        s = event.get("status", "").upper()

        # 내부 함수로 감싸서 Tkinter 메인 스레드에서 실행
        def update_ui():
            # 1️⃣ 지도 마커 색상 변경
            if d in self.markers:
                color = "red" if s == "ALARM" else "green"
                self.canvas.itemconfig(self.markers[d], fill=color)
                print(f"[UI] {d} marker color changed to {color}")

            # 2️⃣ 소리 재생 제어
            if s == "ALARM" and not self.sound_playing:
                self.sound.play(-1)
                self.sound_playing = True
                print("[SOUND] Alarm started")
            elif s == "OK" and self.sound_playing:
                self.sound.stop()
                self.sound_playing = False
                print("[SOUND] Alarm stopped")

        # Tkinter UI 갱신은 메인 스레드에서만 실행 가능
        self.after(0, update_ui)


    # -------------------------------
    # 📋 Open alarm list page
    # -------------------------------
    def open_list(self):
        self.master.show_alarm_list()
