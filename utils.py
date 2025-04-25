import os
import pickle
import csv
import io
from datetime import datetime
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from cryptography.fernet import Fernet

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
KEY_FILE = os.path.join(CONFIG_DIR, "secret.key")
DB_DIR = os.path.join(BASE_DIR, "database")
EMP_FILE = os.path.join(DB_DIR, "employees.pkl")
CSV_FILE = os.path.join(DB_DIR, "employees.csv")
LOG_FILE = os.path.join(DB_DIR, "logs.csv")

def load_key():
    if not os.path.exists(KEY_FILE):
        os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        os.chmod(KEY_FILE, 0o600)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key

cipher = Fernet(load_key())

# Hàm mã hóa file

def encrypt_file(path: str):
    with open(path, "rb") as f:
        data = f.read()
    enc = cipher.encrypt(data)
    with open(path, "wb") as f:
        f.write(enc)
    os.chmod(path, 0o600)

# --- Nhân viên ---

def save_encodings(data: dict):
    raw = pickle.dumps(data)
    enc = cipher.encrypt(raw)
    os.makedirs(os.path.dirname(EMP_FILE), exist_ok=True)
    with open(EMP_FILE, "wb") as f:
        f.write(enc)
    os.chmod(EMP_FILE, 0o600)


def load_encodings() -> dict:
    if not os.path.exists(EMP_FILE):
        return {}
    try:
        with open(EMP_FILE, "rb") as f:
            enc = f.read()
        raw = cipher.decrypt(enc)
        return pickle.loads(raw)
    except Exception as e:
        print("Lỗi khi giải mã data nhân viên:", e)
        return {}


def save_employee_list():
    data = load_encodings()
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "Tên", "Ngày sinh"])
    for eid, info in data.items():
        writer.writerow([eid, info.get("name", ""), info.get("dob", "")])
    enc = cipher.encrypt(buf.getvalue().encode("utf-8"))
    with open(CSV_FILE, "wb") as f:
        f.write(enc)
    os.chmod(CSV_FILE, 0o600)


def get_all_employees() -> list:
    return list(load_encodings().keys())


def get_employee_name(emp_id: str) -> str:
    return load_encodings().get(emp_id, {}).get("name", "")


def get_employee_dob(emp_id: str) -> str:
    return load_encodings().get(emp_id, {}).get("dob", "")

# --- Log chấm công ---

def save_log(emp_id: str, timestamp: str):
    lines = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "rb") as f:
                enc = f.read()
            text = cipher.decrypt(enc).decode("utf-8")
            lines = text.splitlines()
        except:
            lines = ["ID,Thời gian"]
    else:
        lines = ["ID,Thời gian"]
    lines.append(f"{emp_id},{timestamp}")
    text_new = "\n".join(lines)
    enc_new = cipher.encrypt(text_new.encode("utf-8"))
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "wb") as f:
        f.write(enc_new)
    os.chmod(LOG_FILE, 0o600)


def load_logs_to_dataframe() -> pd.DataFrame:
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame(columns=["ID", "Thời gian"])
    try:
        with open(LOG_FILE, "rb") as f:
            enc = f.read()
        text = cipher.decrypt(enc).decode("utf-8")
        # Đọc với dtype ID là str để giữ nguyên leading zeros
        df = pd.read_csv(io.StringIO(text), dtype={"ID": str}, parse_dates=["Thời gian"], dayfirst=True)
        return df
    except Exception as e:
        print("Lỗi khi nạp log:", e)
        return pd.DataFrame(columns=["ID", "Thời gian"])


def has_attended_today(emp_id: str) -> bool:
    df = load_logs_to_dataframe()
    today = datetime.now().date()
    return any((str(r["ID"]).strip() == emp_id and r["Thời gian"].date() == today) for _, r in df.iterrows())


def has_attended_on_date(emp_id: str, date_str: str) -> bool:
    df = load_logs_to_dataframe()
    try:
        target = datetime.strptime(date_str, "%d/%m/%Y").date()
    except:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    return any((str(r["ID"]).strip() == emp_id and r["Thời gian"].date() == target) for _, r in df.iterrows())


def get_attendance_summary() -> dict:
    emps = get_all_employees()
    attended = [eid for eid in emps if has_attended_today(eid)]
    not_attended = [eid for eid in emps if eid not in attended]
    return {
        "total_employees": len(emps),
        "attended_count": len(attended),
        "not_attended_count": len(not_attended),
        "attended_list": attended,
        "not_attended_list": not_attended
    }

# --- Hỗ trợ UI ---

def popup(title: str, message: str):
    win = tk.Tk()
    win.withdraw()
    win.attributes("-topmost", True)
    messagebox.showinfo(title, message, parent=win)
    win.destroy()
