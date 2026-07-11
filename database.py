import sqlite3
import os
import shutil
from datetime import datetime

# ─── PATH SETUP ───────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
DB_PATH = os.path.join(DATA_DIR, "lasthammer.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)


# ─── CONNECTION ───────────────────────────────────────────────
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets you access columns by name
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ─── CREATE ALL TABLES ────────────────────────────────────────
def create_tables():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS general_expenditures (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            date       TEXT    NOT NULL,
            details    TEXT    NOT NULL,
            amount     REAL    NOT NULL DEFAULT 0,
            created_at TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS royalty_payments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            date       TEXT    NOT NULL,
            details    TEXT    NOT NULL,
            num_trucks INTEGER DEFAULT 0,
            amount     REAL    NOT NULL DEFAULT 0,
            created_at TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS excavator_expenditure (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT    NOT NULL,
            details      TEXT,
            hours_worked REAL    NOT NULL DEFAULT 0,
            rate_per_hour REAL   NOT NULL DEFAULT 2200,
            total_amount REAL    NOT NULL DEFAULT 0,
            diesel_litres REAL   DEFAULT 0,
            paid_cash    REAL    DEFAULT 0,
            paid_diesel  REAL    DEFAULT 0,
            balance_due  REAL    DEFAULT 0,
            created_at   TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS dumprei_expenditure (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            date             TEXT    NOT NULL,
            reg_number       TEXT    NOT NULL,
            owner_name       TEXT    NOT NULL,
            total_trips      INTEGER DEFAULT 0,
            weight_tons      REAL    DEFAULT 0,
            diesel_litres    REAL    DEFAULT 0,
            payment_received REAL    DEFAULT 0,
            balance_due      REAL    DEFAULT 0,
            details          TEXT,
            created_at       TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS truck_expenditure (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            date          TEXT    NOT NULL,
            details       TEXT    NOT NULL,
            payment       REAL    DEFAULT 0,
            diesel_litres REAL    DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS memory_notes (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            date             TEXT    NOT NULL,
            description      TEXT    NOT NULL,
            person_name      TEXT,
            amount           REAL    DEFAULT 0,
            transaction_type TEXT    DEFAULT 'Note',
            created_at       TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS debit_credit_ledger (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    NOT NULL,
            description TEXT    NOT NULL,
            party_name  TEXT,
            debit       REAL    DEFAULT 0,
            credit      REAL    DEFAULT 0,
            balance     REAL    NOT NULL DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Insert default settings if they don't exist yet
    defaults = [
        ("company_name",      "Last Hammer"),
        ("owner_email",       ""),
        ("sender_email",      ""),
        ("gmail_app_password",""),
        ("excavator_rate",    "2200"),
    ]
    for key, val in defaults:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

    conn.commit()
    conn.close()


# ─── SETTINGS ─────────────────────────────────────────────────
def get_setting(key):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else ""

def save_setting(key, value):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()


# ─── BACKUP ───────────────────────────────────────────────────
def backup_database():
    """Call this once on app start. Creates a daily backup."""
    today = datetime.now().strftime("%Y-%m-%d")
    backup_path = os.path.join(BACKUP_DIR, f"lasthammer_{today}.db")
    if os.path.exists(DB_PATH) and not os.path.exists(backup_path):
        shutil.copy2(DB_PATH, backup_path)


# ══════════════════════════════════════════════════════════════
#  CHAPTER 1 — GENERAL EXPENDITURES
# ══════════════════════════════════════════════════════════════
def ch1_get_entries(date):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM general_expenditures WHERE date=? ORDER BY id",
        (date,)
    ).fetchall()
    conn.close()
    return rows

def ch1_add(date, details, amount):
    conn = get_connection()
    conn.execute(
        "INSERT INTO general_expenditures (date, details, amount) VALUES (?,?,?)",
        (date, details, float(amount))
    )
    conn.commit()
    conn.close()

def ch1_edit(row_id, details, amount):
    conn = get_connection()
    conn.execute(
        "UPDATE general_expenditures SET details=?, amount=? WHERE id=?",
        (details, float(amount), row_id)
    )
    conn.commit()
    conn.close()

def ch1_delete(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM general_expenditures WHERE id=?", (row_id,))
    conn.commit()
    conn.close()

def ch1_daily_total(date):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM general_expenditures WHERE date=?",
        (date,)
    ).fetchone()
    conn.close()
    return row["total"]

def ch1_monthly_total(year_month):
    """year_month format: '2026-03'"""
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM general_expenditures WHERE date LIKE ?",
        (f"{year_month}%",)
    ).fetchone()
    conn.close()
    return row["total"]


# ══════════════════════════════════════════════════════════════
#  CHAPTER 2 — ROYALTY PAYMENTS
# ══════════════════════════════════════════════════════════════
def ch2_get_entries(date):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM royalty_payments WHERE date=? ORDER BY id",
        (date,)
    ).fetchall()
    conn.close()
    return rows

def ch2_add(date, details, num_trucks, amount):
    conn = get_connection()
    conn.execute(
        "INSERT INTO royalty_payments (date, details, num_trucks, amount) VALUES (?,?,?,?)",
        (date, details, int(num_trucks), float(amount))
    )
    conn.commit()
    conn.close()

def ch2_edit(row_id, details, num_trucks, amount):
    conn = get_connection()
    conn.execute(
        "UPDATE royalty_payments SET details=?, num_trucks=?, amount=? WHERE id=?",
        (details, int(num_trucks), float(amount), row_id)
    )
    conn.commit()
    conn.close()

def ch2_delete(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM royalty_payments WHERE id=?", (row_id,))
    conn.commit()
    conn.close()

def ch2_daily_total(date):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM royalty_payments WHERE date=?",
        (date,)
    ).fetchone()
    conn.close()
    return row["total"]


# ══════════════════════════════════════════════════════════════
#  CHAPTER 3 — EXCAVATOR
# ══════════════════════════════════════════════════════════════
def ch3_get_entries(date):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM excavator_expenditure WHERE date=? ORDER BY id",
        (date,)
    ).fetchall()
    conn.close()
    return rows

def ch3_add(date, details, hours, rate, diesel, paid_cash, paid_diesel):
    total   = round(hours * rate, 2)
    balance = round(total - paid_cash - paid_diesel, 2)
    conn = get_connection()
    conn.execute(
        """INSERT INTO excavator_expenditure
           (date, details, hours_worked, rate_per_hour, total_amount,
            diesel_litres, paid_cash, paid_diesel, balance_due)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (date, details, hours, rate, total, diesel, paid_cash, paid_diesel, balance)
    )
    conn.commit()
    conn.close()

def ch3_edit(row_id, details, hours, rate, diesel, paid_cash, paid_diesel):
    total   = round(hours * rate, 2)
    balance = round(total - paid_cash - paid_diesel, 2)
    conn = get_connection()
    conn.execute(
        """UPDATE excavator_expenditure
           SET details=?, hours_worked=?, rate_per_hour=?, total_amount=?,
               diesel_litres=?, paid_cash=?, paid_diesel=?, balance_due=?
           WHERE id=?""",
        (details, hours, rate, total, diesel, paid_cash, paid_diesel, balance, row_id)
    )
    conn.commit()
    conn.close()

def ch3_delete(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM excavator_expenditure WHERE id=?", (row_id,))
    conn.commit()
    conn.close()

def ch3_daily_total(date):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(total_amount),0) as total FROM excavator_expenditure WHERE date=?",
        (date,)
    ).fetchone()
    conn.close()
    return row["total"]


# ══════════════════════════════════════════════════════════════
#  CHAPTER 4 — DUMPREI
# ══════════════════════════════════════════════════════════════
def ch4_get_entries(date):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM dumprei_expenditure WHERE date=? ORDER BY id",
        (date,)
    ).fetchall()
    conn.close()
    return rows

def ch4_add(date, reg_number, owner_name, total_trips, weight_tons,
            diesel_litres, payment_received, balance_due, details):
    conn = get_connection()
    conn.execute(
        """INSERT INTO dumprei_expenditure
           (date, reg_number, owner_name, total_trips, weight_tons,
            diesel_litres, payment_received, balance_due, details)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (date, reg_number, owner_name, int(total_trips), float(weight_tons),
         float(diesel_litres), float(payment_received), float(balance_due), details)
    )
    conn.commit()
    conn.close()

def ch4_edit(row_id, reg_number, owner_name, total_trips, weight_tons,
             diesel_litres, payment_received, balance_due, details):
    conn = get_connection()
    conn.execute(
        """UPDATE dumprei_expenditure
           SET reg_number=?, owner_name=?, total_trips=?, weight_tons=?,
               diesel_litres=?, payment_received=?, balance_due=?, details=?
           WHERE id=?""",
        (reg_number, owner_name, int(total_trips), float(weight_tons),
         float(diesel_litres), float(payment_received), float(balance_due),
         details, row_id)
    )
    conn.commit()
    conn.close()

def ch4_delete(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM dumprei_expenditure WHERE id=?", (row_id,))
    conn.commit()
    conn.close()

def ch4_daily_total(date):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(payment_received),0) as total FROM dumprei_expenditure WHERE date=?",
        (date,)
    ).fetchone()
    conn.close()
    return row["total"]

def ch4_get_known_vehicles():
    """Returns list of (reg_number, owner_name) for autocomplete."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT reg_number, owner_name FROM dumprei_expenditure ORDER BY reg_number"
    ).fetchall()
    conn.close()
    return rows


# ══════════════════════════════════════════════════════════════
#  CHAPTER 5 — TRUCK / DUMPER
# ══════════════════════════════════════════════════════════════
def ch5_get_entries(date):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM truck_expenditure WHERE date=? ORDER BY id",
        (date,)
    ).fetchall()
    conn.close()
    return rows

def ch5_add(date, details, payment, diesel_litres):
    conn = get_connection()
    conn.execute(
        "INSERT INTO truck_expenditure (date, details, payment, diesel_litres) VALUES (?,?,?,?)",
        (date, details, float(payment), float(diesel_litres))
    )
    conn.commit()
    conn.close()

def ch5_edit(row_id, details, payment, diesel_litres):
    conn = get_connection()
    conn.execute(
        "UPDATE truck_expenditure SET details=?, payment=?, diesel_litres=? WHERE id=?",
        (details, float(payment), float(diesel_litres), row_id)
    )
    conn.commit()
    conn.close()

def ch5_delete(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM truck_expenditure WHERE id=?", (row_id,))
    conn.commit()
    conn.close()

def ch5_daily_total(date):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(payment),0) as total FROM truck_expenditure WHERE date=?",
        (date,)
    ).fetchone()
    conn.close()
    return row["total"]


# ══════════════════════════════════════════════════════════════
#  CHAPTER 6 — MEMORY NOTES
# ══════════════════════════════════════════════════════════════
def ch6_get_entries(date):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM memory_notes WHERE date=? ORDER BY id",
        (date,)
    ).fetchall()
    conn.close()
    return rows

def ch6_add(date, description, person_name, amount, transaction_type):
    conn = get_connection()
    conn.execute(
        """INSERT INTO memory_notes
           (date, description, person_name, amount, transaction_type)
           VALUES (?,?,?,?,?)""",
        (date, description, person_name, float(amount), transaction_type)
    )
    conn.commit()
    conn.close()

def ch6_edit(row_id, description, person_name, amount, transaction_type):
    conn = get_connection()
    conn.execute(
        """UPDATE memory_notes
           SET description=?, person_name=?, amount=?, transaction_type=?
           WHERE id=?""",
        (description, person_name, float(amount), transaction_type, row_id)
    )
    conn.commit()
    conn.close()

def ch6_delete(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM memory_notes WHERE id=?", (row_id,))
    conn.commit()
    conn.close()

def ch6_daily_total(date):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM memory_notes WHERE date=?",
        (date,)
    ).fetchone()
    conn.close()
    return row["total"]


# ══════════════════════════════════════════════════════════════
#  CHAPTER 7 — DEBIT / CREDIT LEDGER
# ══════════════════════════════════════════════════════════════
def ch7_get_all_entries():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM debit_credit_ledger ORDER BY id"
    ).fetchall()
    conn.close()
    return rows

def ch7_get_last_balance():
    conn = get_connection()
    row = conn.execute(
        "SELECT balance FROM debit_credit_ledger ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row["balance"] if row else 0.0

def ch7_add(date, description, party_name, debit, credit):
    last_bal = ch7_get_last_balance()
    new_bal  = round(last_bal + credit - debit, 2)
    conn = get_connection()
    conn.execute(
        """INSERT INTO debit_credit_ledger
           (date, description, party_name, debit, credit, balance)
           VALUES (?,?,?,?,?,?)""",
        (date, description, party_name, float(debit), float(credit), new_bal)
    )
    conn.commit()
    conn.close()

def ch7_edit(row_id, date, description, party_name, debit, credit):
    """Edit a row then recalculate all balances from that row onwards."""
    conn = get_connection()
    conn.execute(
        """UPDATE debit_credit_ledger
           SET date=?, description=?, party_name=?, debit=?, credit=?
           WHERE id=?""",
        (date, description, party_name, float(debit), float(credit), row_id)
    )
    conn.commit()
    _recalculate_ledger_balances(conn, row_id)
    conn.close()

def ch7_delete(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM debit_credit_ledger WHERE id=?", (row_id,))
    conn.commit()
    # Find the row just before the deleted one and recalculate from there
    rows = conn.execute(
        "SELECT id FROM debit_credit_ledger ORDER BY id"
    ).fetchall()
    if rows:
        _recalculate_ledger_balances(conn, rows[0]["id"])
    conn.close()

def _recalculate_ledger_balances(conn, from_id):
    """Recalculate running balances for all rows at and after from_id."""
    # Get balance just before from_id
    prev = conn.execute(
        "SELECT balance FROM debit_credit_ledger WHERE id < ? ORDER BY id DESC LIMIT 1",
        (from_id,)
    ).fetchone()
    running = prev["balance"] if prev else 0.0

    rows = conn.execute(
        "SELECT id, debit, credit FROM debit_credit_ledger WHERE id >= ? ORDER BY id",
        (from_id,)
    ).fetchall()
    for row in rows:
        running = round(running + row["credit"] - row["debit"], 2)
        conn.execute(
            "UPDATE debit_credit_ledger SET balance=? WHERE id=?",
            (running, row["id"])
        )
    conn.commit()

def ch7_get_current_balance():
    return ch7_get_last_balance()


# ══════════════════════════════════════════════════════════════
#  DASHBOARD SUMMARY
# ══════════════════════════════════════════════════════════════
def ch5_fleet_daily_total(date):
    """Total payments from fleet truck_entries for a given date."""
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(payment),0) as total FROM truck_entries WHERE date=?",
        (date,)
    ).fetchone()
    conn.close()
    return row["total"]

def get_all_daily_totals(date):
    """Returns dict of all chapter totals for a given date."""
    return {
        "ch1": ch1_daily_total(date),
        "ch2": 0,  # royalty has no monetary value now
        "ch3": ch3_daily_total(date),
        "ch4": ch4_daily_total(date),
        "ch5": ch5_fleet_daily_total(date),
        "ch6": ch6_daily_total(date),
        "balance": ch7_get_current_balance(),
    }


# ══════════════════════════════════════════════════════════════
#  GET-ALL FUNCTIONS (for show-all-records view)
# ══════════════════════════════════════════════════════════════

def ch1_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM general_expenditures ORDER BY date ASC, id ASC"
    ).fetchall()
    conn.close()
    return rows

def ch1_grand_total():
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM general_expenditures"
    ).fetchone()
    conn.close()
    return row["total"]

def ch2_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM royalty_payments ORDER BY date ASC, id ASC"
    ).fetchall()
    conn.close()
    return rows

def ch2_grand_total():
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM royalty_payments"
    ).fetchone()
    conn.close()
    return row["total"]

def ch3_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM excavator_expenditure ORDER BY date ASC, id ASC"
    ).fetchall()
    conn.close()
    return rows

def ch3_grand_total():
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(total_amount),0) as total FROM excavator_expenditure"
    ).fetchone()
    conn.close()
    return row["total"]

def ch4_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM dumprei_expenditure ORDER BY date ASC, id ASC"
    ).fetchall()
    conn.close()
    return rows

def ch4_grand_total():
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(payment_received),0) as total FROM dumprei_expenditure"
    ).fetchone()
    conn.close()
    return row["total"]

def ch5_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM truck_expenditure ORDER BY date ASC, id ASC"
    ).fetchall()
    conn.close()
    return rows

def ch5_grand_total():
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(payment),0) as total FROM truck_expenditure"
    ).fetchone()
    conn.close()
    return row["total"]

def ch6_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM memory_notes ORDER BY date ASC, id ASC"
    ).fetchall()
    conn.close()
    return rows

def ch6_grand_total():
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM memory_notes"
    ).fetchone()
    conn.close()
    return row["total"]

def ch1_get_by_id(row_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM general_expenditures WHERE id=?", (row_id,)).fetchone()
    conn.close()
    return row

def ch2_get_by_id(row_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM royalty_payments WHERE id=?", (row_id,)).fetchone()
    conn.close()
    return row

def ch3_get_by_id(row_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM excavator_expenditure WHERE id=?", (row_id,)).fetchone()
    conn.close()
    return row

def ch4_get_by_id(row_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM dumprei_expenditure WHERE id=?", (row_id,)).fetchone()
    conn.close()
    return row

def ch5_get_by_id(row_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM truck_expenditure WHERE id=?", (row_id,)).fetchone()
    conn.close()
    return row

def ch6_get_by_id(row_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM memory_notes WHERE id=?", (row_id,)).fetchone()
    conn.close()
    return row


# ══════════════════════════════════════════════════════════════
#  TRUCK FLEET REGISTRY
# ══════════════════════════════════════════════════════════════

def ensure_truck_tables():
    """Call once at startup to create fleet tables if missing."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS truck_fleet (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_number  TEXT NOT NULL UNIQUE,
            owner_name  TEXT NOT NULL,
            truck_type  TEXT DEFAULT 'Dumper',
            notes       TEXT DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS truck_entries (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            truck_id      INTEGER NOT NULL,
            date          TEXT    NOT NULL,
            details       TEXT    NOT NULL DEFAULT '',
            trips         INTEGER DEFAULT 0,
            payment       REAL    DEFAULT 0,
            diesel_litres REAL    DEFAULT 0,
            balance_due   REAL    DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (truck_id) REFERENCES truck_fleet(id)
        )
    """)
    conn.commit()
    conn.close()

# ── Fleet CRUD ────────────────────────────────────────────────
def fleet_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM truck_fleet ORDER BY reg_number"
    ).fetchall()
    conn.close()
    return rows

def fleet_add(reg_number, owner_name, truck_type, notes):
    conn = get_connection()
    conn.execute(
        "INSERT INTO truck_fleet (reg_number, owner_name, truck_type, notes) "
        "VALUES (?,?,?,?)",
        (reg_number.upper().strip(), owner_name.strip(), truck_type, notes)
    )
    conn.commit()
    conn.close()

def fleet_edit(truck_id, reg_number, owner_name, truck_type, notes):
    conn = get_connection()
    conn.execute(
        "UPDATE truck_fleet SET reg_number=?, owner_name=?, truck_type=?, notes=? "
        "WHERE id=?",
        (reg_number.upper().strip(), owner_name.strip(), truck_type, notes, truck_id)
    )
    conn.commit()
    conn.close()

def fleet_delete(truck_id):
    conn = get_connection()
    conn.execute("DELETE FROM truck_entries WHERE truck_id=?", (truck_id,))
    conn.execute("DELETE FROM truck_fleet WHERE id=?", (truck_id,))
    conn.commit()
    conn.close()

def fleet_get_by_id(truck_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM truck_fleet WHERE id=?", (truck_id,)
    ).fetchone()
    conn.close()
    return row

# ── Truck entries CRUD ────────────────────────────────────────
def truck_entries_get(truck_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM truck_entries WHERE truck_id=? ORDER BY date ASC, id ASC",
        (truck_id,)
    ).fetchall()
    conn.close()
    return rows

def truck_entries_add(truck_id, date, details, trips, payment, diesel, balance):
    conn = get_connection()
    conn.execute(
        "INSERT INTO truck_entries "
        "(truck_id, date, details, trips, payment, diesel_litres, balance_due) "
        "VALUES (?,?,?,?,?,?,?)",
        (truck_id, date, details, int(trips), float(payment),
         float(diesel), float(balance))
    )
    conn.commit()
    conn.close()

def truck_entries_edit(entry_id, date, details, trips, payment, diesel, balance):
    conn = get_connection()
    conn.execute(
        "UPDATE truck_entries SET date=?, details=?, trips=?, payment=?, "
        "diesel_litres=?, balance_due=? WHERE id=?",
        (date, details, int(trips), float(payment),
         float(diesel), float(balance), entry_id)
    )
    conn.commit()
    conn.close()

def truck_entries_delete(entry_id):
    conn = get_connection()
    conn.execute("DELETE FROM truck_entries WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()

def truck_entries_get_by_id(entry_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM truck_entries WHERE id=?", (entry_id,)
    ).fetchone()
    conn.close()
    return row

def truck_total_payment(truck_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(payment),0) as total FROM truck_entries WHERE truck_id=?",
        (truck_id,)
    ).fetchone()
    conn.close()
    return row["total"]

def truck_total_balance(truck_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(balance_due),0) as total FROM truck_entries WHERE truck_id=?",
        (truck_id,)
    ).fetchone()
    conn.close()
    return row["total"]

def fleet_grand_total():
    """Total payments across all trucks — for dashboard."""
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(payment),0) as total FROM truck_entries"
    ).fetchone()
    conn.close()
    return row["total"]


# ══════════════════════════════════════════════════════════════
#  SCHEMA MIGRATIONS — run once safely on every startup
# ══════════════════════════════════════════════════════════════
def migrate_tables():
    """Add new columns / tables needed by redesigned modules."""
    conn = get_connection()
    c = conn.cursor()

    def col_exists(table, col):
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
        return col in cols

    def table_exists(tbl):
        return c.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",
            (tbl,)).fetchone()[0] > 0

    # ── CH 2 royalty: add vehicle_number, weight ─────────────
    if not col_exists("royalty_payments", "vehicle_number"):
        c.execute("ALTER TABLE royalty_payments ADD COLUMN vehicle_number TEXT DEFAULT ''")
    if not col_exists("royalty_payments", "weight_tons"):
        c.execute("ALTER TABLE royalty_payments ADD COLUMN weight_tons REAL DEFAULT 0")

    # ── CH 3 excavator: new advance-based table ───────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS excavator_jobs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date    TEXT NOT NULL,
            details       TEXT DEFAULT '',
            cash_advance  REAL DEFAULT 0,
            diesel_value  REAL DEFAULT 0,
            total_advance REAL DEFAULT 0,
            rate_per_hour REAL DEFAULT 2200,
            status        TEXT DEFAULT 'active',
            created_at    TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS excavator_sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id     INTEGER NOT NULL,
            date       TEXT NOT NULL,
            hours      REAL DEFAULT 0,
            earned     REAL DEFAULT 0,
            notes      TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(job_id) REFERENCES excavator_jobs(id)
        )
    """)

    # ── CH 4 dumprei: add paid_cash, paid_diesel; remove weight/diesel_litres ──
    if not col_exists("dumprei_expenditure", "paid_cash"):
        c.execute("ALTER TABLE dumprei_expenditure ADD COLUMN paid_cash REAL DEFAULT 0")
    if not col_exists("dumprei_expenditure", "paid_diesel_value"):
        c.execute("ALTER TABLE dumprei_expenditure ADD COLUMN paid_diesel_value REAL DEFAULT 0")

    # ── CH 5 truck fleet: new entries table with cash/diesel/days ──
    if not col_exists("truck_entries", "paid_cash"):
        try:
            c.execute("ALTER TABLE truck_entries ADD COLUMN paid_cash REAL DEFAULT 0")
        except: pass
    if not col_exists("truck_entries", "paid_diesel_value"):
        try:
            c.execute("ALTER TABLE truck_entries ADD COLUMN paid_diesel_value REAL DEFAULT 0")
        except: pass
    if not col_exists("truck_entries", "days_worked"):
        try:
            c.execute("ALTER TABLE truck_entries ADD COLUMN days_worked REAL DEFAULT 0")
        except: pass

    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════
#  CH 2 — ROYALTY (vehicle number + weight, no payment)
# ══════════════════════════════════════════════════════════════
def ch2_add_v2(date, vehicle_number, weight_tons):
    conn = get_connection()
    conn.execute(
        "INSERT INTO royalty_payments (date, details, vehicle_number, weight_tons, num_trucks, amount) "
        "VALUES (?,?,?,?,0,0)",
        (date, vehicle_number, vehicle_number, float(weight_tons))
    )
    conn.commit(); conn.close()

def ch2_edit_v2(row_id, date, vehicle_number, weight_tons):
    conn = get_connection()
    conn.execute(
        "UPDATE royalty_payments SET date=?, details=?, vehicle_number=?, weight_tons=? WHERE id=?",
        (date, vehicle_number, vehicle_number, float(weight_tons), row_id)
    )
    conn.commit(); conn.close()

def ch2_get_all_v2():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM royalty_payments ORDER BY date ASC, id ASC"
    ).fetchall()
    conn.close()
    return rows


