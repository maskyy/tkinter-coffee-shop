import tkinter as _tk
import tkinter.ttk as _ttk

import logo
import util
from db_sqlite import Database
from login import Login, Roles
from style import Button, Entry
from tableview import TableView
from tabs import Tabs
from window import Window

__all__ = ["Cashier"]


class Cashier(Window):
    def __init__(self, is_admin=False):
        super().__init__("Касса")
        self._is_admin = is_admin
        self.db = Database()
        self.create_widgets()

    def create_widgets(self):
        logo.get_label(self).pack()

        tabs = Tabs(self)
        tabs_dict = {self.create_sales: "Продажа"}
        if self._is_admin:
            tabs_dict[self.create_returns] = "Возврат"
        tabs.populate(tabs_dict)

    def create_sales(self, master):
        frame = _ttk.Frame(master)

        frame.grid_columnconfigure(0, weight=2)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        _ttk.Label(frame, text="Товары").grid(column=0, row=0)
        self._check_text = _ttk.Label(frame)
        self._check_text.grid(column=1, row=0)
        self.update_check_id()

        goods_cols = [
            "ID",
            "Наименование",
            "Производитель",
            "Количество",
            "Цена",
            "Годен до",
            "Закупочная цена",
        ]
        self._goods_cols = display_columns = [
            c for c in goods_cols if c != "ID" and c != "Закупочная цена"
        ]
        self._goods = TableView(
            frame, self.db, "goods", goods_cols, self.on_good_select
        )
        self._goods.config(displaycolumns=display_columns)
        self._goods.grid(column=0, row=1, sticky="nsew", padx=20)
        self._goods.update_data()

        entry_frame = _ttk.Frame(frame)
        self.create_entries(entry_frame)
        entry_frame.grid(column=0, row=2)

        self._check = TableView(
            frame, columns=["Наименование", "Количество", "Стоимость"]
        )
        self._check.grid(column=1, row=1, sticky="nsew", padx=20)

        check_frame = _ttk.Frame(frame)
        check_frame.grid(column=1, row=2)

        self.create_confirm_window()

        self._check_sum = 0
        self._sum_label = _ttk.Label(check_frame, text="Сумма: 0")
        self._sum_label.pack(pady=5)
        Button(check_frame, text="Продать", command=self.on_sell).pack(pady=5)
        Button(check_frame, text="Вернуть", command=self.on_return).pack(pady=5)

        return frame

    def create_entries(self, master):
        _ttk.Label(master, text="Наименование").grid(column=0, row=0, padx=5)
        _ttk.Label(master, text="Количество").grid(column=0, row=1, padx=5)

        self._name = Entry(master)
        self._name.grid(column=1, row=0, padx=5, pady=5)
        self._amount = Entry(master)
        self._amount.grid(column=1, row=1, padx=5, pady=5)

        self.add = Button(master, text="Добавить", command=self.on_add_item)
        self.add.grid(column=0, row=2, columnspan=2, pady=5)

        self.create_search_window()
        Button(master, text="Поиск", command=self.toggle_search).grid(
            column=0, row=3, columnspan=3, pady=5
        )

        self._name.bind("<Return>", lambda _: self.add.invoke())
        self._amount.bind("<Return>", lambda _: self.add.invoke())

    def create_search_window(self):
        win = self._search_window = _tk.Toplevel(self)
        win.title("Поиск")
        last_row = self.create_search_entries(win)
        Button(win, text="Искать", command=self.on_search).grid(
            column=0, row=last_row, columnspan=2, pady=10
        )
        Button(win, text="Сбросить поиск", command=self.clear_search).grid(
            column=0, row=last_row + 1, columnspan=2, pady=10
        )
        self._hidden_items = []
        win.withdraw()

    def on_search(self):
        index = 1
        item = self._goods.get_children()[index]
        self._goods.detach(item)
        self._hidden_items.append((item, index))

    def clear_search(self):
        for item, index in self._hidden_items:
            self._goods.reattach(item, "", index)
        pass

    def create_search_entries(self, master):
        entries = []
        for i in range(len(self._goods_cols)):
            _ttk.Label(master, text=self._goods_cols[i], pad=5).grid(column=0, row=i)
            e = Entry(master)
            e.grid(column=1, row=i, padx=5, pady=5)
        return len(self._goods_cols)

    def toggle_search(self):
        if self._search_window.winfo_ismapped():
            self._search_window.withdraw()
            return
        self._search_window.deiconify()

    def create_returns(self, master):
        frame = _ttk.Frame(master)
        return frame

    def create_confirm_window(self):
        self.confirm_window = _tk.Toplevel(self)
        self.confirm_window.overrideredirect(True)
        self.confirm_return = Login(
            self.confirm_window,
            [
                (
                    "Подтвердить",
                    lambda d, l, p: Login.check_credentials(d, l, p, self.check_return),
                )
            ],
            self.db,
        )
        self.confirm_return.pack()
        self.confirm_window.withdraw()

    def find_row(self, table, name):
        for row in table.get_children():
            if name == table.item(row)["values"][1]:
                return row, table.item(row)["values"]
        return None, None

    def on_good_select(self, _, selected):
        self._name.delete(0, "end")
        self._amount.delete(0, "end")
        self._name.insert(0, selected["values"][1])
        self._amount.insert(0, 1)
        self._name.focus()

    def on_add_item(self):
        name, amount = self._name.get_strip(), self._amount.get_strip()
        if not name:
            return util.show_error("Введите наименование")

        row, values = self.find_row(self._goods, name)

        if not row:
            return util.show_error("Товар не найден")
        if not amount.isdigit() or int(amount) <= 0:
            return util.show_error("Количество должно быть целым положительным числом")
        amount = int(amount)
        if amount > values[3]:
            return util.show_error("Нельзя продать больше товаров, чем есть в наличии")

        self.change_by_amount(-amount, row)
        self.add_to_check(name, amount, row)
        self.update_check_sum()

        self._name.delete(0, "end")
        self._amount.delete(0, "end")

    def change_by_amount(self, amount, row):
        values = self._goods.item(row)["values"]
        values[3] += amount
        self._goods.item(row, values=values)

    def add_to_check(self, name, amount, row):
        cost = amount * self._goods.item(row)["values"][4]
        self._check.insert("", "end", values=(name, amount, cost))

    def on_sell(self):
        if len(self._check.get_children()) == 0:
            return util.show_error("В чеке нет товаров")

        self.db.add_check(self._check_id, self._check_sum)
        for row in self._check.get_children():
            data = (self._check_id, *self._check.item(row)["values"])
            self.db.sell_product(*data)

        self._check.clear()
        self.db.save()

        util.show_info("Чек №%d на сумму %d" % (self._check_id, self._check_sum))
        self.update_check_id()
        self.update_check_sum()

    def check_return(self, role):
        if role != Roles.ADMIN.value:
            return util.show_error("Введите логин и пароль администратора")
        self.do_return()
        self.confirm_window.withdraw()

    def on_return(self):
        if self.confirm_window.winfo_ismapped():
            self.confirm_window.withdraw()
            return
        if not self._check.selection():
            return util.show_error("Выберите товары для возврата")
        self.confirm_window.deiconify()
        util.center_window(self.confirm_window)

    def do_return(self):
        if not self._check.selection():
            return util.show_error("Выберите товары для возврата")

        for row in self._check.selection():
            values = self._check.item(row)["values"]
            _goods_row, _ = self.find_row(self._goods, values[0])
            self.change_by_amount(values[1], _goods_row)
            self._check.delete(row)

        self.update_check_sum()

    def update_check_id(self):
        self._check_id = self.db.get_new_check_id()
        self._check_text.config(text="Чек №%d" % self._check_id)

    def update_check_sum(self):
        result = 0
        for row in self._check.get_children():
            result += self._check.item(row)["values"][2]
        self._check_sum = result
        self._sum_label.config(text="Сумма: %d" % self._check_sum)


if __name__ == "__main__":
    root = _tk.Tk()
    root.withdraw()
    cashier = Cashier()
    util.set_close_handler(cashier, root.destroy)
    cashier.mainloop()
