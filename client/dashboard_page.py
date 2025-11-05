import customtkinter as ctk
import pygame
from socket_client import SocketClient
from PIL import Image, ImageTk
from datetime import datetime
from tkinter import messagebox

HOST = "172.16.1.160"
PORT = 5000

DEVICES = {
    "A1": (80, 100), "A2": (200, 150),
    "A3": (350, 180), "A4": (500, 100),
    "A5": (250, 300), "A6": (450, 280),
    "A7": (650, 320), "A8": (750, 280),
}


class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, username, server):
        super().__init__(master)
        self.master = master
        self.username = username
        self.server = server
        self.pack(fill="both", expand=True)

        # ---------- SOUND ----------
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound("assets/alarm.wav")
        self.sound_playing = False

        # ---------- NAV ----------
        nav = ctk.CTkFrame(self, height=60, fg_color="#1E293B", corner_radius=0)
        nav.pack(fill="x", side="top")

        try:
            logo_img = Image.open("assets/log_bg.png").resize((40, 40))
            self.logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img)
            ctk.CTkLabel(nav, image=self.logo_ctk, text="").pack(side="left", padx=15)
        except:
            ctk.CTkLabel(nav, text="🔔", font=("Arial", 24)).pack(side="left", padx=15)

        ctk.CTkLabel(nav, text="Alarm Monitoring System",
                     font=("Arial", 20, "bold"), text_color="white").pack(side="left", padx=20)

        ctk.CTkButton(nav, text="📜 리력보기", fg_color="transparent",
                      text_color="white", hover_color="#334155",
                      command=self.open_list).pack(side="right", padx=10)

        # --- 메뉴에서 "⚙ 설정" 제거 ---
        self.user_menu = ctk.CTkOptionMenu(
            nav,
            values=["비밀번호 변경", "가입 탈퇴"],
            command=self.handle_user_action,
            fg_color="#334155", button_color="#334155", text_color="white"
        )
        self.user_menu.set(f"👤 {username}")
        self.user_menu.pack(side="right", padx=15, pady=10)

        # ---------- MAIN LAYOUT ----------
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=0, pady=10)

        main_frame.grid_rowconfigure(0, weight=17)
        main_frame.grid_rowconfigure(1, weight=3)
        main_frame.grid_columnconfigure(0, weight=1)

        # ---------- 지도 ----------
        map_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        map_frame.grid(row=0, column=0, sticky="nsew")

        self.canvas = ctk.CTkCanvas(map_frame, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.bg_img_raw = Image.open("assets/map.png")
        self.map_img = None
        self.canvas_image_id = None

        self.markers = {}
        for d, (x, y) in DEVICES.items():
            self.markers[d] = {"pos": (x, y), "id": None, "text": None}

        self.canvas.bind("<Configure>", self._resize_map)

        self.clock_text = None
        self.clock_bg_rect = None
        self.update_clock()

        # ---------- 하단 패널 ----------
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="#0f172a", corner_radius=10)
        bottom_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

        bottom_frame.grid_rowconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=7)
        bottom_frame.grid_columnconfigure(1, weight=3)

        # --- 장치 상태 ---
        devices_outer = ctk.CTkFrame(bottom_frame, fg_color="transparent", corner_radius=8)
        devices_outer.grid(row=0, column=0, padx=(15, 5), pady=8, sticky="nsew")

        title = ctk.CTkLabel(devices_outer, text="📡 장치 상태",
                             font=("Arial", 22, "bold"), text_color="#E2E8F0")
        title.pack(pady=(0, 8))

        border = ctk.CTkFrame(devices_outer, fg_color="transparent",
                              border_color="#64748b", border_width=2, corner_radius=10)
        border.pack(fill="both", expand=True, padx=10, pady=5)

        self.device_labels = {}
        inner = ctk.CTkFrame(border, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=10)

        cols = 3
        row, col = 0, 0
        for i, device in enumerate(DEVICES.keys()):
            lbl = ctk.CTkLabel(inner, text=f"{device} : 정상",
                               font=("Arial", 18, "bold"), text_color="#22c55e")
            lbl.grid(row=row, column=col, padx=35, pady=8, sticky="w")
            self.device_labels[device] = lbl

            col += 1
            if (i + 1) % cols == 0:
                row += 1
                col = 0

        # --- 연결 사용자 ---
        users_outer = ctk.CTkFrame(bottom_frame, fg_color="transparent", corner_radius=8)
        users_outer.grid(row=0, column=1, padx=(5, 15), pady=8, sticky="nsew")

        title = ctk.CTkLabel(users_outer, text="👥 연결 사용자",
                             font=("Arial", 22, "bold"), text_color="#E2E8F0")
        title.pack(pady=(0, 8))

        users_border = ctk.CTkFrame(users_outer, fg_color="transparent",
                                    border_color="#64748b", border_width=2, corner_radius=10)
        users_border.pack(fill="both", expand=True, padx=10, pady=5)

        self.users_inner = ctk.CTkFrame(users_border, fg_color="transparent")
        self.users_inner.pack(fill="both", expand=True, padx=10, pady=8)

        self.user_labels = {}
        self.add_user_label(self.username)

        # ---------- SOCKET ----------
        self.client = SocketClient(self.server, PORT, self.update_alarm)
        self.client.start()

    # -------------------------------
    # 🕒 시계 갱신
    # -------------------------------
    def update_clock(self):
        now = datetime.now().strftime("%Y/%m/%d, %H:%M:%S")
        if self.clock_text:
            self.canvas.itemconfig(self.clock_text, text=now)
        self.after(1000, self.update_clock)

    # -------------------------------
    # 지도 리사이즈 핸들러
    # -------------------------------
    def _resize_map(self, event):
        canvas_w, canvas_h = event.width, event.height

        resized = self.bg_img_raw.resize((canvas_w, canvas_h))
        self.map_img = ImageTk.PhotoImage(resized)

        if self.canvas_image_id:
            self.canvas.itemconfig(self.canvas_image_id, image=self.map_img)
        else:
            self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.map_img)

        for d, data in self.markers.items():
            orig_x, orig_y = data["pos"]
            x = orig_x / 900 * canvas_w
            y = orig_y / 500 * canvas_h

            if data["id"]:
                self.canvas.delete(data["id"])
            if data["text"]:
                self.canvas.delete(data["text"])

            data["id"] = self.canvas.create_oval(x, y, x + 40, y + 40, fill="#22c55e", outline="")
            data["text"] = self.canvas.create_text(x + 20, y - 10, text=d, fill="#1e293b",
                                                   font=("Arial", 14, "bold"))

        # 반투명 시계 카드
        center_x, center_y = canvas_w // 2, 35
        rect_w, rect_h = 300, 50

        if self.clock_bg_rect:
            self.canvas.delete(self.clock_bg_rect)
        if self.clock_text:
            self.canvas.delete(self.clock_text)

        self.clock_bg_rect = self.canvas.create_rectangle(
            center_x - rect_w // 2, center_y - rect_h // 2,
            center_x + rect_w // 2, center_y + rect_h // 2,
            fill="#000000", stipple="gray50", outline="#64748b", width=1
        )
        self.clock_text = self.canvas.create_text(
            center_x, center_y,
            text=datetime.now().strftime("%Y/%m/%d, %H:%M:%S"),
            fill="#f8fafc", font=("Arial", 20, "bold")
        )

    # -------------------------------
    # 🔔 알람 이벤트 처리
    # -------------------------------
    def update_alarm(self, event):
        d = event.get("sensor_id") or event.get("device")
        s = event.get("status", "").upper()

        def update_ui():
            if d in self.markers and self.markers[d]["id"]:
                color = "#ef4444" if s == "ALARM" else "#22c55e"
                self.canvas.itemconfig(self.markers[d]["id"], fill=color)

            if d in self.device_labels:
                if s == "ALARM":
                    self.device_labels[d].configure(text=f"{d} : 경보", text_color="#ef4444")
                elif s == "OK":
                    self.device_labels[d].configure(text=f"{d} : 정상", text_color="#22c55e")

            if s == "ALARM" and not self.sound_playing:
                self.sound.play(-1)
                self.sound_playing = True
            elif s == "OK" and self.sound_playing:
                self.sound.stop()
                self.sound_playing = False

        self.after(0, update_ui)

    # -------------------------------
    # 👥 사용자 추가
    # -------------------------------
    def add_user_label(self, username):
        if username in self.user_labels:
            return
        lbl = ctk.CTkLabel(self.users_inner, text=username,
                           font=("Arial", 18, "bold"), text_color="#f1f5f9")
        lbl.pack(pady=5)
        self.user_labels[username] = lbl

    # -------------------------------
    # 📋 리력보기
    # -------------------------------
    def open_list(self):
        self.master.show_alarm_list(self.username, self.server)

    # -------------------------------
    # ⚙ 사용자 메뉴 액션
    # -------------------------------
    def handle_user_action(self, choice):
        if choice == "비밀번호 변경":
            self.open_change_password()
        elif choice == "가입 탈퇴":
            self.confirm_unsubscribe()
        self.user_menu.set(f"👤 {self.username}")

    # -------------------------------
    # 🔐 비밀번호 변경창
    # -------------------------------
    def open_change_password(self):
        popup = ctk.CTkToplevel(self)
        popup.title("비밀번호 변경")
        popup.geometry("350x250")
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text="기존 비밀번호:", font=("Arial", 14)).pack(pady=(20, 5))
        old_pw = ctk.CTkEntry(popup, show="*")
        old_pw.pack(pady=5)

        ctk.CTkLabel(popup, text="새 비밀번호:", font=("Arial", 14)).pack(pady=(10, 5))
        new_pw = ctk.CTkEntry(popup, show="*")
        new_pw.pack(pady=5)

        def save_new_password():
            o, n = old_pw.get(), new_pw.get()
            if not o or not n:
                messagebox.showwarning("⚠️", "모든 항목을 입력하세요.")
                return
            # 실제 시스템에서는 DB에 업데이트하는 부분
            print(f"[USER] {self.username} → 비밀번호 변경 완료")
            messagebox.showinfo("✅", "비밀번호가 변경되었습니다.")
            popup.destroy()

        ctk.CTkButton(popup, text="변경", command=save_new_password).pack(pady=20)

    # -------------------------------
    # ❌ 가입 탈퇴
    # -------------------------------
    def confirm_unsubscribe(self):
        answer = messagebox.askyesno("가입 탈퇴", f"{self.username}님, 정말 탈퇴하시겠습니까?")
        if answer:
            print(f"[USER] {self.username} 탈퇴 처리 완료")
            messagebox.showinfo("완료", "탈퇴가 완료되었습니다.")
            self.master.show_login_page()