# ══════════════════════════════════════════════════════════════
#  CH 3 — EXCAVATOR JOBS (advance-based)
# ══════════════════════════════════════════════════════════════
def exjob_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM excavator_jobs ORDER BY start_date ASC, id ASC"
    ).fetchall()
    conn.close(); return rows

def exjob_add(start_date, details, cash_advance, diesel_value, rate):
    total = float(cash_advance) + float(diesel_value)
    conn = get_connection()
    conn.execute(
        "INSERT INTO excavator_jobs (start_date,details,cash_advance,diesel_value,total_advance,rate_per_hour) "
        "VALUES (?,?,?,?,?,?)",
        (start_date, details, float(cash_advance), float(diesel_value), total, float(rate))
    )
    conn.commit(); conn.close()

def exjob_edit(job_id, start_date, details, cash_advance, diesel_value, rate):
    total = float(cash_advance) + float(diesel_value)
    conn = get_connection()
    conn.execute(
        "UPDATE excavator_jobs SET start_date=?,details=?,cash_advance=?,diesel_value=?,"
        "total_advance=?,rate_per_hour=? WHERE id=?",
        (start_date, details, float(cash_advance), float(diesel_value), total, float(rate), job_id)
    )
    conn.commit(); conn.close()

def exjob_delete(job_id):
    conn = get_connection()
    conn.execute("DELETE FROM excavator_sessions WHERE job_id=?", (job_id,))
    conn.execute("DELETE FROM excavator_jobs WHERE id=?", (job_id,))
    conn.commit(); conn.close()

