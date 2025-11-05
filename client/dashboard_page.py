import customtkinter as ctk
import pygame

from socket_client import SocketClient
from PIL import Image, ImageTk
from datetime import datetime
from tkinter import messagebox
import socket, json

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
        nav = ctk.CTkFrame(self, height=100, fg_color="#1E293B", corner_radius=0)
        nav.pack(fill="x", side="top")

        try:
            logo_img = Image.open("assets/logo.png").resize((80, 40))
            self.logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img)
            ctk.CTkLabel(nav, image=self.logo_ctk, text="").pack(side="left", padx=15)
        except:
            ctk.CTkLabel(nav, text="🔔", font=("Arial", 24)).pack(side="left", padx=15)

        ctk.CTkLabel(nav, text="Alarm Monitoring System",
                     font=("Arial", 20, "bold"), text_color="white").pack(side="left", padx=20)

        ctk.CTkButton(nav, text="📜 Alarm List", fg_color="transparent",
                      text_color="white", hover_color="#334155",
                      command=self.open_list).pack(side="right", padx=10)

        self.user_menu = ctk.CTkOptionMenu(
            nav,
            values=["Change Password", "Log out"],
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

        # ---------- Map ----------
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

        bottom_frame = ctk.CTkFrame(main_frame, fg_color="#0f172a", corner_radius=10)
        bottom_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

        bottom_frame.grid_rowconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=7)
        bottom_frame.grid_columnconfigure(1, weight=3)

        devices_outer = ctk.CTkFrame(bottom_frame, fg_color="transparent", corner_radius=8)
        devices_outer.grid(row=0, column=0, padx=(15, 5), pady=8, sticky="nsew")

        title = ctk.CTkLabel(devices_outer, text="📡 Device Status",
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
            lbl = ctk.CTkLabel(inner, text=f"{device} : OK",
                               font=("Arial", 18, "bold"), text_color="#22c55e")
            lbl.grid(row=row, column=col, padx=35, pady=8, sticky="w")
            self.device_labels[device] = lbl

            col += 1
            if (i + 1) % cols == 0:
                row += 1
                col = 0

        users_outer = ctk.CTkFrame(bottom_frame, fg_color="transparent", corner_radius=8)
        users_outer.grid(row=0, column=1, padx=(5, 15), pady=8, sticky="nsew")

        title = ctk.CTkLabel(users_outer, text="👥 Connected Users",
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
    # 🕒 Clock
    # -------------------------------
    def update_clock(self):
        now = datetime.now().strftime("%Y/%m/%d, %H:%M:%S")
        if self.clock_text:
            self.canvas.itemconfig(self.clock_text, text=now)
        self.after(1000, self.update_clock)

    # -------------------------------
    # Resize the map
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

        # Background of clock
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
    # 🔔 Event of alarm
    # -------------------------------
    def update_alarm(self, event):
        d = event.get("sensor_id") or event.get("device")
        s = event.get("status", "").upper()

        def update_ui():
            if d in self.markers and self.markers[d]["id"]:
                color = "#ef4444" if s == "ALARM" else "#22c55e"
                self.canvas.itemconfig(self.markers[d]["id"], fill=color)

            etype = event.get("type")
            if etype == "NOTICE":
                from tkinter import messagebox
                messagebox.showinfo("알림", event.get("message"))
                return
            
            if d in self.device_labels:
                if s == "ALARM":
                    self.device_labels[d].configure(text=f"{d} : ALARM", text_color="#ef4444")
                elif s == "OK":
                    self.device_labels[d].configure(text=f"{d} : OK", text_color="#22c55e")

            if s == "ALARM" and not self.sound_playing:
                self.sound.play(-1)
                self.sound_playing = True
            elif s == "OK" and self.sound_playing:
                self.sound.stop()
                self.sound_playing = False

        self.after(0, update_ui)

    # -------------------------------
    # 👥 Add Username on nav
    # -------------------------------
    def add_user_label(self, username):
        if username in self.user_labels:
            return
        lbl = ctk.CTkLabel(self.users_inner, text=username,
                           font=("Arial", 18, "bold"), text_color="#f1f5f9")
        lbl.pack(pady=5)
        self.user_labels[username] = lbl

    # -------------------------------
    # 📋 Show alarm list
    # -------------------------------
    def open_list(self):
        self.master.show_alarm_list(self.username, self.server)

    # -------------------------------
    # ⚙ User menu actions
    # -------------------------------
    def handle_user_action(self, choice):
        if choice == "Change Password":
            self.open_change_password()
        elif choice == "Log out":
            self.confirm_unsubscribe()
        self.user_menu.set(f"👤 {self.username}")

    def update_active_users(self):
        """서버에서 활성 사용자 목록을 가져와 표시"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server, PORT))
            s.send(json.dumps({"command": "GET_ACTIVE_USERS"}).encode())
            data = json.loads(s.recv(4096).decode())
            s.close()

            if data.get("type") == "ACTIVE_USERS":
                active_users = data.get("users", [])
                self.refresh_user_labels(active_users)

        except Exception as e:
            print(f"[!] Active user fetch failed: {e}")

        # 5초마다 반복
        self.after(5000, self.update_active_users)

    # -------------------------------
    # 🔐 change pwd
    # -------------------------------
    def open_change_password(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Chage Password")
        popup.geometry("350x250")
        popup.resizable(False, False)
        popup.lift()
        popup.focus_force()
        popup.grab_set()

        ctk.CTkLabel(popup, text="Old Password:", font=("Arial", 14)).pack(pady=(20, 5))
        old_pw = ctk.CTkEntry(popup, show="*")
        old_pw.pack(pady=5)

        ctk.CTkLabel(popup, text="New Password:", font=("Arial", 14)).pack(pady=(10, 5))
        new_pw = ctk.CTkEntry(popup, show="*")
        new_pw.pack(pady=5)

        def save_new_password():
            o, n = old_pw.get(), new_pw.get()
            if not o or not n:
                messagebox.showwarning("⚠️", "Please input all fields.")
                return

            try:
                import socket, json
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.server, 5000))
                s.send(json.dumps({
                    "command": "CHANGE_PASSWORD",
                    "username": self.username,
                    "old_pw": o,
                    "new_pw": n
                }).encode())
                data = json.loads(s.recv(1024).decode())
                s.close()

                if data.get("success"):
                    messagebox.showinfo("✅", data.get("message"))
                    popup.destroy()
                else:
                    messagebox.showerror("❌", data.get("message"))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(popup, text="Submit", command=save_new_password).pack(pady=20)

    # -------------------------------
    # ❌ Log out
    # -------------------------------
    def confirm_unsubscribe(self):
        answer = messagebox.askyesno("Log out", "정말 탈퇴하시겠습니까?")
        if not answer:
            return

        try:
            import socket, json
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server, 5000))
            s.send(json.dumps({
                "command": "LOGOUT",
                "username": self.username
            }).encode())
            data = json.loads(s.recv(1024).decode())
            s.close()

            if data.get("success"):
                messagebox.showinfo("✅", data.get("message"))
                self.master.show_login()
            else:
                messagebox.showerror("❌", data.get("message"))

        except Exception as e:
            messagebox.showerror("Connecting Error", str(e))
