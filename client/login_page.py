import customtkinter as ctk
from PIL import Image
import socket, json

PORT = 5000

class LoginPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid(row=0, column=0, sticky="nsew")

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        new_width = screen_width * 0.2
        new_height = screen_height * 0.4

        bg_image = Image.open("assets/log_bg.png").convert("RGBA")
        overlay = Image.new("RGBA", bg_image.size, (190, 190, 190, 120))
        blended = Image.alpha_composite(bg_image, overlay)

        self.bg_image = ctk.CTkImage(
            light_image=blended,
            dark_image=blended,
            size=(screen_width * 0.7, screen_height * 0.7)
        )
        ctk.CTkLabel(self, image=self.bg_image, text="").grid(row=0, column=0, sticky="nsew")

        frame = ctk.CTkFrame(
            self,
            width=new_width,
            height=new_height,
            corner_radius=30,
            fg_color=("gray85", "gray25")
        )
        frame.grid(row=0, column=0)
        frame.grid_propagate(False)
        frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            frame, text="🔐 Alarm System Login",
            font=("Arial", 22, "bold"), text_color="yellow"
        ).grid(row=0, column=0, columnspan=2, pady=15)

        ctk.CTkLabel(frame, text="Server Address",
                     font=("Arial", 15, "bold"), text_color="white").grid(row=1, column=0, columnspan=2, pady=(10, 5))
        self.server = ctk.CTkEntry(frame, width=250, height=40, placeholder_text="172.16.1.160",
                                   font=("Arial", 15, "bold"))
        self.server.insert(0, "172.16.1.160")
        self.server.grid(row=2, column=0, columnspan=2)
        self.server.bind("<Key>", self.clear_message)

        ctk.CTkLabel(frame, text="Username",
                     font=("Arial", 15, "bold"), text_color="white").grid(row=3, column=0, columnspan=2, pady=(10, 5))
        self.username = ctk.CTkEntry(frame, width=250, height=40, font=("Arial", 15, "bold"),
                                     placeholder_text="Enter username")
        self.username.grid(row=4, column=0, columnspan=2)
        self.username.bind("<Key>", self.clear_message)

        ctk.CTkLabel(frame, text="Password",
                     font=("Arial", 15, "bold"), text_color="white").grid(row=5, column=0, columnspan=2, pady=(10, 5))
        self.password = ctk.CTkEntry(frame, width=250, height=40, show="*", font=("Arial", 15, "bold"),
                                     placeholder_text="Enter password")
        self.password.grid(row=6, column=0, columnspan=2)
        self.password.bind("<Key>", self.clear_message)

        self.error = ctk.CTkLabel(frame, text="", text_color="red", font=("Arial", 13, "bold"))
        self.error.grid(row=7, column=0, columnspan=2, pady=5)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=2, pady=10)

        ctk.CTkButton(btn_frame, text="Login", fg_color="#4d85ca",
                      width=100, height=40, command=self.check_login).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_frame, text="Register", fg_color="#4d85ca",
                      width=100, height=40, command=self.open_register).grid(row=0, column=1, padx=10)

    def show_message(self, text, color="red"):
        self.error.configure(text=text, text_color=color)
        # 4초 후 자동 제거
        self.after_cancel(getattr(self, "_clear_timer", None)) if hasattr(self, "_clear_timer") else None
        self._clear_timer = self.after(4000, lambda: self.error.configure(text=""))

    def clear_message(self, event=None):
        self.error.configure(text="")

    def check_login(self):
        server = self.server.get().strip()
        u = self.username.get().strip()
        p = self.password.get().strip()

        if not (server and u and p):
            self.show_message("Input username and password")
            return

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((server, PORT))
            s.send(json.dumps({"command": "LOGIN", "username": u, "password": p}).encode())
            data = json.loads(s.recv(2048).decode())
            s.close()

            if data.get("success"):
                self.show_message("✅ Login successful", color="green")
                self.after(1000, lambda: self.master.show_dashboard(u, server))
            else:
                msg = data.get("message") or "Login failed"
                self.show_message(msg)
        except socket.timeout:
            self.show_message("⏱ Server response timeout")
        except ConnectionRefusedError:
            self.show_message("🚫 Cannot connect to server")
        except Exception as e:
            self.show_message("❌ Cannot connect to server")

    def open_register(self):
        RegisterWindow(self)


class RegisterWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Register New User")
        self.geometry("400x330")
        self.parent = parent

        self.lift()
        self.focus_force()
        self.grab_set()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))

        ctk.CTkLabel(self, text="📝 Register", font=("Arial", 20, "bold")).pack(pady=10)

        ctk.CTkLabel(self, text="Username").pack()
        self.username = ctk.CTkEntry(self, width=250)
        self.username.pack()
        self.username.bind("<Key>", self.clear_message)

        ctk.CTkLabel(self, text="Password").pack(pady=(5, 0))
        self.password = ctk.CTkEntry(self, width=250, show="*")
        self.password.pack()
        self.password.bind("<Key>", self.clear_message)

        ctk.CTkLabel(self, text="Confirm Password").pack(pady=(5, 0))
        self.password2 = ctk.CTkEntry(self, width=250, show="*")
        self.password2.pack()
        self.password2.bind("<Key>", self.clear_message)

        self.msg = ctk.CTkLabel(self, text="", text_color="red", font=("Arial", 13, "bold"))
        self.msg.pack(pady=5)

        ctk.CTkButton(self, text="Register", command=self.register_user).pack(pady=10)

    # ---------------- 메시지 관리 ----------------
    def show_message(self, text, color="red"):
        self.msg.configure(text=text, text_color=color)
        self.after_cancel(getattr(self, "_clear_timer", None)) if hasattr(self, "_clear_timer") else None
        self._clear_timer = self.after(4000, lambda: self.msg.configure(text=""))

    def clear_message(self, event=None):
        self.msg.configure(text="")

    # ---------------- 회원가입 처리 ----------------
    def register_user(self):
        server = self.parent.server.get().strip()
        u = self.username.get().strip()
        p1 = self.password.get().strip()
        p2 = self.password2.get().strip()

        if not (server and u and p1 and p2):
            self.show_message("⚠ Fill all fields")
            return
        if p1 != p2:
            self.show_message("⚠ Passwords do not match")
            return

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((server, PORT))
            s.send(json.dumps({"command": "REGISTER", "username": u, "password": p1}).encode())
            data = json.loads(s.recv(2048).decode())
            s.close()

            if data.get("success"):
                self.show_message("✅ Registered successfully", color="green")
            else:
                msg = data.get("message") or "❌ Registration failed"
                self.show_message(msg)
        except socket.timeout:
            self.show_message("⏱ Server not responding")
        except ConnectionRefusedError:
            self.show_message("🚫 Cannot connect to server")
        except Exception as e:
            self.show_message(f"❌ {e}")