def exjob_get_by_id(job_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM excavator_jobs WHERE id=?", (job_id,)).fetchone()
    conn.close(); return row

def exsession_get(job_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM excavator_sessions WHERE job_id=? ORDER BY date ASC, id ASC",
        (job_id,)
    ).fetchall()
    conn.close(); return rows

def exsession_add(job_id, date, hours, notes):
    job = exjob_get_by_id(job_id)
    earned = round(float(hours) * float(job["rate_per_hour"]), 2)
    conn = get_connection()
    conn.execute(
        "INSERT INTO excavator_sessions (job_id,date,hours,earned,notes) VALUES (?,?,?,?,?)",
        (job_id, date, float(hours), earned, notes)
    )
    conn.commit(); conn.close()

def exsession_edit(session_id, date, hours, notes):
    conn = get_connection()
    s = conn.execute("SELECT * FROM excavator_sessions WHERE id=?", (session_id,)).fetchone()
    if s:
        job = conn.execute("SELECT * FROM excavator_jobs WHERE id=?", (s["job_id"],)).fetchone()
        earned = round(float(hours) * float(job["rate_per_hour"]), 2)
        conn.execute(
            "UPDATE excavator_sessions SET date=?,hours=?,earned=?,notes=? WHERE id=?",
            (date, float(hours), earned, notes, session_id)
        )
    conn.commit(); conn.close()

def exsession_delete(session_id):
    conn = get_connection()
    conn.execute("DELETE FROM excavator_sessions WHERE id=?", (session_id,))
    conn.commit(); conn.close()

def exsession_get_by_id(session_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM excavator_sessions WHERE id=?", (session_id,)).fetchone()
    conn.close(); return row

def exjob_total_earned(job_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(earned),0) as t FROM excavator_sessions WHERE job_id=?",
        (job_id,)
    ).fetchone()
    conn.close(); return row["t"]

def ex_grand_total():
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(total_advance),0) as t FROM excavator_jobs"
    ).fetchone()
    conn.close(); return row["t"]


