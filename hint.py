import tkinter.messagebox as _msg
import tkinter.ttk as _ttk

import style as _style

__all__ = ["Hint"]


class Hint(_ttk.Button):
    def __init__(self, *args, **kwargs):
        if "hint" in kwargs:
            self.hint = kwargs["hint"]
            del kwargs["hint"]
        else:
            self.hint = None

        super().__init__(*args, **kwargs)

        if "width" not in kwargs:
            self.config(width=3)
        if "text" not in kwargs:
            self.config(text="?")

        self.config(command=self.show_hint)

    def show_hint(self):
        _msg.showinfo("Помощь", self.hint)
