# ==============================
# Milk Diary Pro
# database.py
# ==============================

import sqlite3
from config import DATABASE_NAME


class Database:

    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.create_tables()
        self.upgrade_tables()

    def create_tables(self):
        # टेबल बनाते समय ही 'rate' कॉलम शामिल कर लिया
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS entries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT UNIQUE,
            milk REAL,
            payment REAL,
            status TEXT DEFAULT 'unfilled',
            rate REAL DEFAULT 65.0
        )
        """)
        self.conn.commit()

    def upgrade_tables(self):
        """अगर पुराना डेटाबेस है, तो उसमें बिना डेटा खोए status और rate कॉलम जोड़ता है"""
        try:
            self.cur.execute("ALTER TABLE entries ADD COLUMN status TEXT DEFAULT 'unfilled'")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            # पुराने डेटाबेस में rate कॉलम जोड़ने के लिए
            self.cur.execute("ALTER TABLE entries ADD COLUMN rate REAL DEFAULT 65.0")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def save_entry(self, date_str, milk, payment, rate, status='filled'):
        # अब सेव करते समय उस दिन का रेट भी साथ में सेव होगा
        self.cur.execute("""
        INSERT INTO entries(entry_date, milk, payment, rate, status)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(entry_date)
        DO UPDATE SET
        milk=excluded.milk,
        payment=excluded.payment,
        rate=excluded.rate,
        status=excluded.status
        """, (date_str, milk, payment, rate, status))
        self.conn.commit()

    def get_entry(self, date_str):
        self.cur.execute("""
        SELECT milk, payment, rate, status
        FROM entries
        WHERE entry_date=?
        """, (date_str,))
        row = self.cur.fetchone()
        if row:
            return row
        return {"milk": 0.0, "payment": 0.0, "rate": 0.0, "status": "unfilled"}

    def get_month_entries(self, year, month):
        month_str = f"{year}-{month:02d}-%"
        self.cur.execute("""
        SELECT entry_date, milk, payment, rate, status 
        FROM entries 
        WHERE entry_date LIKE ?
        """, (month_str,))
        return self.cur.fetchall()

    def get_previous_pending(self, year, month):
        """पिछले महीनों का पेंडिंग अब डेटाबेस के रो-वाइज़ (Milk * Rate - Payment) से कैलकुलेट होगा"""
        first_day_of_month = f"{year}-{month:02d}-01"
        self.cur.execute("""
        SELECT entry_date, milk, payment, rate FROM entries WHERE entry_date < ?
        """, (first_day_of_month,))
        
        rows = self.cur.fetchall()
        prev_pending = 0.0
        for row in rows:
            amount = float(row["milk"]) * float(row["rate"])
            prev_pending += (amount - float(row["payment"]))
        return prev_pending

    def close(self):
        self.conn.close()