# ══════════════════════════════════════════════════════════════
#  CH 4 — DUMPREI (advance cash + diesel, no weight/diesel-litres)
# ══════════════════════════════════════════════════════════════
def ch4_add_v2(date, reg_number, owner_name, total_trips,
               paid_cash, paid_diesel_value, balance_due, details):
    conn = get_connection()
    conn.execute(
        "INSERT INTO dumprei_expenditure "
        "(date,reg_number,owner_name,total_trips,weight_tons,diesel_litres,"
        " payment_received,paid_cash,paid_diesel_value,balance_due,details) "
        "VALUES (?,?,?,?,0,0,?,?,?,?,?)",
        (date, reg_number.upper().strip(), owner_name.strip(),
         int(total_trips),
         float(paid_cash) + float(paid_diesel_value),
         float(paid_cash), float(paid_diesel_value),
         float(balance_due), details)
    )
    conn.commit(); conn.close()

def ch4_edit_v2(row_id, date, reg_number, owner_name, total_trips,
                paid_cash, paid_diesel_value, balance_due, details):
    conn = get_connection()
    conn.execute(
        "UPDATE dumprei_expenditure SET date=?,reg_number=?,owner_name=?,"
        "total_trips=?,payment_received=?,paid_cash=?,paid_diesel_value=?,"
        "balance_due=?,details=? WHERE id=?",
        (date, reg_number.upper().strip(), owner_name.strip(),
         int(total_trips),
         float(paid_cash) + float(paid_diesel_value),
         float(paid_cash), float(paid_diesel_value),
         float(balance_due), details, row_id)
    )
    conn.commit(); conn.close()

def ch4_get_all_v2():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM dumprei_expenditure ORDER BY date ASC, id ASC"
    ).fetchall()
    conn.close(); return rows


# ══════════════════════════════════════════════════════════════
#  DASHBOARD DAILY TOTAL (today only)
# ══════════════════════════════════════════════════════════════
def get_today_total(today):
    conn = get_connection()
    def q(sql, params):
        try:
            return conn.execute(sql, params).fetchone()[0] or 0
        except:
            return 0
    t1 = q("SELECT COALESCE(SUM(amount),0)          FROM general_expenditures  WHERE date=?",       (today,))
    t3 = q("SELECT COALESCE(SUM(total_amount),0)    FROM excavator_expenditure WHERE date=?",        (today,))
    t4 = q("SELECT COALESCE(SUM(payment_received),0) FROM dumprei_expenditure   WHERE date=?",       (today,))
    t5 = q("SELECT COALESCE(SUM(payment),0)          FROM truck_entries         WHERE date=?",       (today,))
    t6 = q("SELECT COALESCE(SUM(amount),0)           FROM memory_notes          WHERE date=?",       (today,))
    conn.close()
    return t1 + t3 + t4 + t5 + t6


# ══════════════════════════════════════════════════════════════
#  NEW SCHEMA UPGRADES  (safe to call every run)
# ══════════════════════════════════════════════════════════════

