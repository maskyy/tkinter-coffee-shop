import tkinter as _tk
import tkinter.messagebox as _msg
import tkinter.ttk as _ttk

import dates
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
        frame.grid_rowconfigure(1, weight=2)
        frame.grid_rowconfigure(2, weight=1)

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
            "Бонусы",
        ]
        self._goods_cols = display_columns = [
            c for c in goods_cols if c not in ["ID", "Закупочная цена", "Бонусы"]
        ]
        self._goods = TableView(
            frame, self.db, "goods", goods_cols, self.on_good_select
        )
        self._goods.config(displaycolumns=display_columns)
        self._goods.grid(column=0, row=1, sticky="nsew", padx=20)
        self._goods.update_data()

        self._sell_frame = _ttk.Frame(frame)
        self.create_entries(self._sell_frame)
        self._sell_frame.grid(column=0, row=2)

        self._check = TableView(
            frame, columns=["Наименование", "Количество", "Стоимость"]
        )
        self._check.grid(column=1, row=1, sticky="nsew", padx=20)

        check_frame = _ttk.Frame(frame)
        check_frame.grid(column=1, row=2)

        self.create_search_frame(frame)
        self.create_confirm_window()

        self._check_sum = 0
        self._sum_label = _ttk.Label(check_frame, text="Сумма: 0")
        self._sum_label.pack(pady=5)
        Button(check_frame, text="Продать", command=self.on_sell).pack(pady=5)
        Button(check_frame, text="Вернуть", command=self.on_return).pack(pady=5)
        _ttk.Label(check_frame, text="Код клиента").pack()
        self._client_code = Entry(check_frame)
        self._client_code.pack()

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

        Button(master, text="Поиск", command=self.toggle_search).grid(
            column=0, row=3, columnspan=3, pady=5
        )

        self._name.bind("<Return>", lambda _: self.add.invoke())
        self._amount.bind("<Return>", lambda _: self.add.invoke())

    def create_search_frame(self, master):
        frame = self._search_frame = _ttk.Frame(master)
        last_row = self.create_search_entries(frame)
        Button(frame, text="Искать", command=self.on_search).grid(
            column=0, row=last_row, columnspan=2, pady=10
        )
        Button(frame, text="Сбросить поиск", command=self.clear_search).grid(
            column=0, row=last_row + 1, columnspan=2, pady=10
        )
        self._hidden_items = []

    def is_number_valid(self, value):
        return value.isdigit() and int(value) >= 0

    def validate_search(self):
        amount, price, use_by = [e.get_strip() for e in self._search_entries[2:]]
        if amount and amount[0] in "<>" and len(amount) > 1:
            amount = amount[1:]
        if price and price[0] in "<>" and len(price) > 1:
            price = price[1:]
        if use_by and use_by[0] in "<>" and len(use_by) > 1:
            use_by = use_by[1:]

        if amount and (not amount.isdigit() or int(amount) < 0):
            return util.show_error(
                "Количество должно быть целым неотрицательным числом"
            )
        if price and not self.is_number_valid(price):
            return util.show_error("Цена должна быть целым неотрицательным числом")
        if use_by and not dates.to_date(use_by):
            return util.show_error("Введите дату (ГГГГ-ММ-ДД)")
        return True

    def _compare_values(self, x, value, operator, type_):
        if type_ == "num":
            x = int(x)
        elif type_ == "date":
            x = dates.to_date(x)

        if operator == ">":
            return x > value
        elif operator == "<":
            return x < value
        return x == value

    def on_search(self):
        if not self.validate_search():
            return

        items_to_keep = list(self._goods.get_children())

        # search filters
        for i in range(len(self._search_entries)):
            text = self._search_entries[i].get_strip()
            if not text:
                continue
            if i < 2:  # name and manufacturer
                comparer = lambda x: text.lower() in x.lower()
            else:  # numbers (>, <, =)
                operator = "="
                if text[0] in "<>":
                    operator = text[0]
                    text = text[1:]
                if i == 4:
                    value = dates.to_date(text)
                else:
                    value = int(text)
                comparer = lambda x: self._compare_values(
                    x, value, operator, "date" if i == 4 else "num"
                )
            items_to_keep = list(
                filter(
                    lambda row: comparer(self._goods.item(row)["values"][i + 1]),
                    items_to_keep,
                )
            )

        for row in self._goods.get_children():
            if row not in items_to_keep:
                self._goods.detach(row)
                self._hidden_items.append(row)

    def clear_search(self):
        children = list(self._goods.get_children()) + self._hidden_items
        children.sort()

        for row, i in zip(children, range(len(children))):
            self._goods.reattach(row, "", i)

        for e in self._search_entries:
            e.delete(0, "end")
        self.toggle_search()

    def create_search_entries(self, master):
        self._search_entries = entries = []

        for i in range(len(self._goods_cols)):
            _ttk.Label(master, text=self._goods_cols[i], pad=5).grid(column=0, row=i)
            e = Entry(master)
            entries.append(e)
            e.grid(column=1, row=i, padx=5, pady=5)
        return len(self._goods_cols)

    def toggle_search(self):
        if self._sell_frame.winfo_ismapped():
            self._sell_frame.grid_forget()
            self._search_frame.grid(column=0, row=2)
            return
        self._search_frame.grid_forget()
        self._sell_frame.grid(column=0, row=2)

    def create_returns(self, master):
        frame = _ttk.Frame(master)

        column_names = ["ID", "ID чека", "ID продукта", "Количество", "Дата продажи"]
        display_columns = [n for n in column_names if n != "ID"]

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=2)
        frame.grid_rowconfigure(0, weight=1)

        self._checks = TableView(
            frame, self.db, "checks", ["ID чека", "Сумма", "Бонусы", "ID клиента"]
        )
        self._checks.grid(column=0, row=0, sticky="nsew", padx=5, pady=5)

        self._sales = TableView(frame, self.db, "sales", column_names)
        self._sales.config(displaycolumns=display_columns)
        self._sales.grid(column=1, row=0, sticky="nsew", padx=5, pady=5)

        Button(frame, text="Вернуть", command=self.on_return_sales).grid(
            column=0, row=1, columnspan=2, pady=10
        )

        self.update_sales()

        return frame

    def update_sales(self):
        self._checks.update_data()
        self._sales.update_data()

    def find_sales(self, check_id):
        result = []
        for row in self._sales.get_children():
            values = self._sales.item(row)["values"]
            if values[1] == check_id:
                result.append(row)
        return result

    def on_return_sales(self):
        if not self._checks.selection() and not self._sales.selection():
            return util.show_error("Выберите хотя бы один чек или товар для возврата")

        selected_sales = list(self._sales.selection())

        for check in self._checks.selection():
            check_id = self._checks.item(check)["values"][0]
            selected_sales += self.find_sales(check_id)
        selected_sales = set(selected_sales)

        if not _msg.askyesno(
            "Подтверждение",
            "Вернуть чеков: %d, товаров: %d?"
            % (len(self._checks.selection()), len(selected_sales)),
        ):
            return

        for sale in selected_sales:
            # ID записи в первом столбце (скрытом)
            values = self._sales.item(sale)["values"]
            self.db.return_sale(values[0])

        for check in self._checks.selection():
            values = self._checks.item(check)["values"]
            self.db.return_check(values[0])

        self.update_sales()
        self._goods.update_data()

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

    def create_bonus_window(self, bonuses):
        self._bonus_window = win = _tk.Toplevel(self)
        self._bonus_window.overrideredirect(True)
        bonuses = _tk.Scale(
            win,
            from_=0,
            to=bonuses,
            tickinterval=bonuses,
            resolution=1,
            font="Ubuntu 16",
            orient="horizontal",
        )
        bonuses.pack()
        Button(
            win, text="Использовать бонусы", command=lambda: self.on_sell(bonuses.get())
        ).pack()
        util.center_window(win)

    def find_row(self, table, name):
        for row in table.get_children():
            if name == table.item(row)["values"][1]:
                return row, table.item(row)["values"]
        return None, None

    def on_good_select(self, _, selected):
        if len(selected["values"]) < 2:
            return
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

    def on_sell(self, use_bonuses=None):
        if len(self._check.get_children()) == 0:
            return util.show_error("В чеке нет товаров")
        if len(self._client_code.get_strip()) == 0:
            result = _msg.askyesno("Подтверждение", "Не вводить код клиента?")
            if not result:
                return
            client_id, bonuses = None, 0
        else:
            data = self.db.get_client_by_code(self._client_code.get_strip())
            if not data:
                return util.show_error("Клиент не найден")
            client_id, bonuses = data

        if client_id is not None and use_bonuses is None and bonuses > 0:
            if _msg.askyesno("Бонусы", "Хотите использовать до %d бонусов?" % bonuses):
                self.create_bonus_window(bonuses)
                return
        elif use_bonuses is not None and use_bonuses >= 0:
            self._bonus_window.destroy()
            self._bonus_window = None

        use_bonuses = 0 if use_bonuses is None else use_bonuses

        self.db.add_check(self._check_id, self._check_sum, use_bonuses, client_id)
        add_bonuses = 0
        for row in self._check.get_children():
            values = self._check.item(row)["values"]
            goods_row = self.find_row(self._goods, values[0])[1]
            product_id = goods_row[0]
            if goods_row[-2] > 0:
                add_bonuses += goods_row[-2]

            amount = self._check.item(row)["values"][1]
            self.db.sell_product(self._check_id, product_id, amount)

        if client_id:
            self.db.change_bonuses(client_id, add_bonuses - use_bonuses)
        self._check.clear()
        self.db.save()

        if use_bonuses:
            self._check_sum -= use_bonuses * 10
        message = "Чек №%d на сумму %d" % (self._check_id, self._check_sum)
        if client_id and use_bonuses > 0:
            message += " (бонусов использовано: %d)" % use_bonuses
        if client_id and add_bonuses > 0:
            message += "\nНачислено бонусов: %d" % add_bonuses
        util.show_info(message)

        self._client_code.delete(0, "end")
        self.update_check_id()
        self.update_check_sum()
        if self._is_admin:
            self.update_sales()

    def check_return(self, role):
        if role != Roles.ADMIN.value:
            return util.show_error("Введите логин и пароль администратора")
        self.do_return()
        self.confirm_window.withdraw()

    def on_return(self):
        if self._is_admin:
            self.do_return()
            return

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
