import enum as _enum
import functools as _ft
import tkinter.messagebox as _msg
import tkinter.ttk as _ttk

import style
import util

__all__ = ["Roles", "Login"]


class Roles(_enum.Enum):
    ADMIN = "admin"
    CASHIER = "cashier"


class Login(_ttk.Frame):
    def register(login, password):
        login, password = login.get_strip(), password.get_strip()
        if not login or not password:
            return util.show_error("Введите логин и пароль")
        if login in _credentials:
            return util.show_error("Логин уже занят")

        answer = _msg.askquestion("Роль", "Да - администратор, нет - кассир")
        role = Roles.ADMIN if answer == "yes" else Roles.CASHIER
        _credentials[login] = (password, role)
        _msg.showinfo("Регистрация", "Регистрация успешна")
        return True

    def check_credentials(login_entry, password_entry, handler):
        login, password = login_entry.get_strip(), password_entry.get_strip()
        if not login or not password:
            return util.show_error("Введите логин и пароль")
        if login not in _credentials:
            return util.show_error("Логин не существует")

        password2, role = _credentials[login]
        if password != password2:
            return util.show_error("Неверный пароль")

        handler(role)
        login_entry.delete(0, "end")
        password_entry.delete(0, "end")
        return True

    def __init__(self, master=None, actions=None, db=None):
        super().__init__(master)
        self._db = db
        self.read_credentials()
        self.create_widgets(actions)

    def read_credentials(self):
        logins = self._db.get_table("logins")
        print(logins)
        pass

    def create_widgets(self, actions):
        _ttk.Label(self, text="Логин").pack()
        self.login = login = style.Entry(self)
        login.pack(pady=5)

        _ttk.Label(self, text="Пароль").pack()
        self.password = password = style.Entry(self, show="*")
        password.pack(pady=5)

        self.buttons = []
        for name, action in actions:
            btn = style.Button(
                self, text=name, command=_ft.partial(action, login, password), width=20
            )
            btn.pack(pady=5)
            self.buttons.append(btn)