def upgrade_tables():
    """Add new columns and tables needed by redesigned modules."""
    conn = get_connection()
    # ── Royalty: drop amount/num_trucks, add vehicle_number + weight_tons
    try:
        conn.execute("ALTER TABLE royalty_payments ADD COLUMN vehicle_number TEXT DEFAULT ''")
    except: pass
    try:
        conn.execute("ALTER TABLE royalty_payments ADD COLUMN weight_tons REAL DEFAULT 0")
    except: pass

    # ── Excavator advance tracking
    try:
        conn.execute("ALTER TABLE excavator_expenditure ADD COLUMN cash_advance REAL DEFAULT 0")
    except: pass
    try:
        conn.execute("ALTER TABLE excavator_expenditure ADD COLUMN diesel_advance REAL DEFAULT 0")
    except: pass
    try:
        conn.execute("ALTER TABLE excavator_expenditure ADD COLUMN cash_used REAL DEFAULT 0")
    except: pass
    try:
        conn.execute("ALTER TABLE excavator_expenditure ADD COLUMN diesel_used REAL DEFAULT 0")
    except: pass

    # ── Dumprei: add paid_cash, paid_diesel columns
    try:
        conn.execute("ALTER TABLE dumprei_expenditure ADD COLUMN paid_cash REAL DEFAULT 0")
    except: pass
    try:
        conn.execute("ALTER TABLE dumprei_expenditure ADD COLUMN paid_diesel_worth REAL DEFAULT 0")
    except: pass

    # ── Loaders: separate table for loader type trucks
    conn.execute("""
        CREATE TABLE IF NOT EXISTS loader_entries (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            truck_id      INTEGER NOT NULL,
            entry_type    TEXT    NOT NULL DEFAULT 'work',
            date          TEXT    NOT NULL,
            description   TEXT    DEFAULT '',
            days_worked   REAL    DEFAULT 0,
            cash_paid     REAL    DEFAULT 0,
            diesel_worth  REAL    DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (truck_id) REFERENCES truck_fleet(id)
        )
    """)
    conn.commit()
    conn.close()

# ── Royalty redesigned CRUD ────────────────────────────────────
def ch2_add_v2(date, vehicle_number, weight_tons, payment=0, details=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO royalty_payments (date, details, vehicle_number, weight_tons, num_trucks, amount) "
        "VALUES (?,?,?,?,0,?)",
        (date, details or "", vehicle_number.strip().upper(), float(weight_tons), float(payment))
    )
    conn.commit(); conn.close()

def ch2_edit_v2(row_id, date, vehicle_number, weight_tons, payment=0, details=""):
    conn = get_connection()
    conn.execute(
        "UPDATE royalty_payments SET date=?, details=?, vehicle_number=?, weight_tons=?, amount=? WHERE id=?",
        (date, details or "", vehicle_number.strip().upper(), float(weight_tons), float(payment), row_id)
    )
    conn.commit(); conn.close()

def ch2_get_all_v2():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM royalty_payments ORDER BY date ASC, id ASC"
    ).fetchall(); conn.close(); return rows

def ch2_grand_total_v2():
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM royalty_payments"
    ).fetchone(); conn.close(); return row["total"]

def ch2_total_weight():
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(weight_tons),0) as total FROM royalty_payments"
    ).fetchone(); conn.close(); return row["total"]

# ── Excavator redesigned CRUD ─────────────────────────────────
def ch3_add_v2(date, details, hours_worked, rate_per_hour,
               cash_advance, diesel_advance, cash_used, diesel_used):
    total    = float(hours_worked) * float(rate_per_hour)
    advances = float(cash_advance) + float(diesel_advance)
    used     = float(cash_used) + float(diesel_used)
    balance  = advances - used
    conn = get_connection()
    conn.execute(
        "INSERT INTO excavator_expenditure "
        "(date, details, hours_worked, rate_per_hour, total_amount, "
        " diesel_litres, paid_cash, paid_diesel, balance_due, "
        " cash_advance, diesel_advance, cash_used, diesel_used) "
        "VALUES (?,?,?,?,?,0,?,?,?,?,?,?,?)",
        (date, details or "", float(hours_worked), float(rate_per_hour),
         total, float(cash_advance), float(diesel_advance), balance,
         float(cash_advance), float(diesel_advance),
         float(cash_used), float(diesel_used))
    )
    conn.commit(); conn.close()

def ch3_edit_v2(row_id, date, details, hours_worked, rate_per_hour,
                cash_advance, diesel_advance, cash_used, diesel_used):
    total   = float(hours_worked) * float(rate_per_hour)
    balance = (float(cash_advance) + float(diesel_advance)) - (float(cash_used) + float(diesel_used))
    conn = get_connection()
    conn.execute(
        "UPDATE excavator_expenditure SET "
        "date=?, details=?, hours_worked=?, rate_per_hour=?, total_amount=?, "
        "paid_cash=?, paid_diesel=?, balance_due=?, "
        "cash_advance=?, diesel_advance=?, cash_used=?, diesel_used=? "
        "WHERE id=?",
        (date, details or "", float(hours_worked), float(rate_per_hour), total,
         float(cash_advance), float(diesel_advance), balance,
         float(cash_advance), float(diesel_advance),
         float(cash_used), float(diesel_used), row_id)
    )
    conn.commit(); conn.close()

# ── Dumprei redesigned CRUD ───────────────────────────────────
def ch4_add_v2(date, reg_number, owner_name, total_trips,
               paid_cash, paid_diesel_worth, balance_due, details=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO dumprei_expenditure "
        "(date, reg_number, owner_name, total_trips, weight_tons, diesel_litres, "
        " payment_received, balance_due, details, paid_cash, paid_diesel_worth) "
        "VALUES (?,?,?,?,0,0,?,?,?,?,?)",
        (date, reg_number.strip().upper(), owner_name.strip(),
         int(total_trips) if total_trips else 0,
         float(paid_cash) + float(paid_diesel_worth),
         float(balance_due), details or "",
         float(paid_cash), float(paid_diesel_worth))
    )
    conn.commit(); conn.close()

def ch4_edit_v2(row_id, date, reg_number, owner_name, total_trips,
                paid_cash, paid_diesel_worth, balance_due, details=""):
    conn = get_connection()
    conn.execute(
        "UPDATE dumprei_expenditure SET "
        "date=?, reg_number=?, owner_name=?, total_trips=?, "
        "payment_received=?, balance_due=?, details=?, "
        "paid_cash=?, paid_diesel_worth=? WHERE id=?",
        (date, reg_number.strip().upper(), owner_name.strip(),
         int(total_trips) if total_trips else 0,
         float(paid_cash) + float(paid_diesel_worth),
         float(balance_due), details or "",
         float(paid_cash), float(paid_diesel_worth), row_id)
    )
    conn.commit(); conn.close()

def ch4_get_all_v2():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM dumprei_expenditure ORDER BY date ASC, id ASC"
    ).fetchall(); conn.close(); return rows

# ── Loader entries CRUD ───────────────────────────────────────
def loader_entries_get(truck_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM loader_entries WHERE truck_id=? ORDER BY date ASC, id ASC",
        (truck_id,)
    ).fetchall(); conn.close(); return rows

def loader_entries_add(truck_id, entry_type, date, description,
                       days_worked, cash_paid, diesel_worth):
    conn = get_connection()
    conn.execute(
        "INSERT INTO loader_entries "
        "(truck_id, entry_type, date, description, days_worked, cash_paid, diesel_worth) "
        "VALUES (?,?,?,?,?,?,?)",
        (truck_id, entry_type, date, description or "",
         float(days_worked), float(cash_paid), float(diesel_worth))
    )
    conn.commit(); conn.close()

def loader_entries_edit(entry_id, entry_type, date, description,
                        days_worked, cash_paid, diesel_worth):
    conn = get_connection()
    conn.execute(
        "UPDATE loader_entries SET entry_type=?, date=?, description=?, "
        "days_worked=?, cash_paid=?, diesel_worth=? WHERE id=?",
        (entry_type, date, description or "",
         float(days_worked), float(cash_paid), float(diesel_worth), entry_id)
    )
    conn.commit(); conn.close()

def loader_entries_delete(entry_id):
    conn = get_connection()
    conn.execute("DELETE FROM loader_entries WHERE id=?", (entry_id,))
    conn.commit(); conn.close()

def loader_entries_get_by_id(entry_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM loader_entries WHERE id=?", (entry_id,)
    ).fetchone(); conn.close(); return row

