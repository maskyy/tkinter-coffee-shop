import json as _json
import tkinter as _tk
import tkinter.ttk as _ttk

__all__ = ["init_style", "lookup"]

_default_name = "files/style.json"
_style = None


def init_style(filename=_default_name):
    global _style
    _style = _ttk.Style()

    with open(filename) as f:
        data = _json.load(f)
    for k, v in data.items():
        _style.configure(k, **v)


def lookup(style, option):
    if _style is None:
        return None
    return _style.lookup(style, option)


class Entry(_ttk.Entry):
    """add another getter and try to fix font setting with a style"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        font = lookup(self.winfo_class(), "font")
        if font:
            self["font"] = font

    def get_strip(self):
        return self.get().strip()


class Button(_ttk.Button):
    """add padding in style"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pad = lookup(self.winfo_class(), "pad")
        if pad:
            self["pad"] = pad
