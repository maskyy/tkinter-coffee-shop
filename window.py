import tkinter as _tk

__all__ = ["RootWindow", "Window"]


def _init_window(win, title):
    win.title(title)
    win.attributes("-zoomed", True)


class RootWindow(_tk.Tk):
    def __init__(self, title=None):
        super().__init__()
        _init_window(self, title)


class Window(_tk.Toplevel):
    def __init__(self, title=None):
        super().__init__()
        _init_window(self, title)