def loader_total_cash(truck_id):
    conn = get_connection()
    r = conn.execute(
        "SELECT COALESCE(SUM(cash_paid),0) as t FROM loader_entries WHERE truck_id=?",
        (truck_id,)).fetchone(); conn.close(); return r["t"]

def loader_total_diesel(truck_id):
    conn = get_connection()
    r = conn.execute(
        "SELECT COALESCE(SUM(diesel_worth),0) as t FROM loader_entries WHERE truck_id=?",
        (truck_id,)).fetchone(); conn.close(); return r["t"]

def loader_total_days(truck_id):
    conn = get_connection()
    r = conn.execute(
        "SELECT COALESCE(SUM(days_worked),0) as t FROM loader_entries WHERE truck_id=?",
        (truck_id,)).fetchone(); conn.close(); return r["t"]


def upgrade_truck_entries():
    """Add paid_cash / paid_diesel columns to truck_entries if missing."""
    conn = get_connection()
    for col in ["paid_cash", "paid_diesel", "trips"]:
        try:
            conn.execute(f"ALTER TABLE truck_entries ADD COLUMN {col} REAL DEFAULT 0")
        except: pass
    conn.commit(); conn.close()


# ══════════════════════════════════════════════════════════════
#  NEW MODULES  CH9–CH14  (completely independent, safe to add)
# ══════════════════════════════════════════════════════════════

