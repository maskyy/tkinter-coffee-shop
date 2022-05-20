import tkinter as _tk

__all__ = ["create_image", "get_label"]

_logo_default = "files/logo.png"
_logo = None


def create_image(filename=_logo_default):
    global _logo
    _logo = _tk.PhotoImage(file=filename)


def get_label(master):
    return _tk.Label(master, image=_logo)
