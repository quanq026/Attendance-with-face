import os
import sys
import bcrypt
import tkinter as tk
from tkinter import messagebox, Toplevel, Label, Entry
import admin as admin_mod
from register_employee import register
from recognize import recognize_face
import manager
from change_admin_password import change_admin_password
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import ttkbootstrap.style as style
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
os.chdir(BASE_DIR)

window = ttk.Window(themename="darkly")
window.title("Phần mềm chấm công")
window.geometry("500x650")
window.resizable(False, False)

# style config
style.Style().configure("TButton", font=("Arial", 12), padding=10)
style.Style().configure("PRIMARY.TButton", background="#268BD2", foreground="white")
style.Style().configure("SUCCESS.TButton", background="#2AA198", foreground="white")
style.Style().configure("INFO.TButton", background="#B58900", foreground="white")
style.Style().configure("DANGER.TButton", background="#DC322F", foreground="white")
style.Style().configure("SECONDARY.TButton", background="#073642", foreground="white")
style.Style().configure("TLabel", font=("Arial", 14), foreground="#93A1A1", background="#002B36")
style.Style().configure("TFrame", background="#002B36")
style.Style().configure("Message.TLabel", font=("Arial", 12), foreground="white", background="#2AA198", padding=10)
style.Style().configure("CYAN.TButton", background="#00b2b2", foreground="white")

# Main container
main_container = ttk.Frame(window, padding=20, style="TFrame")
main_container.pack(fill=BOTH, expand=True)

# Hiển thị tin nhắn tạm thời
def show_message(parent, text, style_name="Message.TLabel", duration=3000):
    frame = ttk.Frame(parent, style="TFrame")
    frame.pack(fill=X, pady=5)
    label = ttk.Label(frame, text=text, style=style_name, anchor="center")
    label.pack(fill=X, padx=10)
    parent.after(duration, frame.destroy)

# Tiêu đề app
title_label = ttk.Label(
    main_container,
    text="Phần mềm chấm công",
    font=("Arial", 24, "bold"),
    style="TLabel"
)
title_label.pack(pady=20)

# Frame chính và frame admin
main_frame = ttk.Frame(main_container, style="TFrame")
main_frame.pack(pady=20, fill=X)
admin_frame = ttk.Frame(main_container, style="TFrame")
login_btn = None

def show_admin_buttons():
    if admin_mod.login():
        login_btn.pack_forget()
        admin_frame.pack(pady=10, fill=X)

def logout_admin():
    admin_frame.pack_forget()
    login_btn.pack(pady=10)
    show_message(main_container, "Đã đăng xuất khỏi admin.")

def open_manager():
    manager.manage_employees()

def change_password_ui():
    dialog = Toplevel(window)
    dialog.title('Đổi mật khẩu admin')
    dialog.geometry('350x320')
    dialog.resizable(False, False)

    frame = ttk.Frame(dialog, padding=20, style="TFrame")
    frame.pack(fill=BOTH, expand=True)

    # Trường nhập mật khẩu hiện tại
    ttk.Label(frame, text='Mật khẩu hiện tại:', style="TLabel").pack(anchor='w')
    current_var = tk.StringVar()
    Entry(frame, textvariable=current_var, show='*', font=("Arial",12)).pack(fill=X, pady=5)

    # Trường nhập mật khẩu mới
    ttk.Label(frame, text='Mật khẩu mới:', style="TLabel").pack(anchor='w')
    new_var = tk.StringVar()
    Entry(frame, textvariable=new_var, show='*', font=("Arial",12)).pack(fill=X, pady=5)

    # Trường xác nhận mật khẩu
    ttk.Label(frame, text='Xác nhận mật khẩu mới:', style="TLabel").pack(anchor='w')
    confirm_var = tk.StringVar()
    Entry(frame, textvariable=confirm_var, show='*', font=("Arial",12)).pack(fill=X, pady=5)

    def on_submit():
        current = current_var.get().strip()
        new = new_var.get().strip()
        confirm = confirm_var.get().strip()
        if not current or not new or not confirm:
            messagebox.showerror('Lỗi', 'Vui lòng nhập đủ thông tin.', parent=dialog)
            return
        cfg = admin_mod.load_admin_config()
        if not bcrypt.checkpw(current.encode(), cfg.get('password', b'')):
            messagebox.showerror('Lỗi', 'Mật khẩu hiện tại không đúng.', parent=dialog)
            return
        if new != confirm:
            messagebox.showerror('Lỗi', 'Mật khẩu mới không khớp.', parent=dialog)
            return
        msg = change_admin_password(new)
        show_message(main_container, msg)
        dialog.destroy()

    btn_frame = ttk.Frame(frame, style="TFrame")
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text='Đổi mật khẩu', command=on_submit, style="PRIMARY.TButton").pack(side=LEFT, padx=5)
    ttk.Button(btn_frame, text='Hủy', command=dialog.destroy, style="DANGER.TButton").pack(side=LEFT, padx=5)

    dialog.transient(window)
    dialog.grab_set()
    dialog.wait_window()

# Nút
def create_btn(parent, text, cmd, style_name=PRIMARY):
    btn = ttk.Button(parent, text=text, command=cmd, style=f"{style_name}.TButton", width=25)
    btn.bind('<Enter>', lambda e: btn.configure(style=f"{style_name}.TButton"))
    btn.bind('<Leave>', lambda e: btn.configure(style=f"{style_name}.TButton"))
    return btn

# Nút chính
create_btn(main_frame, 'Chấm công', recognize_face, SUCCESS).pack(pady=10)
login_btn = create_btn(main_frame, 'Admin login', show_admin_buttons, PRIMARY)
login_btn.pack(pady=10)

# Nút admin
create_btn(admin_frame, 'Đăng ký nhân viên', register, INFO).pack(pady=10)
create_btn(admin_frame, 'Quản lý nhân viên', open_manager, INFO).pack(pady=10)
create_btn(admin_frame, 'Xuất log chấm công', manager.export_logs, "CYAN").pack(pady=10)
create_btn(admin_frame, 'Xuất danh sách nhân viên', manager.export_employees, "CYAN").pack(pady=10)
create_btn(admin_frame, 'Đổi mật khẩu admin', change_password_ui, INFO).pack(pady=10)
create_btn(admin_frame, 'Đăng xuất', logout_admin, SECONDARY).pack(pady=10)

# Hiệu ứng fade in
def fade_in(step=0):
    alpha = step/10
    window.attributes('-alpha', alpha)
    if step<10:
        window.after(50, fade_in, step+1)

window.attributes('-alpha', 0)
fade_in()

# Chạy giao diện
window.mainloop()