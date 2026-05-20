import tkinter as tk

class DefaultModule(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        label = tk.Label(self, text="Mở Khoá Pin", font=('Helvetica', 16))
        label.pack(pady=20)

        message = tk.Label(self, text="Chọn một mô-đun từ thanh bên để hiển thị nội dung của nó.")
        message.pack(pady=10)

        info = tk.Label(self, text="Đây là nội dung mặc định của mô-đun.")
        info.pack(pady=10)
