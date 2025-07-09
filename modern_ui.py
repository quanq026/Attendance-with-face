import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

import admin as admin_mod
from register_employee import register
from recognize import recognize_face
import manager
from change_admin_password import change_admin_password


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attendance System")
        self.resize(400, 500)
        self.logged_in = False
        self._build_ui()

    def _build_ui(self):
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Phần mềm chấm công")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size:24px;font-weight:bold")
        self.layout.addWidget(self.title)

        self.message = QLabel("")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.message)

        btn_check = QPushButton("Chấm công")
        btn_check.clicked.connect(recognize_face)
        self.layout.addWidget(btn_check)

        self.btn_login = QPushButton("Admin login")
        self.btn_login.clicked.connect(self.login)
        self.layout.addWidget(self.btn_login)

        # admin buttons
        self.admin_buttons = []
        self.add_admin_button("Đăng ký nhân viên", register)
        self.add_admin_button("Quản lý nhân viên", manager.manage_employees)
        self.add_admin_button("Xuất log chấm công", manager.export_logs)
        self.add_admin_button("Xuất danh sách nhân viên", manager.export_employees)
        self.add_admin_button("Đổi mật khẩu admin", self.change_password)
        self.add_admin_button("Đăng xuất", self.logout)

    def add_admin_button(self, text, func):
        b = QPushButton(text)
        b.clicked.connect(func)
        b.setVisible(False)
        self.layout.addWidget(b)
        self.admin_buttons.append(b)

    def show_message(self, text, timeout=3000):
        self.message.setText(text)
        if timeout:
            QTimer.singleShot(timeout, lambda: self.message.setText(""))

    def login(self):
        config = admin_mod.load_admin_config()
        lock_time = config.get('lockout_time')
        if lock_time:
            QMessageBox.warning(self, "Bị khóa", "Tài khoản bị khóa. Thử lại sau.")
            return
        pwd, ok = QInputDialog.getText(self, "Đăng nhập", "Mật khẩu:", echo=QInputDialog.EchoMode.Password)
        if not ok:
            return
        if not pwd or not admin_mod.bcrypt.checkpw(pwd.encode(), config['password']):
            config['attempts'] = config.get('attempts', 0) + 1
            if config['attempts'] >= admin_mod.MAX_LOGIN_ATTEMPTS:
                config['lockout_time'] = admin_mod.datetime.now() + admin_mod.LOCKOUT_DURATION
            admin_mod.save_admin_config(config)
            remaining = max(0, admin_mod.MAX_LOGIN_ATTEMPTS - config['attempts'])
            QMessageBox.critical(self, "Sai mật khẩu", f"Sai mật khẩu. Còn {remaining} lần.")
            return
        config['attempts'] = 0
        config['lockout_time'] = None
        admin_mod.save_admin_config(config)
        self.logged_in = True
        self.btn_login.setVisible(False)
        for b in self.admin_buttons:
            b.setVisible(True)
        self.show_message("Đăng nhập thành công")

    def logout(self):
        self.logged_in = False
        for b in self.admin_buttons:
            b.setVisible(False)
        self.btn_login.setVisible(True)
        self.show_message("Đã đăng xuất")

    def change_password(self):
        new, ok = QInputDialog.getText(self, "Đổi mật khẩu", "Mật khẩu mới:", echo=QInputDialog.EchoMode.Password)
        if not ok or not new:
            return
        confirm, ok = QInputDialog.getText(self, "Xác nhận", "Nhập lại mật khẩu:", echo=QInputDialog.EchoMode.Password)
        if not ok or new != confirm:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu không khớp")
            return
        msg = change_admin_password(new)
        QMessageBox.information(self, "", msg)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
