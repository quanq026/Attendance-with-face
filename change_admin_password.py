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
    enc = cipher.encrypt(raw)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'wb') as f:
        f.write(enc)
    os.chmod(CONFIG_FILE, 0o600)

# Giai mã
def load_admin_config():
    if not os.path.exists(CONFIG_FILE):
        # Tạo config mặc định
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
        return pickle.loads(raw)
    except Exception:
        # Mã hóa lỗi -> xóa và tạo lại
        os.remove(CONFIG_FILE)
        return load_admin_config()

# Change admin password
def change_admin_password(new_password: str) -> str:
    if not new_password:
        return 'Lỗi: Mật khẩu không được để trống.'

    # Tạo config mới với mật khẩu mới
    config = {
        'password': bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()),
        'attempts': 0,
        'lockout_time': None
    }
    save_admin_config(config)
    return 'Đã cập nhật mật khẩu admin.'

if __name__ == '__main__':
    pwd = input('Nhập mật khẩu admin mới: ')
    print(change_admin_password(pwd))
