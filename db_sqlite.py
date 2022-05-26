import datetime as _dt
import os.path as _path
import random as _rnd
import sqlite3 as _sql

import dates as _dates

__all__ = ["Database"]

_default_name = _path.dirname(__file__) + "/files/coffee.sqlite3"

_init_script = """
PRAGMA encoding = "UTF-8";
PRAGMA foreign_keys = 1;

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    phone TEXT NOT NULL,
    name TEXT NOT NULL,
    bonuses INTEGER NOT NULL DEFAULT 0 CHECK(bonuses >= 0),
    bonus_code TEXT NOT NULL,
    code_date TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS goods (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    manufacturer TEXT NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0 CHECK(amount >= 0),
    sell_price INTEGER NOT NULL DEFAULT 0 CHECK(sell_price >= 0),
    use_by TEXT NOT NULL,
    purchase_price INTEGER NOT NULL DEFAULT 0 CHECK(purchase_price >= 0),
    bonuses INTEGER NOT NULL DEFAULT 0 CHECK(bonuses >= 0),
    returnable INTEGER NOT NULL DEFAULT 1
) STRICT;

CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY,
    sum INTEGER NOT NULL DEFAULT 0 CHECK(sum >= 0),
    client_id INTEGER DEFAULT NULL,
    FOREIGN KEY(client_id) REFERENCES clients(id) ON UPDATE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY,
    check_id INTEGER,
    product_id INTEGER,
    amount INTEGER NOT NULL DEFAULT 0 CHECK(amount > 0),
    sell_date TEXT NOT NULL,
    FOREIGN KEY(check_id) REFERENCES checks(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES goods(id) ON UPDATE CASCADE 
) STRICT;

CREATE TABLE IF NOT EXISTS logins (
    login TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT "cashier"
)
"""

_exit_script = """
PRAGMA analysis_limit = 1000;
PRAGMA optimize;
"""


class Database:
    _connection = None

    def close_connection():
        Database._connection.close()

    def __init__(self, filename=_default_name):
        if not Database._connection:
            Database._connection = _sql.connect(filename)
        self.closed = False
        self._cur = Database._connection.cursor()
        self._cur.executescript(_init_script)

    def __del__(self):
        self.close()

    def save(self):
        Database._connection.commit()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self._cur.executescript(_exit_script)
        self._cur.close()
        self.save()

    def get_table(self, name):
        return self._cur.execute("SELECT * FROM %s" % name).fetchall()

    def execute(self, *args):
        return self._cur.execute(*args)

    def get_columns(self, table):
        self._cur.execute("SELECT name FROM PRAGMA_TABLE_INFO('%s')" % table)
        return [name[0] for name in self._cur.fetchall()]

    def get_user(self, login):
        self._cur.execute("SELECT password, role FROM logins WHERE login = ?", (login,))
        result = self._cur.fetchone()
        return result

    def register_user(self, login, password, role):
        self._cur.execute(
            "INSERT INTO logins VALUES (?, ?, ?)", (login, password, role)
        )

    def get_new_check_id(self):
        result = self._cur.execute("SELECT MAX(id)+1 FROM checks").fetchone()[0]
        return 1 if not result else result

    def add_check(self, id_, sum_, client):
        self._cur.execute("INSERT INTO checks VALUES (?, ?, ?)", (id_, sum_, client))

    def change_by_amount(self, id_, amount):
        self._cur.execute("SELECT amount FROM goods WHERE id = ?", (id_,))
        current = self._cur.fetchone()
        if not current:
            print("Item not found!")
            return False
        new = current[0] + amount
        self._cur.execute(
            "UPDATE goods SET amount = ? WHERE id = ?", (new, id_)
        )

    def sell_product(self, check_id, product_id, amount):
        self.change_by_amount(product_id, -amount)

        self._cur.execute(
            "INSERT INTO sales VALUES (NULL, ?, ?, ?, date())",
            (check_id, product_id, amount),
        )

    def return_check(self, check_id):
        self._cur.execute("DELETE FROM checks WHERE id = ?", (check_id,))
        self._cur.execute("DELETE FROM sales WHERE check_id = ?", (check_id,))

    def return_sale(self, id_):
        self._cur.execute("SELECT check_id FROM sales WHERE id = ?", (id_,))
        check_id = self._cur.fetchone()
        if not check_id:
            print("Check not found!")
            return False
        check_id = check_id[0]

        self._cur.execute("SELECT product_id, amount FROM sales WHERE id = ?", (id_,))
        product_id, amount = self._cur.fetchone()
        self._cur.execute("SELECT sell_price, returnable FROM goods WHERE id = ?", (product_id,))
        sell_price, returnable = self._cur.fetchone()

        if returnable:
            self.change_by_amount(product_id, amount)
        self._cur.execute(
            "UPDATE checks SET sum = sum - ? WHERE id = ?", (amount * sell_price, check_id)
        )
        self._cur.execute("DELETE FROM sales WHERE id = ?", (id_,))

    def generate_codes(self):
        self._cur.execute("SELECT id, bonus_code, code_date FROM clients")
        results = [list(row) for row in self._cur.fetchall()]
        today = _dt.date.today()
        for row in results:
            date = _dates.to_date(row[2])
            if not date or date < today:
                row[1] = str(_rnd.randint(1000000, 1999999))[1:]
                row[2] = _dates.from_date(today)
            self._cur.execute("UPDATE clients SET bonus_code = ?, code_date = ? WHERE id = ?", (row[1], row[2], row[0]))
        print("Codes:", results)
        self.save()

    def get_client_by_code(self, code):
        self._cur.execute("SELECT id, bonuses FROM clients WHERE bonus_code = ?", (code,))
        result = self._cur.fetchone()
        return result if result else None

"""
    def add_product(self, *args):
        _check_args(5, args)
        self._cur.execute("INSERT INTO goods VALUES (?, ?, ?, ?, ?)", args)

    def update_product(self, barcode, **kwargs):
        set_str = ""
        data = []
        for key in ["name", "manufacturer", "amount", "price"]:
            if key in kwargs:
                data.append(kwargs[key])
                set_str += key + " = ?, "
        data.append(barcode)
        data = tuple(data)
        set_str = set_str[:-2]
        self._cur.execute("UPDATE goods SET %s WHERE barcode = ?" % set_str, data)

    def sell_product(self, check_id, barcode, amount, cost):
        """ """
        count = self._cur.execute(
            "SELECT amount FROM goods WHERE barcode = ?", (barcode,)
        ).fetchone()[0]
        new_amount = count - amount
        self._cur.execute(
            "UPDATE goods SET amount = ? WHERE barcode = ?", (new_amount, barcode)
        )
        """ """
        self.change_by_amount(barcode, -amount)

        self._cur.execute(
            "INSERT INTO sales VALUES (NULL, ?, ?, ?, ?)",
            (check_id, barcode, amount, cost),
        )
        """ """
        self._cur.execute(
            "UPDATE checks SET sum = sum + ? WHERE id = ?", (cost, check_id)
        )
        """ """

    def reset_sales(self):
        self._cur.executescript("DELETE FROM sales; DELETE FROM checks;")
"""
