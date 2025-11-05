import customtkinter as ctk
from PIL import Image
import socket, json

PORT = 5000

class LoginPage(ctk.CTkFrame):
    def __init__(self, master):
        # super().__init__(master)
        super().__init__(master)
        self.master = master
        self.grid(row=0, column=0, sticky="nsew")

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # 프레임 생성
        new_width = screen_width * 0.2
        new_height = screen_height * 0.4

        bg_image = Image.open("assets/log_bg.png").convert("RGBA")
        overlay = Image.new("RGBA", bg_image.size, (190, 190, 190, 120))  # (R,G,B,A)
        blended = Image.alpha_composite(bg_image, overlay)

        self.bg_image = ctk.CTkImage(light_image=blended, dark_image=blended, size=(screen_width * 0.7, screen_height * 0.7))
        ctk.CTkLabel(self, image=self.bg_image, text="").grid(row=0, column=0, sticky="nsew")

        # 프레임은 투명한 듯 회색(중간투명 느낌)
        frame = ctk.CTkFrame(
            self,
            width=new_width,
            height=new_height,
            corner_radius=30,
            fg_color=("gray85", "gray25")  # HEX + alpha (1A ≈ 10% 불투명)
        )
        
        frame.grid(row=0, column=0)
        frame.grid_propagate(False)

        # 프레임 내부를 grid 배치
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(
            frame, text="🔐 Alarm System Login",
            font=("Arial", 22, "bold"), text_color="yellow"
        ).grid(row=0, column=0, columnspan=2, pady=15)

        # Server
        ctk.CTkLabel(
            frame, text="Server Address",
            font=("Arial", 15, "bold"), text_color="white"
        ).grid(row=1, column=0, columnspan=2, pady=(10, 5))
        self.server = ctk.CTkEntry(
            frame, width=250, height=40,
            placeholder_text="172.16.1.160",
            font=("Arial", 15, "bold")
        )
        self.server.insert(0, "172.16.1.160")
        self.server.grid(row=2, column=0, columnspan=2)

        # Username
        ctk.CTkLabel(
            frame, text="Username",
            font=("Arial", 15, "bold"), text_color="white"
        ).grid(row=3, column=0, columnspan=2, pady=(10, 5))
        self.username = ctk.CTkEntry(
            frame, width=250, height=40,
            font=("Arial", 15, "bold"),
            placeholder_text="Enter username"
        )
        self.username.grid(row=4, column=0, columnspan=2)

        # Password
        ctk.CTkLabel(
            frame, text="Password",
            font=("Arial", 15, "bold"), text_color="white"
        ).grid(row=5, column=0, columnspan=2, pady=(10, 5))
        self.password = ctk.CTkEntry(
            frame, width=250, height=40,
            show="*", font=("Arial", 15, "bold"),
            placeholder_text="Enter password"
        )
        self.password.grid(row=6, column=0, columnspan=2)

        # Error
        self.error = ctk.CTkLabel(frame, text="", text_color="red")
        self.error.grid(row=7, column=0, columnspan=2, pady=5)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=2, pady=10)

        ctk.CTkButton(
            btn_frame, text="Login",
            fg_color="#4d85ca", width=100, height=40,
            command=self.check_login
        ).grid(row=0, column=0, padx=10)

        ctk.CTkButton(
            btn_frame, text="Register",
            fg_color="#4d85ca", width=100, height=40,
            command=self.open_register
        ).grid(row=0, column=1, padx=10)

    def open_register(self):
        RegisterWindow(self)

    def check_login(self):
        server = self.server.get().strip()
        u = self.username.get().strip()
        p = self.password.get().strip()
        if not (server and u and p):
            self.error.configure(text="⚠ Fill all fields")
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((server, PORT))
            s.send(json.dumps({"command": "LOGIN", "username": u, "password": p}).encode())
            data = json.loads(s.recv(1024).decode())
            s.close()
            if data.get("success"):
                self.master.show_dashboard(u, server)
            else:
                self.error.configure(text="❌ Invalid credentials")
        except Exception as e:
            self.error.configure(text=f"❌ {e}")

class RegisterWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Register New User")
        self.geometry("400x300")
        self.parent = parent

        # ✅ 창을 항상 위로 띄움
        self.lift()
        self.focus_force()
        self.grab_set()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))  # 안정적으로 포커스 유지

        ctk.CTkLabel(self, text="📝 Register", font=("Arial", 20, "bold")).pack(pady=10)
        ctk.CTkLabel(self, text="Username").pack()
        self.username = ctk.CTkEntry(self, width=250)
        self.username.pack()

        ctk.CTkLabel(self, text="Password").pack(pady=(5, 0))
        self.password = ctk.CTkEntry(self, width=250, show="*")
        self.password.pack()

        ctk.CTkLabel(self, text="Confirm Password").pack(pady=(5, 0))
        self.password2 = ctk.CTkEntry(self, width=250, show="*")
        self.password2.pack()

        self.msg = ctk.CTkLabel(self, text="", text_color="red")
        self.msg.pack(pady=5)

        ctk.CTkButton(self, text="Register", command=self.register_user).pack(pady=10)

    def register_user(self):
        server = self.parent.server.get().strip()
        u = self.username.get().strip()
        p1 = self.password.get().strip()
        p2 = self.password2.get().strip()

        if not (server and u and p1 and p2):
            self.msg.configure(text="⚠ Fill all fields")
            return
        if p1 != p2:
            self.msg.configure(text="⚠ Passwords do not match")
            return

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((server, PORT))
            s.send(json.dumps({"command": "REGISTER", "username": u, "password": p1}).encode())
            data = json.loads(s.recv(1024).decode())
            s.close()
            if data.get("success"):
                self.msg.configure(text="✅ Registered successfully", text_color="green")
            else:
                self.msg.configure(text="❌ Username already exists")
        except Exception as e:
            self.msg.configure(text=f"❌ {e}")