def init_new_modules():
    """Create all new module tables. Called from main.py after existing init."""
    conn = get_connection()
    conn.executescript("""
        -- CH9: Advance / Loan Register
        CREATE TABLE IF NOT EXISTS advances (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT    NOT NULL,
            person_name  TEXT    NOT NULL,
            category     TEXT    NOT NULL DEFAULT 'Other',
            amount       REAL    NOT NULL DEFAULT 0,
            note         TEXT    DEFAULT '',
            repaid       REAL    NOT NULL DEFAULT 0,
            status       TEXT    NOT NULL DEFAULT 'Pending'
        );

        -- CH10: Production Tracker
        CREATE TABLE IF NOT EXISTS production (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT    NOT NULL,
            shift        TEXT    NOT NULL DEFAULT 'Day',
            tons_extracted REAL  NOT NULL DEFAULT 0,
            machine      TEXT    NOT NULL DEFAULT 'Excavator',
            operator     TEXT    DEFAULT '',
            hours_run    REAL    DEFAULT 0,
            note         TEXT    DEFAULT ''
        );

        -- CH12: Alerts
        CREATE TABLE IF NOT EXISTS alerts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            created_date TEXT    NOT NULL,
            due_date     TEXT    NOT NULL,
            title        TEXT    NOT NULL,
            body         TEXT    DEFAULT '',
            category     TEXT    NOT NULL DEFAULT 'General',
            priority     TEXT    NOT NULL DEFAULT 'Normal',
            status       TEXT    NOT NULL DEFAULT 'Active',
            dismissed    INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.commit(); conn.close()

# ── CH9: Advances ─────────────────────────────────────────────
def adv_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM advances ORDER BY date DESC, id DESC"
    ).fetchall(); conn.close(); return rows

def adv_get_pending():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM advances WHERE status='Pending' ORDER BY date ASC"
    ).fetchall(); conn.close(); return rows

def adv_add(date, person_name, category, amount, note=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO advances (date,person_name,category,amount,note,repaid,status) "
        "VALUES (?,?,?,?,?,0,'Pending')",
        (date, person_name.strip(), category, float(amount), note)
    ); conn.commit(); conn.close()

def adv_repay(adv_id, repaid_amount):
    conn = get_connection()
    row = conn.execute("SELECT amount,repaid FROM advances WHERE id=?", (adv_id,)).fetchone()
    if row:
        new_repaid = float(row["repaid"]) + float(repaid_amount)
        status = "Cleared" if new_repaid >= float(row["amount"]) else "Pending"
        conn.execute("UPDATE advances SET repaid=?, status=? WHERE id=?",
                     (new_repaid, status, adv_id))
        conn.commit()
    conn.close()

def adv_delete(adv_id):
    conn = get_connection()
    conn.execute("DELETE FROM advances WHERE id=?", (adv_id,))
    conn.commit(); conn.close()

def adv_total_outstanding():
    conn = get_connection()
    r = conn.execute(
        "SELECT COALESCE(SUM(amount-repaid),0) as t FROM advances WHERE status='Pending'"
    ).fetchone(); conn.close(); return r["t"]

# ── CH10: Production ──────────────────────────────────────────
def prod_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM production ORDER BY date DESC, id DESC"
    ).fetchall(); conn.close(); return rows

def prod_get_range(date_from, date_to):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM production WHERE date>=? AND date<=? ORDER BY date ASC",
        (date_from, date_to)
    ).fetchall(); conn.close(); return rows

def prod_add(date, shift, tons, machine, operator, hours_run, note=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO production (date,shift,tons_extracted,machine,operator,hours_run,note) "
        "VALUES (?,?,?,?,?,?,?)",
        (date, shift, float(tons), machine, operator, float(hours_run), note)
    ); conn.commit(); conn.close()

def prod_edit(row_id, date, shift, tons, machine, operator, hours_run, note=""):
    conn = get_connection()
    conn.execute(
        "UPDATE production SET date=?,shift=?,tons_extracted=?,machine=?,"
        "operator=?,hours_run=?,note=? WHERE id=?",
        (date, shift, float(tons), machine, operator, float(hours_run), note, row_id)
    ); conn.commit(); conn.close()

def prod_delete(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM production WHERE id=?", (row_id,))
    conn.commit(); conn.close()

def prod_total_tons(date_from=None, date_to=None):
    conn = get_connection()
    if date_from and date_to:
        r = conn.execute(
            "SELECT COALESCE(SUM(tons_extracted),0) as t FROM production "
            "WHERE date>=? AND date<=?", (date_from, date_to)).fetchone()
    else:
        r = conn.execute(
            "SELECT COALESCE(SUM(tons_extracted),0) as t FROM production").fetchone()
    conn.close(); return r["t"]

# ── CH12: Alerts ──────────────────────────────────────────────
def alert_get_active():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM alerts WHERE dismissed=0 ORDER BY due_date ASC"
    ).fetchall(); conn.close(); return rows

def alert_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY due_date ASC"
    ).fetchall(); conn.close(); return rows

def alert_add(created_date, due_date, title, body, category, priority):
    conn = get_connection()
    conn.execute(
        "INSERT INTO alerts (created_date,due_date,title,body,category,priority,status,dismissed) "
        "VALUES (?,?,?,?,?,?,'Active',0)",
        (created_date, due_date, title, body, category, priority)
    ); conn.commit(); conn.close()

def alert_dismiss(alert_id):
    conn = get_connection()
    conn.execute("UPDATE alerts SET dismissed=1,status='Done' WHERE id=?", (alert_id,))
    conn.commit(); conn.close()

def alert_delete(alert_id):
    conn = get_connection()
    conn.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
    conn.commit(); conn.close()

def alert_count_overdue():
    from datetime import date
    today = date.today().isoformat()
    conn = get_connection()
    r = conn.execute(
        "SELECT COUNT(*) as c FROM alerts WHERE dismissed=0 AND due_date<=?", (today,)
    ).fetchone(); conn.close(); return r["c"]

# ── Global Search ─────────────────────────────────────────────
def global_search(query):
    """Search across all major tables. Robust — each table wrapped in try/except."""
    q    = f"%{query.strip()}%"
    qnum = query.strip()  # for amount search
    conn = get_connection()
    results = []

    def safe_query(sql, params, builder):
        try:
            for r in conn.execute(sql, params).fetchall():
                try:
                    item = builder(r)
                    if item: results.append(item)
                except Exception:
                    pass
        except Exception:
            pass

    # CH1 General — column is "details" not "description"
    safe_query(
        "SELECT id,date,details,amount FROM general_expenditures "
        "WHERE details LIKE ? OR CAST(amount AS TEXT) LIKE ? ORDER BY date DESC LIMIT 25",
        (q, q),
        lambda r: {"source":"CH1 General","date":r["date"],
                   "description":r["details"] or "General expense",
                   "amount":float(r["amount"] or 0),"id":r["id"],
                   "extra":""}
    )

    # CH2 Royalty — has vehicle_number (upgraded) + details + weight_tons
    safe_query(
        "SELECT id,date,"
        "COALESCE(NULLIF(vehicle_number,''),details,'') as veh,"
        "COALESCE(weight_tons,0) as wt, amount "
        "FROM royalty_payments "
        "WHERE details LIKE ? OR vehicle_number LIKE ? OR CAST(amount AS TEXT) LIKE ? "
        "ORDER BY date DESC LIMIT 25",
        (q, q, q),
        lambda r: {"source":"CH2 Royalty","date":r["date"],
                   "description":f"Vehicle: {r['veh']}  |  Weight: {float(r['wt'] or 0):,.0f} kg",
                   "amount":float(r["amount"] or 0),"id":r["id"],
                   "extra":f"{float(r['wt'] or 0):,.0f} kg"}
    )

    # CH3 Excavator
    safe_query(
        "SELECT id,date,details,hours_worked,total_amount FROM excavator_expenditure "
        "WHERE details LIKE ? OR CAST(total_amount AS TEXT) LIKE ? ORDER BY date DESC LIMIT 25",
        (q, q),
        lambda r: {"source":"CH3 Excavator","date":r["date"],
                   "description":r["details"] or "Work session",
                   "amount":float(r["total_amount"] or 0),"id":r["id"],
                   "extra":f"{float(r['hours_worked'] or 0):.1f} hrs"}
    )

    # CH4 Dumprei — amount column is "payment_received"
    safe_query(
        "SELECT id,date,reg_number,owner_name,total_trips,payment_received "
        "FROM dumprei_expenditure "
        "WHERE reg_number LIKE ? OR owner_name LIKE ? OR details LIKE ? "
        "ORDER BY date DESC LIMIT 25",
        (q, q, q),
        lambda r: {"source":"CH4 Dumprei","date":r["date"],
                   "description":f"{r['owner_name']}  ({r['reg_number']})",
                   "amount":float(r["payment_received"] or 0),"id":r["id"],
                   "extra":f"{int(r['total_trips'] or 0)} trips"}
    )

    # CH5 Truck fleet
    safe_query(
        "SELECT te.id,te.date,te.payment,tf.owner_name,tf.reg_number,"
        "COALESCE(te.trips,0) as trips "
        "FROM truck_entries te JOIN truck_fleet tf ON te.truck_id=tf.id "
        "WHERE tf.owner_name LIKE ? OR tf.reg_number LIKE ? "
        "ORDER BY te.date DESC LIMIT 25",
        (q, q),
        lambda r: {"source":"CH5 Truck","date":r["date"],
                   "description":f"{r['owner_name']}  ({r['reg_number']})",
                   "amount":float(r["payment"] or 0),"id":r["id"],
                   "extra":f"{int(r['trips'] or 0)} trips"}
    )

    # CH5 Loader
    safe_query(
        "SELECT le.id,le.date,le.cash_paid,le.diesel_worth,le.days_worked,"
        "tf.owner_name,tf.reg_number "
        "FROM loader_entries le JOIN truck_fleet tf ON le.truck_id=tf.id "
        "WHERE tf.owner_name LIKE ? OR tf.reg_number LIKE ? "
        "ORDER BY le.date DESC LIMIT 25",
        (q, q),
        lambda r: {"source":"CH5 Loader","date":r["date"],
                   "description":f"{r['owner_name']}  ({r['reg_number']})",
                   "amount":float(r["cash_paid"] or 0)+float(r["diesel_worth"] or 0),
                   "id":r["id"],
                   "extra":f"{float(r['days_worked'] or 0):.1f} days"}
    )

    # CH6 Memory notes
    safe_query(
        "SELECT id,date,description,person_name,amount FROM memory_notes "
        "WHERE description LIKE ? OR person_name LIKE ? ORDER BY date DESC LIMIT 25",
        (q, q),
        lambda r: {"source":"CH6 Memo","date":r["date"],
                   "description":f"{r['description']}  |  {r['person_name'] or ''}",
                   "amount":float(r["amount"] or 0),"id":r["id"],
                   "extra":""}
    )

    # CH9 Advances
    safe_query(
        "SELECT id,date,person_name,amount,repaid,note FROM advances "
        "WHERE person_name LIKE ? OR note LIKE ? ORDER BY date DESC LIMIT 25",
        (q, q),
        lambda r: {"source":"CH9 Advance","date":r["date"],
                   "description":f"{r['person_name']}  —  {r['note'] or ''}",
                   "amount":float(r["amount"] or 0),"id":r["id"],
                   "extra":f"Repaid: PKR {float(r['repaid'] or 0):,.0f}"}
    )

    conn.close()
    results.sort(key=lambda x: x.get("date",""), reverse=True)
    return results


# ══════════════════════════════════════════════════════════════
#  CH15 — Diesel & Cash Distribution Tracker
# ══════════════════════════════════════════════════════════════
def init_fuel_tracker():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS fuel_cash_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT    NOT NULL,
            entry_type   TEXT    NOT NULL DEFAULT 'Diesel',
            given_to     TEXT    NOT NULL,
            category     TEXT    NOT NULL DEFAULT 'Machine',
            quantity      REAL    DEFAULT 0,
            unit         TEXT    DEFAULT 'Litres',
            rate_per_unit REAL   DEFAULT 0,
            amount        REAL   NOT NULL DEFAULT 0,
            vehicle_reg  TEXT    DEFAULT '',
            purpose      TEXT    DEFAULT '',
            ref_chapter  TEXT    DEFAULT '',
            created_at   TEXT    DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit(); conn.close()

def fuel_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM fuel_cash_log ORDER BY date DESC, id DESC"
    ).fetchall(); conn.close(); return rows

def fuel_get_range(date_from, date_to, entry_type=None):
    conn = get_connection()
    if entry_type and entry_type != "All":
        rows = conn.execute(
            "SELECT * FROM fuel_cash_log WHERE date>=? AND date<=? AND entry_type=? "
            "ORDER BY date DESC, id DESC",
            (date_from, date_to, entry_type)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM fuel_cash_log WHERE date>=? AND date<=? "
            "ORDER BY date DESC, id DESC",
            (date_from, date_to)).fetchall()
    conn.close(); return rows

def fuel_add(date, entry_type, given_to, category, quantity,
             unit, rate_per_unit, amount, vehicle_reg, purpose, ref_chapter=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO fuel_cash_log "
        "(date,entry_type,given_to,category,quantity,unit,rate_per_unit,"
        "amount,vehicle_reg,purpose,ref_chapter) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (date, entry_type, given_to.strip(), category,
         float(quantity), unit, float(rate_per_unit),
         float(amount), vehicle_reg.strip(), purpose.strip(), ref_chapter)
    ); conn.commit(); conn.close()

def fuel_edit(row_id, date, entry_type, given_to, category, quantity,
              unit, rate_per_unit, amount, vehicle_reg, purpose, ref_chapter=""):
    conn = get_connection()
    conn.execute(
        "UPDATE fuel_cash_log SET date=?,entry_type=?,given_to=?,category=?,"
        "quantity=?,unit=?,rate_per_unit=?,amount=?,vehicle_reg=?,purpose=?,ref_chapter=? "
        "WHERE id=?",
        (date, entry_type, given_to.strip(), category,
         float(quantity), unit, float(rate_per_unit),
         float(amount), vehicle_reg.strip(), purpose.strip(), ref_chapter, row_id)
    ); conn.commit(); conn.close()

def fuel_delete(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM fuel_cash_log WHERE id=?", (row_id,))
    conn.commit(); conn.close()

def fuel_totals(date_from=None, date_to=None):
    conn = get_connection()
    if date_from and date_to:
        extra = "AND date>=? AND date<=?"
        p = (date_from, date_to)
    else:
        extra = ""; p = ()
    def q(etype):
        r = conn.execute(
            f"SELECT COALESCE(SUM(amount),0) as t, COALESCE(SUM(quantity),0) as q "
            f"FROM fuel_cash_log WHERE entry_type=? {extra}", (etype,)+p
        ).fetchone()
        return float(r["t"] or 0), float(r["q"] or 0)
    diesel_amt, diesel_qty = q("Diesel")
    cash_amt,   cash_qty   = q("Cash")
    conn.close()
    return {"diesel_amount": diesel_amt, "diesel_litres": diesel_qty,
            "cash_amount":   cash_amt,   "cash_count":    cash_qty,
            "total":         diesel_amt + cash_amt}

def fuel_by_recipient(date_from=None, date_to=None):
    conn = get_connection()
    if date_from and date_to:
        rows = conn.execute(
            "SELECT given_to, entry_type, SUM(amount) as total, SUM(quantity) as qty, COUNT(*) as cnt "
            "FROM fuel_cash_log WHERE date>=? AND date<=? "
            "GROUP BY given_to, entry_type ORDER BY total DESC",
            (date_from, date_to)).fetchall()
    else:
        rows = conn.execute(
            "SELECT given_to, entry_type, SUM(amount) as total, SUM(quantity) as qty, COUNT(*) as cnt "
            "FROM fuel_cash_log "
            "GROUP BY given_to, entry_type ORDER BY total DESC").fetchall()
    conn.close(); return rows


# ══════════════════════════════════════════════════════════════
#  CH 8 — Land / Surface Rent
# ══════════════════════════════════════════════════════════════
def init_land_rent():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS land_rent (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_name    TEXT    NOT NULL,
            land_desc     TEXT    DEFAULT '',
            rent_from     TEXT    NOT NULL,
            rent_to       TEXT    NOT NULL,
            payment_date  TEXT    NOT NULL,
            amount        REAL    NOT NULL DEFAULT 0,
            payment_mode  TEXT    NOT NULL DEFAULT 'Cash',
            cheque_number TEXT    DEFAULT '',
            bank_name     TEXT    DEFAULT '',
            notes         TEXT    DEFAULT '',
            created_at    TEXT    DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit(); conn.close()

def land_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM land_rent ORDER BY payment_date DESC, id DESC"
    ).fetchall(); conn.close(); return rows

def land_get_range(date_from, date_to):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM land_rent "
        "WHERE payment_date>=? AND payment_date<=? "
        "ORDER BY payment_date DESC, id DESC",
        (date_from, date_to)
    ).fetchall(); conn.close(); return rows

def land_get_by_owner(owner_name):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM land_rent WHERE owner_name=? ORDER BY payment_date DESC",
        (owner_name,)
    ).fetchall(); conn.close(); return rows

def land_get_owners():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT owner_name FROM land_rent ORDER BY owner_name"
    ).fetchall(); conn.close(); return [r["owner_name"] for r in rows]

def land_add(owner_name, land_desc, rent_from, rent_to,
             payment_date, amount, payment_mode, cheque_number, bank_name, notes):
    conn = get_connection()
    conn.execute(
        "INSERT INTO land_rent "
        "(owner_name,land_desc,rent_from,rent_to,payment_date,"
        "amount,payment_mode,cheque_number,bank_name,notes) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (owner_name.strip(), land_desc.strip(), rent_from, rent_to,
         payment_date, float(amount), payment_mode,
         cheque_number.strip(), bank_name.strip(), notes.strip())
    ); conn.commit(); conn.close()

def land_edit(row_id, owner_name, land_desc, rent_from, rent_to,
              payment_date, amount, payment_mode, cheque_number, bank_name, notes):
    conn = get_connection()
    conn.execute(
        "UPDATE land_rent SET owner_name=?,land_desc=?,rent_from=?,rent_to=?,"
        "payment_date=?,amount=?,payment_mode=?,cheque_number=?,bank_name=?,notes=? "
        "WHERE id=?",
        (owner_name.strip(), land_desc.strip(), rent_from, rent_to,
         payment_date, float(amount), payment_mode,
         cheque_number.strip(), bank_name.strip(), notes.strip(), row_id)
    ); conn.commit(); conn.close()

def land_delete(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM land_rent WHERE id=?", (row_id,))
    conn.commit(); conn.close()

def land_total(date_from=None, date_to=None):
    conn = get_connection()
    if date_from and date_to:
        r = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as t FROM land_rent "
            "WHERE payment_date>=? AND payment_date<=?", (date_from, date_to)
        ).fetchone()
    else:
        r = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as t FROM land_rent"
        ).fetchone()
    conn.close(); return float(r["t"] or 0)

def land_filter_month(ym):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM land_rent WHERE payment_date LIKE ? ORDER BY payment_date ASC",
        (f"{ym}%",)
    ).fetchall(); conn.close(); return rows


# ══════════════════════════════════════════════════════════════
#  PEOPLE REGISTER  — individual ledger
# ══════════════════════════════════════════════════════════════
def init_people_register():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS people (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            phone        TEXT    DEFAULT '',
            category     TEXT    DEFAULT 'Other',
            notes        TEXT    DEFAULT '',
            created_at   TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS people_ledger (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id    INTEGER NOT NULL,
            date         TEXT    NOT NULL,
            entry_type   TEXT    NOT NULL DEFAULT 'Note',
            description  TEXT    DEFAULT '',
            cash_given   REAL    DEFAULT 0,
            cash_received REAL   DEFAULT 0,
            created_at   TEXT    DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (person_id) REFERENCES people(id)
        );
    """)
    conn.commit(); conn.close()

