import tkinter.messagebox as _msg

__all__ = ["set_close_handler"]


def set_close_handler(win, func):
    win.protocol("WM_DELETE_WINDOW", func)


def show_error(text):
    _msg.showerror("Ошибка", text)
    return False


def show_info(text):
    _msg.showinfo("Информация", text)
    return True


def center_window(win):
    w, h = [int(x) for x in win.geometry().split("+")[0].split("x")]
    x = (win.winfo_screenwidth() - w) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry("+%d+%d" % (x, y))
