import os
import pickle
import bcrypt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
KEY_FILE = os.path.join(CONFIG_DIR, 'secret.key')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'admin_config.enc')

MAX_LOGIN_ATTEMPTS = 99
LOCKOUT_DURATION = timedelta(minutes=15)

# Khóa Fernet
def load_key():
    if not os.path.exists(KEY_FILE):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        os.chmod(KEY_FILE, 0o600)
    else:
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
    return key

cipher = Fernet(load_key())

# Mã hóa
def save_admin_config(config: dict):
    raw = pickle.dumps(config)
    data = cipher.encrypt(raw)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'wb') as f:
        f.write(data)
    os.chmod(CONFIG_FILE, 0o600)

# Giải mã
def load_admin_config():
    if not os.path.exists(CONFIG_FILE):
        default = {
            'password': bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()),
            'attempts': 0,
            'lockout_time': None
        }
        save_admin_config(default)
        return default
    try:
        with open(CONFIG_FILE, 'rb') as f:
            enc = f.read()
        raw = cipher.decrypt(enc)
        config = pickle.loads(raw)
        return config
    except Exception as e:
        print(f"Lỗi giải mã admin config: {e}")
        os.remove(CONFIG_FILE)
        return load_admin_config()

# Login function
def login():
    config = load_admin_config()
    now = datetime.now()
    lock_time = config.get('lockout_time')
    if lock_time and now < lock_time:
        remaining = int((lock_time - now).total_seconds() // 60)
        from tkinter import messagebox
        messagebox.showerror('Tài khoản bị khóa', f'Bạn bị khóa. Thử lại sau {remaining} phút.')
        return False

    from tkinter.simpledialog import askstring
    from tkinter import messagebox
    pwd = askstring('Đăng nhập', 'Nhập mật khẩu admin:', show='*')
    if not pwd or not bcrypt.checkpw(pwd.encode(), config['password']):
        # wrong password
        config['attempts'] = config.get('attempts', 0) + 1
        if config['attempts'] >= MAX_LOGIN_ATTEMPTS:
            config['lockout_time'] = now + LOCKOUT_DURATION
        save_admin_config(config)
        remaining = max(0, MAX_LOGIN_ATTEMPTS - config['attempts'])
        messagebox.showerror('Sai mật khẩu', f'Sai mật khẩu. Còn {remaining} lần.')
        return False

    # correct password
    config['attempts'] = 0
    config['lockout_time'] = None
    save_admin_config(config)
    return True