# ── People CRUD ───────────────────────────────────────────────
def people_get_all():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM people ORDER BY name ASC"
    ).fetchall(); conn.close(); return rows

def people_get_by_id(pid):
    conn = get_connection()
    r = conn.execute("SELECT * FROM people WHERE id=?", (pid,)).fetchone()
    conn.close(); return r

def people_add(name, phone, category, notes):
    conn = get_connection()
    conn.execute(
        "INSERT INTO people (name,phone,category,notes) VALUES (?,?,?,?)",
        (name.strip(), phone.strip(), category, notes.strip())
    ); conn.commit(); conn.close()

def people_edit(pid, name, phone, category, notes):
    conn = get_connection()
    conn.execute(
        "UPDATE people SET name=?,phone=?,category=?,notes=? WHERE id=?",
        (name.strip(), phone.strip(), category, notes.strip(), pid)
    ); conn.commit(); conn.close()

def people_delete(pid):
    conn = get_connection()
    conn.execute("DELETE FROM people_ledger WHERE person_id=?", (pid,))
    conn.execute("DELETE FROM people WHERE id=?", (pid,))
    conn.commit(); conn.close()

# ── Ledger CRUD ───────────────────────────────────────────────
def people_ledger_get(person_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM people_ledger WHERE person_id=? ORDER BY date ASC, id ASC",
        (person_id,)
    ).fetchall(); conn.close(); return rows

def people_ledger_add(person_id, date, entry_type, description, cash_given, cash_received):
    conn = get_connection()
    conn.execute(
        "INSERT INTO people_ledger "
        "(person_id,date,entry_type,description,cash_given,cash_received) "
        "VALUES (?,?,?,?,?,?)",
        (person_id, date, entry_type, description.strip(),
         float(cash_given), float(cash_received))
    ); conn.commit(); conn.close()

def people_ledger_edit(entry_id, date, entry_type, description, cash_given, cash_received):
    conn = get_connection()
    conn.execute(
        "UPDATE people_ledger SET date=?,entry_type=?,description=?,"
        "cash_given=?,cash_received=? WHERE id=?",
        (date, entry_type, description.strip(),
         float(cash_given), float(cash_received), entry_id)
    ); conn.commit(); conn.close()

def people_ledger_delete(entry_id):
    conn = get_connection()
    conn.execute("DELETE FROM people_ledger WHERE id=?", (entry_id,))
    conn.commit(); conn.close()

def people_ledger_summary(person_id):
    """Returns (total_given, total_received, net_balance)."""
    conn = get_connection()
    r = conn.execute(
        "SELECT COALESCE(SUM(cash_given),0) as tg, "
        "COALESCE(SUM(cash_received),0) as tr "
        "FROM people_ledger WHERE person_id=?",
        (person_id,)
    ).fetchone(); conn.close()
    given    = float(r["tg"] or 0)
    received = float(r["tr"] or 0)
    return given, received, given - received   # net > 0 = they owe us