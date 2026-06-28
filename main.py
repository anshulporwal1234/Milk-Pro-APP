# ==============================
# Milk Diary Pro - Perfect Hindu Paksha & Month Header Edition
# main_mobile.py
# ==============================

import calendar
import os
import smtplib
import sqlite3
from datetime import date, datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from plyer import notification

# ReportLab इम्पोर्ट्स
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from config import DATABASE_NAME, REPORT_FOLDER, load_settings, save_settings

# सेट मोबाइल स्क्रीन डाइमेंशन्स
Window.size = (360, 680)

def init_mobile_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT UNIQUE,
            milk REAL,
            payment REAL,
            status TEXT DEFAULT 'unfilled',
            rate REAL DEFAULT 65.0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS monthly_notes(
            date_key TEXT PRIMARY KEY,
            note_text TEXT
        )
    """)
    conn.commit()
    conn.close()

init_mobile_db()


class MilkDiaryMobileApp(App):

    def get_google_account_email(self):
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            AccountManager = autoclass('android.accounts.AccountManager')
            manager = AccountManager.get(activity)
            accounts = manager.getAccountsByType("com.google")
            if accounts and len(accounts) > 0:
                return accounts[0].name
        except:
            pass
        return self.config_data.get("email", "your_registered_email@gmail.com")

    def get_hindu_month_label(self, year, month):
        month_map = {
            1:  {"English": "Pausha / Magha", "Hindi": "पौष / माघ"},
            2:  {"English": "Magha / Phalguna", "Hindi": "माघ / फाल्गुन"},
            3:  {"English": "Phalguna / Chaitra", "Hindi": "फाल्गुन / चैत्र"},
            4:  {"English": "Chaitra / Vaishakha", "Hindi": "चैत्र / वैशाख"},
            5:  {"English": "Vaishakha / Jyeshtha", "Hindi": "वैशाख / ज्येष्ठ"},
            6:  {"English": "Jyeshtha / Ashadha", "Hindi": "ज्येष्ठ / आषाढ़"},
            7:  {"English": "Ashadha / Shravana", "Hindi": "आषाढ़ / श्रावण"},
            8:  {"English": "Shravana / Bhadrapada", "Hindi": "श्रावण / भाद्रपद"},
            9:  {"English": "Bhadrapada / Ashvina", "Hindi": "भाद्रपद / आश्विन"},
            10: {"English": "Ashvina / Kartika", "Hindi": "आश्विन / कार्तिक"},
            11: {"English": "Kartika / Margashirsha", "Hindi": "कार्तिक / मार्गशीर्ष"},
            12: {"English": "Margashirsha / Pausha", "Hindi": "मार्गशीर्ष / पौष"}
        }
        return month_map.get(month, {"English": "", "Hindi": ""})[self.current_lang]

    def get_hindu_tithi_with_paksha(self, cur_date):
        base_date = date(2024, 1, 11)  # अमावस्या बेस रेफरेन्स
        diff_days = (cur_date - base_date).days
        lunar_age = diff_days % 29.53059
        
        tithi_index = int((lunar_age / 29.53059) * 30) + 1
        if tithi_index > 30: tithi_index = 30
        
        names_map = {
            1: "Ekam", 2: "Dooj", 3: "Teej", 4: "Chauth", 5: "Panchami",
            6: "Chhath", 7: "Satam", 8: "Aatham", 9: "Noumi", 10: "Dashami",
            11: "Ekadashi", 12: "Dwadashi", 13: "Teras", 14: "Chaudas"
        }
        names_map_hi = {
            1: "एकम", 2: "दूज", 3: "तीज", 4: "चौथ", 5: "पंचमी",
            6: "छठ", 7: "सातम", 8: "आठम", 9: "नौमी", 10: "दशमी",
            11: "एकादशी", 12: "द्वादशी", 13: "तेरस", 14: "चौदस"
        }

        if tithi_index == 15:
            return {"English": "Punam", "Hindi": "पूनम"}[self.current_lang]
        if tithi_index == 30:
            return {"English": "Amavasya", "Hindi": "अमावस्या"}[self.current_lang]

        if tithi_index < 15:
            t_name = names_map[tithi_index] if self.current_lang == "English" else names_map_hi[tithi_index]
            p_name = "(S)" if self.current_lang == "English" else "(शु)"
            return f"{t_name} {p_name}"
        else:
            k_index = tithi_index - 15
            t_name = names_map[k_index] if self.current_lang == "English" else names_map_hi[k_index]
            p_name = "(K)" if self.current_lang == "English" else "(कृ)"
            return f"{t_name} {p_name}"

    def build(self):
        self.config_data = load_settings()
        self.milk_rate = float(self.config_data.get("milk_rate", 65.0))
        self.selected_date = date.today()
        self.current_lang = self.config_data.get("language", "English")
        self.is_loading = False
        self.block_save = False 
        
        if not self.config_data.get("email"):
            self.config_data["email"] = self.get_google_account_email()
            save_settings(self.config_data)

        self.old_milk = 0.0
        self.old_payment = 0.0
        self.old_status = "unfilled"
        self.old_rate = self.milk_rate

        # भाषा शब्दकोश
        self.lang_dict = {
            "English": {
                "milk": "Milk", "rate": "Rate", "amount": "Current Month Amount", "paid": "Paid", 
                "pending": "Pending", "days": "Days", "settings": "Settings ⚙️", 
                "pdf": "Open PDF Bill 📄", "prev": "PREV", "next": "NEXT",
                "milk_lbl": "Milk (L):", "pay_lbl": "Paid:", "notes_title": "📝 Selected Date Notes / Adjustments",
                "notes_hint": "Write note for this specific date here...", "confirm_title": "Confirm Security Update",
                "confirm_msg": "Data is locked! Want to overwrite?", "yes": "Yes, Change", "no": "No, Cancel"
            },
            "Hindi": {
                "milk": "मिल्क", "rate": "रेट", "amount": "इस महीने की रकम", "paid": "भुगतान", 
                "pending": "बकाया", "days": "कुल दिन", "settings": "सेटिंग्स ⚙️", 
                "pdf": "बिल PDF खोलें 📄", "prev": "पीछे", "next": "आगे",
                "milk_lbl": "दूध (L):", "pay_lbl": "जमा ₹:", "notes_title": "📝 चुनी हुई तारीख के नोट्स",
                "notes_hint": "इस खास तारीख का note यहाँ लिखें...", "confirm_title": "सुरक्षा लॉक पुष्टि",
                "confirm_msg": "तारीख लॉक है! क्या आप एंट्री बदलना चाहते हैं?", "yes": "हाँ, बदलें", "no": "नहीं"
            }
        }

        self.bg_color = (0.94, 0.95, 0.96, 1)      
        self.text_color = (0.09, 0.12, 0.17, 1)     
        self.card_bg = (1, 1, 1, 1)                
        self.green_highlight = (0.47, 0.81, 0.61, 1)   
        self.orange_highlight = (0.94, 0.69, 0.45, 1)  
        self.gray_filled = (0.78, 0.82, 0.85, 1)       
        self.blue_today = (0.22, 0.47, 0.84, 1)       

        root_scroll = ScrollView(size_hint=(1, 1))
        self.main_layout = BoxLayout(orientation="vertical", padding=14, spacing=10, size_hint_y=None)
        self.main_layout.bind(minimum_height=self.main_layout.setter('height'))
        
        with self.main_layout.canvas.before:
            Color(*self.bg_color)
            self.rect = Rectangle(size=Window.size, pos=self.main_layout.pos)
        self.main_layout.bind(size=self._update_rect, pos=self._update_rect)

        # 1. समरी पैनल
        self.summary_grid = GridLayout(cols=3, size_hint_y=None, height=125, spacing=6)
        self.labels = {}
        self.create_summary_cards()
        self.main_layout.add_widget(self.summary_grid)

        # 2. एक्शन बार
        self.action_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=42, spacing=6)
        self.btn_set = Button(text=self.t("settings"), font_size="13sp", size_hint_x=0.35, background_color=(0.28, 0.35, 0.44, 1), background_normal='')
        self.btn_set.bind(on_release=lambda x: self.open_settings())
        
        self.btn_pdf = Button(text=self.t("pdf"), font_size="13sp", size_hint_x=0.65, background_color=(0.75, 0.22, 0.22, 1), background_normal='')
        self.btn_pdf.bind(on_release=lambda x: self.open_pdf_bill())
        
        self.action_bar.add_widget(self.btn_set)
        self.action_bar.add_widget(self.btn_pdf)
        self.main_layout.add_widget(self.action_bar)

        # 3. डेली एंट्री पैनल
        self.entry_panel = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=8, padding=[0, 5, 0, 5])
        self.milk_spinner = Spinner(text="", values=("0", "0.5", "1", "Other"), size_hint_x=0.35)
        self.milk_spinner.bind(on_touch_down=self.on_spinner_touch_down)
        self.milk_spinner.bind(text=self.on_milk_change)
        
        self.payment_input = TextInput(hint_text="0", multiline=False, size_hint_x=0.45, input_filter="float", write_tab=False)
        self.payment_input.bind(focus=self.on_payment_focus_change)
        
        self.milk_lbl_widget = Label(text=self.t("milk_lbl"), size_hint_x=0.18, color=self.text_color, font_size="12sp")
        self.pay_lbl_widget = Label(text=self.t("pay_lbl"), size_hint_x=0.15, color=self.text_color, font_size="12sp")
        
        self.entry_panel.add_widget(self.milk_lbl_widget)
        self.entry_panel.add_widget(self.milk_spinner)
        self.entry_panel.add_widget(self.pay_lbl_widget)
        self.entry_panel.add_widget(self.payment_input)
        self.main_layout.add_widget(self.entry_panel)

        # 4. नोट्स पैनल
        self.notes_panel = BoxLayout(orientation="vertical", padding=10, spacing=5, size_hint_y=None, height=100)
        with self.notes_panel.canvas.before:
            Color(*self.card_bg)
            self.notes_rect = Rectangle(size=self.notes_panel.size, pos=self.notes_panel.pos)
        self.notes_panel.bind(size=lambda inst, val: setattr(self.notes_rect, 'size', val),
                              pos=lambda inst, val: setattr(self.notes_rect, 'pos', val))
        
        self.notes_title = Label(text=self.t("notes_title"), font_size="12sp", bold=True, color=(0.3, 0.4, 0.5, 1), size_hint_y=0.25)
        self.notes_input = TextInput(hint_text=self.t("notes_hint"), font_size="11sp", background_color=(0.97, 0.98, 0.99, 1), multiline=True)
        self.notes_input.bind(focus=self.on_notes_focus_change)
        
        self.notes_panel.add_widget(self.notes_title)
        self.notes_panel.add_widget(self.notes_input)
        self.main_layout.add_widget(self.notes_panel)

        # 5. कैलेंडर कंट्रोल बार
        self.control_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=45, spacing=10)
        self.prev_btn = Button(text=self.t("prev"), size_hint_x=0.22, bold=True, background_color=(0.6, 0.65, 0.7, 1), background_normal='')
        self.prev_btn.bind(on_release=lambda x: self.navigate_month(-1))
        
        self.month_label = Label(text="", font_size="14sp", bold=True, color=self.text_color, halign="center", markup=True)
        self.month_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        
        self.next_btn = Button(text=self.t("next"), size_hint_x=0.22, bold=True, background_color=(0.6, 0.65, 0.7, 1), background_normal='')
        self.next_btn.bind(on_release=lambda x: self.navigate_month(1))
        
        self.control_bar.add_widget(self.prev_btn)
        self.control_bar.add_widget(self.month_label)
        self.control_bar.add_widget(self.next_btn)
        self.main_layout.add_widget(self.control_bar)

        # 6. बड़ा कैलेंडर ग्रिड
        self.calendar_grid = GridLayout(cols=7, size_hint_y=None, height=430, spacing=4)
        self.main_layout.add_widget(self.calendar_grid)

        self.load_month_view()
        self.load_selected_day_data()
        self.load_monthly_note()
        self.check_new_month_and_mail()
        self.check_daily_notification()

        root_scroll.add_widget(self.main_layout)
        return root_scroll

    def t(self, key):
        return self.lang_dict.get(self.current_lang, self.lang_dict["English"]).get(key, "")

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = (instance.width, max(instance.height, Window.height))

    def create_summary_cards(self):
        cards = [
            ("milk", "0 L"), ("rate", f"₹{self.milk_rate}"), ("amount", "₹0"),
            ("paid", "₹0"), ("pending", "₹0"), ("days", "0")
        ]
        for key, value in cards:
            box = BoxLayout(orientation="vertical", padding=6, spacing=2)
            with box.canvas.before:
                Color(*self.card_bg)
                box.rect = Rectangle(size=box.size, pos=box.pos)
            box.bind(size=lambda inst, val, b=box: setattr(b.rect, 'size', val),
                     pos=lambda inst, val, b=box: setattr(b.rect, 'pos', val))
            
            title_lbl = Label(text=self.t(key), font_size="11sp", color=[0.5, 0.5, 0.6, 1])
            val_lbl = Label(text=value, font_size="15sp", bold=True, color=self.text_color)
            
            box.add_widget(title_lbl)
            box.add_widget(val_lbl)
            if key == "rate":
                box.bind(on_touch_down=self.on_rate_card_touch)
                
            self.summary_grid.add_widget(box)
            self.labels[key] = val_lbl

    def on_rate_card_touch(self, instance, touch):
        if instance.collide_point(*touch.pos) and touch.is_double_tap:
            self.open_rate_changer()

    def on_spinner_touch_down(self, spinner, touch):
        if spinner.collide_point(*touch.pos) and spinner.text == "Other" and not self.is_loading:
            self.show_other_milk_popup()

    def open_rate_changer(self):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        txt = TextInput(text=str(self.milk_rate), multiline=False, input_filter="float")
        btn = Button(text="Update & Refresh", size_hint_y=0.4, background_color=(0.2, 0.5, 0.8, 1), background_normal='')
        content.add_widget(Label(text="Enter New Milk Rate (₹/L):"))
        content.add_widget(txt)
        content.add_widget(btn)
        popup = Popup(title="Change Rate", content=content, size_hint=(0.8, 0.35))
        
        def save(x):
            try:
                self.milk_rate = float(txt.text)
                self.config_data["milk_rate"] = self.milk_rate
                save_settings(self.config_data)
                self.labels["rate"].text = f"₹{self.milk_rate}"
                self.load_month_view()
            except: pass
            popup.dismiss()
            
        btn.bind(on_release=save)
        popup.open()

    def open_settings(self):
        content = BoxLayout(orientation="vertical", padding=12, spacing=6)
        owner = TextInput(text=self.config_data.get("owner_name", ""), hint_text="Owner Name", multiline=False)
        cust = TextInput(text=self.config_data.get("customer_name", ""), hint_text="Customer Name", multiline=False)
        email = TextInput(text=self.config_data.get("email", ""), hint_text="Google Email ID", multiline=False)
        app_pass = TextInput(text=self.config_data.get("app_password", ""), hint_text="Gmail App Password (16 letters)", multiline=False, password=True)
        
        lang_spinner = Spinner(text=self.current_lang, values=("English", "Hindi"), size_hint_y=None, height=38)
        btn = Button(text="Save Configuration 💾", size_hint_y=None, height=42, background_color=(0.15, 0.55, 0.35, 1), background_normal='')
        
        content.add_widget(Label(text="Select App Language:", font_size="12sp"))
        content.add_widget(lang_spinner)
        content.add_widget(Label(text="Owner Name:", font_size="12sp"))
        content.add_widget(owner)
        content.add_widget(Label(text="Customer Name:", font_size="12sp"))
        content.add_widget(cust)
        content.add_widget(Label(text="Google Sync Mail (Auto-Fetched):", font_size="12sp"))
        content.add_widget(email)
        content.add_widget(Label(text="Gmail App Password (For Auto-Mail):", font_size="12sp"))
        content.add_widget(app_pass)
        content.add_widget(btn)
        
        popup = Popup(title="App Settings Panel", content=content, size_hint=(0.9, 0.9))
        
        def save(x):
            self.config_data["owner_name"] = owner.text.strip()
            self.config_data["customer_name"] = cust.text.strip()
            self.config_data["email"] = email.text.strip()
            self.config_data["app_password"] = app_pass.text.strip()
            self.config_data["language"] = lang_spinner.text
            save_settings(self.config_data)
            popup.dismiss()
            
            self.current_lang = lang_spinner.text
            self.refresh_ui_labels()
            
        btn.bind(on_release=save)
        popup.open()

    def refresh_ui_labels(self):
        self.btn_set.text = self.t("settings")
        self.btn_pdf.text = self.t("pdf")
        self.prev_btn.text = self.t("prev")
        self.next_btn.text = self.t("next")
        self.milk_lbl_widget.text = self.t("milk_lbl")
        self.pay_lbl_widget.text = self.t("pay_lbl")
        self.notes_title.text = self.t("notes_title")
        self.notes_input.hint_text = self.t("notes_hint")
        self.load_month_view()

    # 🌟 मास्टर रेंडरिंग कैलेंडर इंजन (ब्रैकेटेड पक्ष पृथक्करण और पूर्ण फोंट आकार नियंत्रण के साथ)
    def load_month_view(self):
        self.calendar_grid.clear_widgets()
        year, month = self.selected_date.year, self.selected_date.month
        
        eng_month_name = self.selected_date.strftime("%B %Y")
        hindu_month_name = self.get_hindu_month_label(year, month)
        self.month_label.text = f"{eng_month_name} \n[color=ff3333][b][{hindu_month_name}][/b][/color]"

        for day_name in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            self.calendar_grid.add_widget(Label(text=day_name, bold=True, size_hint_y=None, height=25, color=[0.25, 0.45, 0.75, 1]))

        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        month_str = f"{year}-{month:02d}-%"
        cur.execute("SELECT entry_date, milk, payment, status FROM entries WHERE entry_date LIKE ?", (month_str,))
        db_data = {row["entry_date"]: row for row in cur.fetchall()}
        conn.close()

        month_matrix = calendar.monthcalendar(year, month)
        today_str = date.today().strftime("%Y-%m-%d")

        for week in month_matrix:
            for day in week:
                if day == 0:
                    self.calendar_grid.add_widget(Label())
                    continue
                
                cur_date = date(year, month, day)
                date_str = cur_date.strftime("%Y-%m-%d")
                
                # 🌟 पंचांग से पक्ष सहित नाम फैच करना
                tithi_label = self.get_hindu_tithi_with_paksha(cur_date)
                
                btn_text = f"[b]{day}[/b]\n[color=ff3333]{tithi_label}[/color]\n-- L"
                bg_color = (1, 1, 1, 1) 
                t_color = (0.09, 0.12, 0.17, 1) 

                if date_str in db_data:
                    row = db_data[date_str]
                    if row["status"] == "filled":
                        bg_color = self.gray_filled
                        btn_text = f"[b]{day}[/b]\n[color=ff3333]{tithi_label}[/color]\n{row['milk']} L"
                        
                        if row["milk"] > 0: 
                            bg_color = self.green_highlight
                            
                        if row["payment"] > 0: 
                            bg_color = self.orange_highlight
                            btn_text = f"[b]{day}[/b]\n[color=ff3333]{tithi_label}[/color]\n{row['milk']} L\n₹{int(row['payment'])}"

                if date_str == today_str:
                    bg_color = self.blue_today
                    t_color = (1, 1, 1, 1)
                    if date_str in db_data and db_data[date_str]["status"] == "filled":
                        btn_text = f"[b]{day} •[/b]\n[color=ffff00]{tithi_label}[/color]\n{db_data[date_str]['milk']} L"
                        if db_data[date_str]['payment'] > 0:
                            btn_text += f"\n₹{int(db_data[date_str]['payment'])}"
                    else:
                        btn_text = f"[b]{day} •[/b]\n[color=ffff00]{tithi_label}[/color]\n-- L"

                # 🌟 इमेज image_08b098.png फिक्स: फ्यूचर डेट्स का फोंट एकदम छोटा, अलाइन और सटीक कर दिया
                if cur_date > date.today():
                    f_text = f"[b]{day}[/b]\n[color=ff6666]{tithi_label}[/color]\n-- L"
                    btn = Button(text=f_text, markup=True, background_color=[0.92, 0.93, 0.94, 0.7], color=[0.4, 0.4, 0.4, 1], font_size="11sp", halign="center", valign="middle", background_normal='')
                    btn.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
                    btn.bind(on_release=lambda x: None)
                else:
                    btn = Button(text=btn_text, markup=True, background_color=bg_color, color=t_color, font_size="11sp", halign="center", valign="middle", background_normal='')
                    btn.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
                    btn.bind(on_release=lambda x, d=cur_date: self.select_day(d))
                
                self.calendar_grid.add_widget(btn)

        self.refresh_mobile_summary()

    def select_day(self, day):
        self.selected_date = day
        self.load_selected_day_data()
        self.load_monthly_note()

    def load_selected_day_data(self):
        self.is_loading = True
        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()
        cur.execute("SELECT milk, payment, status, rate FROM entries WHERE entry_date=?", (self.selected_date.strftime("%Y-%m-%d"),))
        row = cur.fetchone()
        conn.close()

        if row:
            milk, payment, status, entry_rate = row[0], row[1], row[2], row[3]
            self.old_milk = milk
            self.old_payment = payment
            self.old_status = status
            self.old_rate = entry_rate if entry_rate else self.milk_rate
            
            if milk in [0.0, 0.5, 1.0]:
                self.milk_spinner.text = str(milk)
            else:
                self.milk_spinner.text = "Other"
                
            self.payment_input.text = "" if payment == 0.0 else str(int(payment))
        else:
            self.old_milk = 0.0
            self.old_payment = 0.0
            self.old_status = "unfilled"
            self.old_rate = self.milk_rate
            self.milk_spinner.text = "" 
            self.payment_input.text = ""
        self.is_loading = False

    def navigate_month(self, direction):
        y, m = self.selected_date.year, self.selected_date.month + direction
        if m < 1: m = 12; y -= 1
        elif m > 12: m = 1; y += 1
        
        self.selected_date = date(y, m, 1)
        self.load_month_view()
        self.load_selected_day_data()
        self.load_monthly_note()
        self.refresh_mobile_summary()

    def on_milk_change(self, spinner, text):
        if self.is_loading: return
        if text == "": return 
        if text == "Other": 
            self.show_other_milk_popup()
        else: 
            self.validate_and_save()

    def on_payment_focus_change(self, instance, has_focus):
        if not has_focus and not self.is_loading:
            if self.milk_spinner.text == "":
                self.milk_spinner.text = "0"
            self.validate_and_save()

    def on_notes_focus_change(self, instance, has_focus):
        if not has_focus:
            date_key = self.selected_date.strftime("%Y-%m-%d")
            note_text = instance.text.strip()
            
            conn = sqlite3.connect(DATABASE_NAME)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO monthly_notes(date_key, note_text)
                VALUES(?, ?)
                ON CONFLICT(date_key) DO UPDATE SET note_text=excluded.note_text
            """, (date_key, note_text))
            conn.commit()
            conn.close()
            self.generate_backend_pdf()

    def load_monthly_note(self):
        date_key = self.selected_date.strftime("%Y-%m-%d")
        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()
        cur.execute("SELECT note_text FROM monthly_notes WHERE date_key=?", (date_key,))
        row = cur.fetchone()
        conn.close()
        self.notes_input.text = row[0] if row else ""

    def show_other_milk_popup(self):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        current_val = str(self.old_milk) if self.old_milk not in [0.0, 0.5, 1.0] else ""
        txt = TextInput(text=current_val, hint_text="Litres (e.g. 2.5)", multiline=False, input_filter="float", size_hint_y=0.6)
        btn = Button(text="Save Quantity", size_hint_y=0.4, background_color=(0.2, 0.5, 0.8, 1), background_normal='')
        content.add_widget(txt)
        content.add_widget(btn)
        popup = Popup(title="Custom Milk Quantity", content=content, size_hint=(0.8, 0.35))
        
        def save(x):
            try:
                float(txt.text)
                self.block_save = True 
                self.milk_spinner.text = txt.text
                self.block_save = False
            except: 
                self.milk_spinner.text = "0"
            popup.dismiss()
            self.validate_and_save()
            
        btn.bind(on_release=save)
        popup.open()

    def validate_and_save(self):
        if self.block_save: return 
        
        try: milk = float(self.milk_spinner.text)
        except: milk = 0.0
        try: payment = float(self.payment_input.text) if self.payment_input.text.strip() != "" else 0.0
        except: payment = 0.0

        if self.old_status == "unfilled":
            self.execute_save(milk, payment, self.milk_rate)
            return

        if self.old_status == "filled" and (milk != self.old_milk or payment != self.old_payment):
            content = BoxLayout(orientation="vertical", padding=10, spacing=10)
            content.add_widget(Label(text=f"{self.t('confirm_msg')}\n\nOld: {self.old_milk}L, ₹{self.old_payment}\nNew: {milk}L, ₹{payment}", font_size="13sp"))
            btns = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=0.4)
            btn_yes = Button(text=self.t("yes"), background_color=(0.15, 0.55, 0.35, 1), background_normal='')
            btn_no = Button(text=self.t("no"), background_color=(0.75, 0.22, 0.22, 1), background_normal='')
            btns.add_widget(btn_yes)
            btns.add_widget(btn_no)
            content.add_widget(btns)
            
            popup = Popup(title=self.t("confirm_title"), content=content, size_hint=(0.85, 0.4))
            
            def proceed(x):
                popup.dismiss()
                self.execute_save(milk, payment, self.old_rate)
            def cancel(x):
                popup.dismiss()
                self.load_selected_day_data()
                
            btn_yes.bind(on_release=proceed)
            btn_no.bind(on_release=cancel)
            popup.open()
        else:
            self.execute_save(milk, payment, self.old_rate)

    def execute_save(self, milk, payment, rate_to_lock):
        date_str = self.selected_date.strftime("%Y-%m-%d")
        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO entries(entry_date, milk, payment, rate, status)
            VALUES(?, ?, ?, ?, 'filled')
            ON CONFLICT(entry_date) DO UPDATE SET milk=excluded.milk, payment=excluded.payment, status='filled'
        """, (date_str, milk, payment, rate_to_lock))
        conn.commit()
        conn.close()

        self.old_milk = milk
        self.old_payment = payment
        self.old_status = "filled"
        self.old_rate = rate_to_lock
        
        self.generate_backend_pdf()
        self.load_month_view()

    def generate_backend_pdf(self, target_date=None):
        ref_date = target_date if target_date else self.selected_date
        if not os.path.exists(REPORT_FOLDER): os.makedirs(REPORT_FOLDER)
        month_name = ref_date.strftime("%B_%Y")
        pdf_filename = os.path.join(REPORT_FOLDER, f"Milk_Bill_{month_name}.pdf")
        
        year, month = ref_date.year, ref_date.month
        month_str = f"{year}-{month:02d}-%"
        
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT entry_date, milk, payment, rate FROM entries WHERE entry_date LIKE ? ORDER BY entry_date ASC", (month_str,))
        rows = cur.fetchall()
        
        first_day = f"{year}-{month:02d}-01"
        cur.execute("SELECT milk, payment, rate FROM entries WHERE entry_date < ?", (first_day,))
        prev_pending = sum((r["milk"] * (r["rate"] if r["rate"] else self.milk_rate)) - r["payment"] for r in cur.fetchall())
        
        cur.execute("SELECT date_key, note_text FROM monthly_notes WHERE date_key LIKE ? ORDER BY date_key ASC", (month_str,))
        note_rows = cur.fetchall()
        conn.close()
        
        try:
            doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('TStyle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor("#1A365D"), spaceAfter=12)
            meta_style = ParagraphStyle('MStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#4A5568"))
            note_style = ParagraphStyle('NStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#2D3748"), leading=14)
            
            elements = []
            elements.append(Paragraph(f"<b>Milk Diary Pro - Statement</b>", title_style))
            elements.append(Paragraph(f"<b>Month:</b> {ref_date.strftime('%B %Y')}", meta_style))
            elements.append(Paragraph(f"<b>Owner:</b> {self.config_data.get('owner_name', 'Dairy Service')}", meta_style))
            elements.append(Paragraph(f"<b>Customer:</b> {self.config_data.get('customer_name', 'Valued Customer')}", meta_style))
            elements.append(Spacer(1, 15))
            
            table_data = [["Date", "Quantity", "Rate/L", "Cost", "Paid"]]
            total_milk, total_amount, total_payment = 0.0, 0.0, 0.0
            
            for r in rows:
                m, p, rate = r["milk"], r["payment"], (r["rate"] if r["rate"] else self.milk_rate)
                cost = m * rate
                total_milk += m; total_amount += cost; total_payment += p
                
                d_fmt = datetime.strptime(r["entry_date"], "%Y-%m-%d").strftime("%d-%b")
                table_data.append([d_fmt, f"{m} L", f"Rs.{rate}", f"Rs.{cost:.0f}", f"Rs.{p:.0f}"])
            
            final_pending = prev_pending + (total_amount - total_payment)
            
            t = Table(table_data, colWidths=[100, 100, 100, 100, 110])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#224784")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F7FAFC"))
            ]))
            elements.append(t)
            elements.append(Spacer(1, 15))
            
            sum_data = [
                ["Total Milk Volume:", f"{total_milk:.1f} L"],
                ["Net Cost Total:", f"Rs. {total_amount:.2f}"],
                ["Net Paid Settled:", f"Rs. {total_payment:.2f}"],
                ["Previous Balance:", f"Rs. {prev_pending:.2f}"],
                ["Net Outstanding Due:", f"Rs. {final_pending:.2f}"]
            ]
            st = Table(sum_data, colWidths=[160, 120], hAlign='RIGHT')
            st.setStyle(TableStyle([
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#E53E3E"))
            ]))
            elements.append(st)
            
            if note_rows:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph(f"<b>📄 Date-wise Notes & Special Remarks:</b>", meta_style))
                elements.append(Spacer(1, 5))
                for nr in note_rows:
                    dt_lbl = datetime.strptime(nr["date_key"], "%Y-%m-%d").strftime("%d-%b")
                    elements.append(Paragraph(f"• <b>{dt_lbl}:</b> {nr['note_text']}", note_style))
                
            doc.build(elements)
            return pdf_filename
        except:
            return None

    def check_new_month_and_mail(self):
        today = date.today()
        last_logged_month = self.config_data.get("last_mailed_month", "")
        current_month_str = today.strftime("%Y-%m")
        
        if last_logged_month == "":
            self.config_data["last_mailed_month"] = current_month_str
            save_settings(self.config_data)
            return

        if current_month_str != last_logged_month:
            lm = today.month - 1 if today.month > 1 else 12
            ly = today.year if today.month > 1 else today.year - 1
            prev_month_date = date(ly, lm, 1)
            
            pdf_to_mail = self.generate_backend_pdf(target_date=prev_month_date)
            
            if pdf_to_mail and os.path.exists(pdf_to_mail):
                recipient = self.config_data.get("email", "").strip()
                sender = self.config_data.get("email", "").strip()
                password = self.config_data.get("app_password", "").strip()
                
                if not sender or not password:
                    self.config_data["last_mailed_month"] = current_month_str
                    save_settings(self.config_data)
                    return
                
                msg = MIMEMultipart()
                msg['From'] = sender; msg['To'] = recipient
                msg['Subject'] = f"📊 Monthly Milk Statement Auto-Sent - {prev_month_date.strftime('%B %Y')}"
                msg.attach(MIMEText(f"Hello, Attached is your final dairy statement.", 'plain'))
                
                try:
                    with open(pdf_to_mail, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(pdf_to_mail)}")
                        msg.attach(part)
                        
                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(sender, password)
                    server.sendmail(sender, recipient, msg.as_string())
                    server.quit()
                    
                    self.config_data["last_mailed_month"] = current_month_str
                    save_settings(self.config_data)
                except:
                    pass

    def refresh_mobile_summary(self):
        year, month = self.selected_date.year, self.selected_date.month
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        first_day = f"{year}-{month:02d}-01"
        cur.execute("SELECT milk, payment, rate FROM entries WHERE entry_date < ?", (first_day,))
        prev_pending = sum((row["milk"] * (row["rate"] if row["rate"] else self.milk_rate)) - row["payment"] for row in cur.fetchall())

        month_str = f"{year}-{month:02d}-%"
        cur.execute("SELECT milk, payment, rate FROM entries WHERE entry_date LIKE ?", (month_str,))
        rows = cur.fetchall()
        conn.close()

        m_milk = sum(row["milk"] for row in rows)
        m_paid = sum(row["payment"] for row in rows)
        m_amt = sum(row["milk"] * (row["rate"] if row["rate"] else self.milk_rate) for row in rows)
        m_days = sum(1 for row in rows if row["milk"] > 0)

        self.labels["milk"].text = f"{m_milk:.1f} L"
        self.labels["amount"].text = f"₹{m_amt:.0f}"
        self.labels["paid"].text = f"₹{m_paid:.0f}"
        self.labels["pending"].text = f"₹{(prev_pending + (m_amt - m_paid)):.0f}"
        self.labels["days"].text = str(m_days)
        
        for key in self.labels:
            box = self.labels[key].parent
            box.children[1].text = self.t(key)

    def open_pdf_bill(self):
        month_name = self.selected_date.strftime("%B_%Y")
        pdf_path = os.path.abspath(os.path.join(REPORT_FOLDER, f"Milk_Bill_{month_name}.pdf"))
        self.generate_backend_pdf()
            
        if os.path.exists(pdf_path):
            try: os.startfile(pdf_path)
            except: pass

    def check_daily_notification(self):
        today_str = date.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()
        cur.execute("SELECT status FROM entries WHERE entry_date=?", (today_str,))
        row = cur.fetchone()
        conn.close()
        
        if not row or row[0] != "filled":
            try:
                notification.notify(title="Milk Diary Pro Reminder 🥛", message="Today's dairy ledger log is pending.", timeout=7)
            except: pass


if __name__ == "__main__":
    MilkDiaryMobileApp().run()