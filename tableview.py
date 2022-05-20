import tkinter.ttk as _ttk


class TableView(_ttk.Treeview):
    def __init__(self, master=None, db=None, table=None, columns=None, on_select=None):
        super().__init__(master)

        self.db = db
        self.table = table

        self.config(columns=columns)

        self.column("#0", width=0, stretch="no")
        self.heading("#0", text="")

        for c in columns:
            self.column(c, anchor="center", width=90)
            self.heading(c, text=c)

        self.bind("<<TreeviewSelect>>", lambda e: self.on_select(e, on_select))

    def clear(self):
        self.delete(*self.get_children())

    def clear_selection(self):
        self.selection_remove(self.selection())

    def update_data(self):
        if not self.db or not self.table:
            return

        self.clear()

        for row in self.db.get_table(self.table):
            row = tuple(str(x) for x in row)
            self.insert("", "end", values=row)

    def on_select(self, event, func):
        if func is None:
            return
        func(event, self.item(self.focus()))
