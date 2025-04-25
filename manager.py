import os
import pickle
from tkinter import Toplevel, Listbox, Button, messagebox, filedialog, Frame, simpledialog
import pandas as pd
from utils import load_encodings, save_encodings, save_employee_list, load_logs_to_dataframe
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, 'database')
FACES_DIR = os.path.join(DB_DIR, 'faces')
LOG_FILE = os.path.join(DB_DIR, 'logs.csv')

# Giao diện quản lý nhân viên
def manage_employees():
    window = Toplevel()
    window.title("Quản lý nhân viên")
    window.geometry("500x500")

    main_frame = Frame(window)
    main_frame.pack(pady=10, fill='both', expand=True)

    listbox = Listbox(main_frame, width=50)
    listbox.pack(pady=10, fill='both', expand=True)

    btn_frame = Frame(main_frame)
    btn_frame.pack(pady=5)

    def refresh_list():
        listbox.delete(0, 'end')
        data = load_encodings()
        for eid, info in data.items():
            name = info.get('name', '')
            dob = info.get('dob', '')
            listbox.insert('end', f"{eid} - {name} - DOB: {dob or 'Chưa có'}")

    def delete_employee():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Chọn nhân viên", "Hãy chọn nhân viên cần xóa.")
            return
        eid = listbox.get(sel[0]).split(' - ')[0]
        if messagebox.askyesno("Xác nhận", f"Xóa nhân viên {eid}? "):
            data = load_encodings()
            if eid in data:
                del data[eid]
                save_encodings(data)
                save_employee_list()
                img = os.path.join(FACES_DIR, f"{eid}.jpg")
                if os.path.exists(img): os.remove(img)
                refresh_list()
                messagebox.showinfo("Thành công", f"Đã xóa {eid}.")
            else:
                messagebox.showerror("Lỗi", f"ID {eid} không tồn tại.")

    def rename_employee():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Chọn nhân viên", "Hãy chọn nhân viên cần đổi tên.")
            return
        eid = listbox.get(sel[0]).split(' - ')[0]
        new_name = simpledialog.askstring("Đổi tên", "Nhập tên mới:")
        if new_name:
            data = load_encodings()
            if eid in data:
                data[eid]['name'] = new_name
                save_encodings(data)
                save_employee_list()
                refresh_list()
                messagebox.showinfo("Thành công", "Đã đổi tên.")

    def change_dob():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Chọn nhân viên", "Hãy chọn nhân viên cần đổi DOB.")
            return
        eid = listbox.get(sel[0]).split(' - ')[0]
        new_dob = simpledialog.askstring("Đổi DOB", "Nhập DOB (DD/MM/YYYY):")
        try:
            pd.to_datetime(new_dob, dayfirst=True)
        except:
            messagebox.showerror("Lỗi", "Định dạng DOB không hợp lệ.")
            return
        data = load_encodings()
        if eid in data:
            data[eid]['dob'] = new_dob
            save_encodings(data)
            save_employee_list()
            refresh_list()
            messagebox.showinfo("Thành công", "Đã cập nhật DOB.")

    # Nút
    Button(btn_frame, text="Xóa", command=delete_employee).pack(side='left', padx=5)
    Button(btn_frame, text="Đổi tên", command=rename_employee).pack(side='left', padx=5)
    Button(btn_frame, text="Đổi DOB", command=change_dob).pack(side='left', padx=5)
    Button(btn_frame, text="Làm mới", command=refresh_list).pack(side='left', padx=5)
    Button(btn_frame, text="Đóng", command=window.destroy).pack(side='right', padx=5)

    refresh_list()

# Xuất và xóa log chấm công
def export_logs():
    df = load_logs_to_dataframe()
    if df.empty:
        messagebox.showwarning("Không có log", "Chưa có dữ liệu chấm công.")
        return
    path = filedialog.asksaveasfilename(
        title="Lưu log chấm công",
        defaultextension=".xlsx",
        filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")]
    )
    if path:
        if path.endswith('.xlsx'):
            df.to_excel(path, index=False)
        else:
            df.to_csv(path, index=False)
        messagebox.showinfo("Thành công", f"Đã lưu log tới {path}.")


def clear_logs():
    if not os.path.exists(LOG_FILE):
        messagebox.showwarning("Không có log", "Chưa có file log.")
        return
    if messagebox.askyesno("Xác nhận", "Xóa toàn bộ log chấm công?"):
        os.remove(LOG_FILE)
        messagebox.showinfo("Đã xóa", "Log chấm công đã được xóa.")
        
def export_employees():
    data = load_encodings()
    if not data:
        messagebox.showwarning("Không có nhân viên", "Chưa có dữ liệu nhân viên.")
        return
    # Chọn đường dẫn lưu
    path = filedialog.asksaveasfilename(
        title="Lưu danh sách nhân viên",
        defaultextension=".xlsx",
        filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")]
    )
    if not path:
        return
    # Tạo DataFrame rồi xuất
    df = pd.DataFrame([
        {"ID": eid, "Tên": info.get("name", ""), "Ngày sinh": info.get("dob", "")}
        for eid, info in data.items()
    ])
    if path.lower().endswith('.xlsx'):
        df.to_excel(path, index=False)
    else:
        df.to_csv(path, index=False)
    messagebox.showinfo("Thành công", f"Đã lưu danh sách nhân viên tới {path}.")
