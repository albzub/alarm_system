import customtkinter as ctk
from PIL import Image

class LoginPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack(fill="both", expand=True)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Background
        bg_image = Image.open("assets/log_bg.png")
        self.bg_image = ctk.CTkImage(
            light_image=bg_image,
            dark_image=bg_image,
            size=(screen_width * 0.7, screen_height * 0.7)
        )
        ctk.CTkLabel(self, image=self.bg_image, text="").place(x=0, y=0, relwidth=1, relheight=1)

        # Header label
        # ctk.CTkLabel(self, text="🔐 Login to Alarm System", font=("Arial", 20, "bold")).pack(pady=20)

        # Define frame size
        new_width = screen_width*0.25
        new_height = screen_height*0.3

        # Login panel
        frame = ctk.CTkFrame(self, width=new_width, height=new_height, corner_radius=10, bg_color="transparent", fg_color="#2a2d3e")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # Prevent frame from resizing to fit its contents
        frame.pack_propagate(False)

        # Frame contents
        ctk.CTkLabel(frame, text="🔐 Login to Alarm System", font=("Arial", 28, "bold"), text_color="yellow").pack(pady=20)
        ctk.CTkLabel(frame, text="Username", font=("Arial", 14, "bold")).pack(pady=(10, 0))
        self.username = ctk.CTkEntry(frame, width=250, placeholder_text="👤 Enter username")
        self.username.pack()
        ctk.CTkLabel(frame, text="Password", font=("Arial", 14, "bold")).pack(pady=(10, 0))
        self.password = ctk.CTkEntry(frame, width=250, placeholder_text="🔐 Enter password", show="*")
        self.password.pack()

        self.error = ctk.CTkLabel(frame, text="", text_color="red", font=("Arial", 12))
        self.error.pack(pady=(3, 0))
        ctk.CTkButton(frame, text="Login", command=self.check_login).pack(pady=15)

    def check_login(self):
        u, p = self.username.get(), self.password.get()
        if u == "admin" and p == "1234":
            self.master.show_dashboard(u)
        else:
            self.error.configure(text="❌ Invalid credentials")
