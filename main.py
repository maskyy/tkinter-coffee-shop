#!/usr/bin/env python3
import sys

import cashier
import logo
import util
import style
import window
from db_sqlite import Database
from login import Login, Roles


class MainWindow(window.RootWindow):
    def __init__(self):
        super().__init__("Cinnabon")
        logo.create_image()
        style.init_style()
        self._db = Database()
        self.create_widgets()

    def create_widgets(self):
        logo.get_label(self).pack()

        check_credentials = lambda d, l, p: Login.check_credentials(
            d, l, p, self.open_window
        )
        login_window = Login(
            self,
            [
                ("Зарегистрироваться", Login.register),
                ("Войти", check_credentials),
            ],
            self._db,
        )
        login_window.pack()
        login_window.login.focus()
        login_window.password.bind(
            "<Return>", lambda _: login_window.buttons[1].invoke()
        )

        if len(sys.argv) >= 3:
            login_window.login.insert(0, sys.argv[1])
            login_window.password.insert(0, sys.argv[2])
            login_window.buttons[1].invoke()

    def open_window(self, role):
        win = cashier.Cashier(role == Roles.ADMIN.value)
        util.set_close_handler(win, lambda: self.close_handler(win))
        self.withdraw()

    def close_handler(self, win):
        win.destroy()
        self.deiconify()


def run():
    root = MainWindow()
    root.mainloop()


if __name__ == "__main__":
    run()
