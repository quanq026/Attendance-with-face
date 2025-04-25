import os
import cv2
import face_recognition
import tkinter as tk
from tkinter import Toplevel, Label, Entry, Button, simpledialog, messagebox
from datetime import datetime
from utils import (
    load_encodings,
    save_encodings,
    save_employee_list,
    popup,
    encrypt_file
)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, 'database')
FACES_DIR = os.path.join(DB_DIR, 'faces')

def generate_new_id():
    data = load_encodings()
    used = set(data.keys())
    n = 1
    while True:
        sid = str(n).zfill(5)
        if sid not in used:
            return sid
        n += 1

def register():
    dialog = Toplevel()
    dialog.title('Đăng ký nhân viên')
    dialog.geometry('300x300')
    dialog.resizable(False, False)

    Label(dialog, text='Tên:', font=('Arial', 12)).pack(pady=5)
    name_var = tk.StringVar()
    Entry(dialog, textvariable=name_var, font=('Arial', 12)).pack(pady=5)

    Label(dialog, text='Ngày sinh (DD/MM/YYYY):', font=('Arial', 12)).pack(pady=5)
    dob_var = tk.StringVar()
    Entry(dialog, textvariable=dob_var, font=('Arial', 12)).pack(pady=5)

    def on_submit():
        name = name_var.get().strip()
        dob = dob_var.get().strip()
        if not name or not dob:
            messagebox.showerror('Lỗi', 'Vui lòng nhập đủ thông tin', parent=dialog)
            return
        try:
            datetime.strptime(dob, '%d/%m/%Y')
        except:
            messagebox.showerror('Lỗi', 'Định dạng ngày sinh không hợp lệ', parent=dialog)
            return
        dialog.user = {'name': name, 'dob': dob}
        dialog.destroy()

    Button(dialog, text='OK', command=on_submit, font=('Arial', 12)).pack(pady=20)
    dialog.transient()
    dialog.grab_set()
    dialog.wait_window()

    if not hasattr(dialog, 'user'):
        return
    name = dialog.user['name']
    dob = dialog.user['dob']
    emp_id = generate_new_id()

    popup('Hướng dẫn', "Đưa khuôn mặt vào khung, ấn 's' để chụp, 'q' để hủy.")
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        popup('Lỗi', 'Không thể mở camera')
        return

    cv2.namedWindow('Register Face', cv2.WINDOW_NORMAL)
    while True:
        ret, frame = cam.read()
        if not ret:
            popup('Lỗi', 'Không nhận được hình ảnh từ camera')
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb)
        cv2.imshow('Register Face', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            if not faces:
                popup('Cảnh báo', 'Không phát hiện khuôn mặt. Thử lại.')
                continue
            encs = face_recognition.face_encodings(rgb, faces)
            if not encs:
                popup('Cảnh báo', 'Không mã hóa được khuôn mặt. Thử lại.')
                continue
            # Tạo thư mục lưu ảnh
            os.makedirs(FACES_DIR, exist_ok=True)
            file_path = os.path.join(FACES_DIR, f'{emp_id}.jpg')
            cv2.imwrite(file_path, frame)
            # Mã hóa ảnh
            encrypt_file(file_path)
            # Lưu encoding và thông tin
            data = load_encodings()
            data[emp_id] = {'name': name, 'dob': dob, 'encoding': encs[0].tolist()}
            save_encodings(data)
            save_employee_list()
            new_emp_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'new_employees.txt')
            with open(new_emp_path, 'a', encoding='utf-8') as f:
                f.write(f"{name}\n")
            popup('Thành công', f'Đã đăng ký {name} (ID: {emp_id})')
            break
        elif key == ord('q') or cv2.getWindowProperty('Register Face', cv2.WND_PROP_VISIBLE) < 1:
            break

    cam.release()
    cv2.destroyAllWindows()
