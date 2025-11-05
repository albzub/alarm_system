import customtkinter as ctk
from login_page import LoginPage
from dashboard_page import DashboardPage
from alarm_list_page import AlarmListPage
from db_client import init_local_db

class AlarmApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Alarm Monitoring Client")
        # self.geometry("900x600")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{int(screen_width*0.7)}x{int(screen_height*0.7)}")
        init_local_db()
        self.current_user = None
        self.pages = {}
        self.show_login()

    def clear(self):
        for page in self.pages.values():
            page.pack_forget()

    def show_login(self):
        self.clear()
        if "login" not in self.pages:
            self.pages["login"] = LoginPage(self)
        self.pages["login"].pack(fill="both", expand=True)

    def show_dashboard(self, username):
        self.clear()
        self.current_user = username
        if "dashboard" not in self.pages:
            self.pages["dashboard"] = DashboardPage(self, username)
        self.pages["dashboard"].pack(fill="both", expand=True)

    def show_alarm_list(self):
        self.clear()
        if "alarm_list" not in self.pages:
            self.pages["alarm_list"] = AlarmListPage(self, self.current_user)
        self.pages["alarm_list"].pack(fill="both", expand=True)

if __name__ == "__main__":
    app = AlarmApp()
    app.mainloop()
