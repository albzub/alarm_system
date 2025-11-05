import customtkinter as ctk
from tkinter import ttk
import json, socket

PORT = 5000

class AlarmListPage(ctk.CTkFrame):
    def __init__(self, master, username, server):
        super().__init__(master)
        self.master = master
        self.username = username
        self.server = server

        # common variable
        self.current_page = 1
        self.rows_per_page = 10
        self.logs = []

        # =====================
        # Title
        # =====================
        title = ctk.CTkLabel(
            self, text="📋 Alarm History",
            font=("Arial", 24, "bold"),
            text_color="#181818"
        )
        title.pack(pady=(15, 10))

        # =====================
        # Table
        # =====================
        table_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1E293B")
        table_frame.pack(padx=30, pady=10, fill="both", expand=True)

        # Treeview style
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#FDFDFD",
            foreground="black",
            rowheight=50,
            fieldbackground="#FFFFFF",
            font=("Consolas", 15)
        )
        style.configure(
            "Treeview.Heading",
            font=("Arial", 17, "bold"),
            foreground="#FFFFFF",
            background="#7E7E80"
        )
        style.map("Treeview", background=[("selected", "#9DD3F7")])

        # create Treeview 
        self.table = ttk.Treeview(
            table_frame,
            columns=("Device", "TimeOn", "TimeOff", "Status"),
            show="headings"
        )

        self.table.heading("Device", text="Device")
        self.table.heading("TimeOn", text="Time On")
        self.table.heading("TimeOff", text="Time Off")
        self.table.heading("Status", text="Status")

        self.table.column("Device", width=120, anchor="center")
        self.table.column("TimeOn", width=180, anchor="center")
        self.table.column("TimeOff", width=180, anchor="center")
        self.table.column("Status", width=120, anchor="center")

        # scroll bar
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=vsb.set)

        self.table.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # =====================
        # control panel
        # =====================
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(pady=(10, 30))

        ctk.CTkButton(
            controls, text="🔄 Refresh", fg_color="#3B82F6", hover_color="#2563EB",
            width=120, height=40, corner_radius=12, command=self.load_data
        ).grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            controls, text="⬅ Back", fg_color="#64748B", hover_color="#475569",
            width=120, height=40, corner_radius=12, command=self.go_back
        ).grid(row=0, column=1, padx=8)

        ctk.CTkButton(
            controls, text="⏮ Prev", fg_color="#0D9488", hover_color="#0F766E",
            width=100, height=40, corner_radius=12, command=self.prev_page
        ).grid(row=0, column=2, padx=8)

        ctk.CTkButton(
            controls, text="Next ⏭", fg_color="#0D9488", hover_color="#0F766E",
            width=100, height=40, corner_radius=12, command=self.next_page
        ).grid(row=0, column=3, padx=8)

        # num of pages
        self.page_label = ctk.CTkLabel(
            controls, text="Page 1", font=("Arial", 14, "bold"), text_color="white"
        )
        self.page_label.grid(row=0, column=4, padx=(20, 10))

        # num of per page
        ctk.CTkLabel(controls, text="Rows per page:", font=("Arial", 13), text_color="white").grid(row=0, column=5, padx=(20, 5))
        self.per_page_menu = ctk.CTkOptionMenu(
            controls, values=["5", "10", "20", "50"], width=70, command=self.change_rows_per_page
        )
        self.per_page_menu.set("10")
        self.per_page_menu.grid(row=0, column=6, padx=(0, 10))

        self.load_data()

    # =====================================================
    # pagination
    # =====================================================
    def next_page(self):
        if self.current_page * self.rows_per_page < len(self.logs):
            self.current_page += 1
            self.display_page()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.display_page()

    def change_rows_per_page(self, value):
        self.rows_per_page = int(value)
        self.current_page = 1
        self.display_page()

    def display_page(self):
        for row in self.table.get_children():
            self.table.delete(row)

        start = (self.current_page - 1) * self.rows_per_page
        end = start + self.rows_per_page
        visible_logs = self.logs[start:end]

        for i, row in enumerate(visible_logs):
            device = str(row.get("device") or row.get("sensor_id") or "")
            time_on = str(row.get("on_time") or "")
            time_off = str(row.get("off_time") or "")
            status = str(row.get("status") or "")
            status_icon = "🟥 ALARM" if status.upper() == "ALARM" else "🟩 OK"

            tag = "even" if i % 2 == 0 else "odd"
            self.table.insert("", "end", values=(device, time_on, time_off, status_icon), tags=(tag,))

        self.table.tag_configure("even", background="#E8E8E9")
        self.table.tag_configure("odd", background="#DDDEE0")

        total_pages = max(1, (len(self.logs) + self.rows_per_page - 1) // self.rows_per_page)
        self.page_label.configure(text=f"Page {self.current_page} / {total_pages}")

    # =====================================================
    # load data from server
    # =====================================================
    def load_data(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server, PORT))
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

            text = raw.decode(errors="ignore")
            first_json = text.split("}{")[0] + "}" if "}{" in text else text.strip()
            response = json.loads(first_json)

            if response.get("type") == "LOGS":
                self.logs = response["data"]
                self.current_page = 1
                self.display_page()
            else:
                self.show_error("Invalid response")

        except Exception as e:
            self.show_error(f"❌ Error: {e}")

        self.after(10000, self.load_data)

    def show_error(self, msg):
        for row in self.table.get_children():
            self.table.delete(row)
        self.table.insert("", "end", values=(msg, "", "", ""))

    def go_back(self):
        self.master.show_dashboard(self.username, self.server)
