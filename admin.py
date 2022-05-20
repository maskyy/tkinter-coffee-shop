import enum as _enum
import tkinter as _tk
import tkinter.messagebox as _msg
import tkinter.ttk as _ttk

import logo
import util
from db_sqlite import Database
from hint import Hint
from style import Button, Entry
from tableview import TableView
from tabs import Tabs
from window import Window

__all__ = ["Admin"]


class DeliveryActions(_enum.Enum):
    INSERT = "Вставить"
    ADD = "Добавить"
    UPDATE = "Обновить"


class Admin(Window):
    def __init__(self):
        super().__init__("Панель администратора")
        self.db = Database()
        self.goods_cols = [
            "Штрихкод",
            "Наименование",
            "Производитель",
            "Количество",
            "Цена",
        ]

        self.create_widgets()

    def create_widgets(self):
        logo.get_label(self).pack()
        tabs = Tabs(self)
        tabs.populate(
            {
                self.create_goods: "Товары",
                self.create_delivery: "Поставка",
                self.create_sales: "Продажи",
            }
        )

    def create_goods(self, master):
        frame = _ttk.Frame(master)
        self.goods = TableView(frame, self.db, "goods", self.goods_cols)
        self.goods.update_data()
        self.goods.pack(expand=True, fill="both", padx=20, pady=20)
        Button(frame, text="Обновить", command=self.goods.update_data).pack(pady=15)
        Hint(
            frame,
            hint="""В данном окне показана таблица всех товаров в магазине.
Чтобы обновить таблицу, можно нажать соответствующую кнопку.""",
        ).pack()
        return frame

    def create_delivery(self, master):
        frame = _ttk.Frame(master)
        self.delivery = TableView(frame, columns=self.goods_cols + ["Действие"])
        self.delivery.grid(column=0, row=0, sticky="nsew", padx=20, pady=20)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        subframe = _ttk.Frame(frame)
        subframe.grid(column=1, row=0, sticky="n", padx=10, pady=20)
        self.product_info = self.add_product_entries(subframe)
        Button(subframe, text="Добавить", command=self.add_product).pack(pady=10)
        Button(subframe, text="Завершить поставку", command=self.make_delivery).pack(
            pady=40
        )
        Hint(
            subframe,
            hint="""Чтобы добавить новый товар, введите все его данные:
- штрихкод из 13 цифр
- название товара
- производитель
- количество товара (не меньше 0)
- цена одного товара (не меньше 0)

Если товар существует, можно либо увеличить его количество, либо обновить его данные

Для завершения поставки необходимо нажать соответствующую кнопку.""",
        ).pack(pady=30)

        return frame

    def add_product_entries(self, master):
        entries = []
        for i in range(len(self.goods_cols)):
            name = self.goods_cols[i]
            _ttk.Label(master, text=name).pack(pady=2)
            e = Entry(master)
            e.pack(pady=2)
            entries.append(e)
        return entries

    def validate_add_data(self, barcode, amount):
        if not barcode or len(barcode) != 13 or not barcode.isdigit():
            return util.show_error("Введите штрихкод из 13 цифр")

        if not amount or (not amount.isdigit() or int(amount) < 0):
            return util.show_error(
                "Количество должно быть целым неотрицательным числом"
            )

        return True

    def validate_other_data(self, name, manufacturer, price):
        if not name:
            return util.show_error("Наименование товара не должно быть пустым")

        if not manufacturer:
            return util.show_error("Производитель не должен быть пустым")

        if not price or (not price.isdigit() or int(price) < 0):
            return util.show_error("Цена должна быть целым неотрицательным числом")

        return True

    def product_exists(self, barcode):
        for row in self.goods.get_children():
            if str(self.goods.item(row)["values"][0]) == barcode:
                return True

        for row in self.delivery.get_children():
            if str(self.delivery.item(row)["values"][0]) == barcode:
                return True

        return False

    def add_product(self):
        info = [e.get_strip() for e in self.product_info]
        barcode, name, manufacturer, amount, price = info
        action = DeliveryActions.INSERT

        if not self.validate_add_data(barcode, amount):
            return
        if self.product_exists(barcode):
            result = _msg.askyesno(
                "Добавить или обновить?",
                "Да - добавить количество к существующему товару, нет - обновить его данные",
            )
            if result:
                action = DeliveryActions.ADD
            else:
                action = DeliveryActions.UPDATE

        if action != DeliveryActions.ADD and not self.validate_other_data(
            name, manufacturer, price
        ):
            return

        self.delivery.insert("", "end", values=info + [action.value])
        [e.delete(0, "end") for e in self.product_info]

    def make_delivery(self):
        for row in self.delivery.get_children():
            row = self.delivery.item(row)["values"]
            if row[-1] == DeliveryActions.INSERT.value:
                self.db.add_product(*row[:-1])
            elif row[-1] == DeliveryActions.ADD.value:
                self.db.change_by_amount(row[0], row[3])
            else:
                kwargs = dict(
                    zip(["name", "manufacturer", "amount", "price"], row[1:-1])
                )
                self.db.update_product(row[0], **kwargs)

        self.delivery.clear()
        self.goods.update_data()

    def create_sales(self, master):
        frame = _ttk.Frame(master)
        column_names = ["ID", "ID чека", "Штрихкод", "Количество", "Стоимость"]
        display_columns = [n for n in column_names if n != "ID"]

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=2)

        self.checks = TableView(frame, self.db, "checks", ["ID чека", "Сумма"])
        self.checks.grid(column=0, row=0, sticky="ew", padx=5, pady=5)

        self.sales = TableView(frame, self.db, "sales", column_names)
        self.sales.config(displaycolumns=display_columns)
        self.sales.grid(column=1, row=0, sticky="ew", padx=5, pady=5)

        self._check_sum = _ttk.Label(frame)
        self._check_sum.grid(column=0, row=1)

        Button(frame, text="Вернуть", command=self.on_return).grid(
            column=0, row=2, pady=10
        )
        Button(frame, text="Сбросить выручку", command=self.on_reset).grid(
            column=0, row=3, pady=10
        )

        Hint(
            frame,
            hint="""В этом окне показаны все чеки и проданные товары, а также выручка.
Чтобы вернуть чеки и/или товары, выберите их в таблице (можно выбрать несколько через Shift или Ctrl).
Чтобы сбросить выручку (удалить все чеки и товары), нужно нажать соответствующую кнопку.""",
        ).grid(column=0, row=4, pady=10)

        self.update_sales()

        return frame

    def update_sales(self):
        self.checks.update_data()
        self.sales.update_data()

        result = 0
        for row in self.checks.get_children():
            result += self.checks.item(row)["values"][1]
        self._check_sum.config(text="Выручка: %d" % result)

    def find_sales(self, check_id):
        result = []
        for row in self.sales.get_children():
            values = self.sales.item(row)["values"]
            if values[1] == check_id:
                result.append(row)
        return result

    def on_return(self):
        if not self.checks.selection() and not self.sales.selection():
            return util.show_error("Выберите хотя бы один чек или товар для возврата")

        selected_sales = list(self.sales.selection())

        for check in self.checks.selection():
            check_id = self.checks.item(check)["values"][0]
            selected_sales += self.find_sales(check_id)
        selected_sales = set(selected_sales)

        if not _msg.askyesno(
            "Подтверждение",
            "Вернуть чеков: %d, товаров: %d?"
            % (len(self.checks.selection()), len(selected_sales)),
        ):
            return

        for sale in selected_sales:
            # ID записи в первом столбце (скрытом)
            values = self.sales.item(sale)["values"]
            self.db.return_sale(values[0])

        for check in self.checks.selection():
            values = self.checks.item(check)["values"]
            self.db.return_check(values[0])

        self.update_sales()
        self.goods.update_data()

    def on_reset(self):
        if not _msg.askyesno("Подтверждение", "Сбросить всю выручку?"):
            return

        self.db.reset_sales()
        self.update_sales()


if __name__ == "__main__":
    root = _tk.Tk()
    root.withdraw()
    admin = Admin()
    util.set_close_handler(admin, root.destroy)
    admin.mainloop()
