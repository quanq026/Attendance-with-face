"""
Script đọc và hiển thị danh sách nhân viên cùng lịch sử log chấm công.
Sử dụng các hàm trong utils.py để giải mã và tải dữ liệu.
"""

import os
import sys
from utils import load_encodings, load_logs_to_dataframe


def main():
    # Đảm bảo chạy đúng thư mục chứa database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    os.chdir(BASE_DIR)

    # Nạp danh sách nhân viên (đã giải mã)
    employees = load_encodings()
    if not employees:
        print("Chưa có nhân viên nào.")
    else:
        print("Danh sách nhân viên:")
        for emp_id, info in employees.items():
            name = info.get('name', '')
            dob = info.get('dob', '')
            print(f"- ID: {emp_id}\tTên: {name}\tNgày sinh: {dob}")

    print("\nLịch sử chấm công:")
    # Nạp log chấm công thành DataFrame
    df = load_logs_to_dataframe()
    if df.empty:
        print("Chưa có bản ghi chấm công nào.")
    else:
        # Hiển thị toàn bộ log
        # df có hai cột: ID, Thời gian
        for _, row in df.iterrows():
            emp_id = str(row['ID']).strip()
            timestamp = row['Thời gian'].strftime('%d/%m/%Y %H:%M:%S')
            print(f"- ID: {emp_id}\tThời gian: {timestamp}")


if __name__ == '__main__':
    main()