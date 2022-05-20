#!/usr/bin/env python3
import sys

import logo
import util
from admin import Admin
from cashier import Cashier
from db_sqlite import Database
from hint import Hint
from login import Login, Roles
from style import init_style
from window import RootWindow


class MainWindow(RootWindow):
    def __init__(self):
        super().__init__("ATAC")
        logo.create_image()
        init_style()
        self._db = Database()
        self.create_widgets()

    def create_widgets(self):
        logo.get_label(self).pack()

        check_credentials = lambda l, p: Login.check_credentials(l, p, self.open_window)
        login_window = Login(
            self,
            [
                ("Зарегистрироваться", Login.register),
                ("Войти", check_credentials),
            ], self._db
        )
        login_window.pack()
        login_window.login.focus()
        login_window.password.bind(
            "<Return>", lambda _: login_window.buttons[1].invoke()
        )

        Hint(
            self,
            hint="Введите логин и пароль кассира или администратора либо зарегистрируйтесь.",
        ).pack()

        if len(sys.argv) >= 3:
            login_window.login.insert(0, sys.argv[1])
            login_window.password.insert(0, sys.argv[2])
            login_window.buttons[1].invoke()

    def open_window(self, role):
        if role == Roles.ADMIN:
            admin = Admin()
            util.set_close_handler(admin, lambda: self.close_handler(admin))
        else:
            cashier = Cashier()
            util.set_close_handler(cashier, lambda: self.close_handler(cashier))
        self.withdraw()

    def close_handler(self, win):
        win.destroy()
        self.deiconify()


def run():
    root = MainWindow()
    root.mainloop()


if __name__ == "__main__":
    run()
