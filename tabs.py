import tkinter as _tk
import tkinter.ttk as _ttk

__all__ = ["Tabs"]


class Tabs(_ttk.Notebook):
    """tabs is a dictionary where key is frame and value is name"""

    def __init__(self, master=None, tabs={}):
        super().__init__(master)
        self.pack(expand=True, fill="both")

    def populate(self, tabs):
        for k, v in tabs.items():
            if callable(k):
                k = k(self)
            self.add(k, text=v)
