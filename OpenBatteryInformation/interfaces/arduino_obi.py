import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports

INTERFACE_VERSION_CMD   = [0x01, 0x00, 0x03, 0x01]

def get_display_name():
    return "Arduino OBI"

class Interface(tk.Frame):
    def __init__(self, parent, obi_instance):
        super().__init__(parent)
        self.parent = parent
        self.obi_instance = obi_instance
        self.serial = serial.Serial()
        self.serial.timeout = 1
        self.create_widgets()

    def create_widgets(self):
        serial_label = tk.Label(self, text="Cổng nối tiếp:")
        serial_label.pack(pady=5)

        ports = self.get_available_serial_ports()

        self.conf_port = ttk.Combobox(self, values=ports, state="readonly")
        self.conf_port.pack(pady=5)

        self.connect_button = tk.Button(self, text="Kết nối", command=self.toggle_connection)
        self.connect_button.pack(pady=10)
        self.connect_button.config(width=20)


        self.refresh_button = tk.Button(self, text="Làm mới danh sách cổng", command=self.refresh_serial_list)
        self.refresh_button.pack(pady=10)
        self.refresh_button.config(width=20)

        self.version_label = tk.Label(self, anchor="w", width=20, text="Phiên Bản:")
        self.version_label.pack(pady=5)

    def refresh_serial_list(self):
        ports = self.get_available_serial_ports()
        self.conf_port["values"] = ports


    def get_available_serial_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports

    def toggle_connection(self):
        if self.serial.is_open:
            self.close_serial_port()
        else:
            self.open_serial_port()

    def open_serial_port(self):
        selected_port = self.conf_port.get()
        if not selected_port:
            self.obi_instance.update_debug("Chưa chọn cổng nối tiếp nào. Vui lòng chọn cổng từ menu thả xuống.")
            return
        self.serial.port = selected_port
        try:
            self.serial.open()
            self.update_version()
            self.obi_instance.update_debug(f"Cổng nối tiếp đã được mở: {selected_port}")
            self.connect_button.config(text="Ngắt kết nối", command=self.close_serial_port)
        except serial.SerialException as e:
            self.serial.close()
            self.obi_instance.update_debug(f"Lỗi khi mở cổng nối tiếp {selected_port}: {e}. Kiểm tra xem cổng đó có đang được ứng dụng khác sử dụng hay không.")
        except Exception as e:
            self.serial.close()
            self.obi_instance.update_debug(f"Lỗi không mong muốn khi mở cổng nối tiếp {selected_port}: {type(e).__name__}: {e}")

    def close_serial_port(self):
        if self.serial.is_open:
            self.serial.close()
            self.obi_instance.update_debug("Cổng nối tiếp đóng")
            self.connect_button.config(text="Kết nối", command=self.open_serial_port)

    def get_version(self):
        response = self.request(INTERFACE_VERSION_CMD, max_attempts=5)
        version_string = '.'.join(str(byte) for byte in response[2:])
    
        return version_string
    
    def update_version(self):
        self.version_label.config(text=f"Phiên bản: {self.get_version()}")

    def request(self, request, max_attempts=2):
        if not self.serial.is_open:
            raise ConnectionError("Cổng nối tiếp chưa được mở. Vui lòng kết nối với Arduino trước.")

        expected_length = request[2] + 2
        for attempt in range(1, max_attempts + 1):
            self.obi_instance.update_debug(f">> {' '.join(f'{x:02X}' for x in request[3:])}")
            try:
                self.serial.reset_input_buffer()
                self.serial.write(request)

                response = self.serial.read(expected_length)
                self.obi_instance.update_debug(f"<< {' '.join(f'{x:02X}' for x in response[2:])}")
                if request[2] == 0:
                    return

                if len(response) == 0:
                    raise TimeoutError(f"Không nhận được phản hồi từ Arduino (dự kiến {expected_length} bytes). Kiểm tra xem pin đã được kết nối chưa.")

                if len(response) != expected_length:
                    raise ValueError(f"Phản hồi chưa đầy đủ: đã nhận được {len(response)} bytes, expected {expected_length}. Pin có thể chưa được lắp đúng cách.")

                if all(byte == 0xff for byte in response[2:]):
                    raise ValueError("Phản hồi không hợp lệ: tất cả các byte đều là 0xFF. Có thể pin không giao tiếp đúng cách.")

                return response

            except (TimeoutError, ValueError) as e:
                self.obi_instance.update_debug(f"Attempt {attempt}/{max_attempts} failed: {e}")
            except serial.SerialException as e:
                self.obi_instance.update_debug(f"Attempt {attempt}/{max_attempts} serial error: {e}. The Arduino may have been disconnected.")
            except Exception as e:
                self.obi_instance.update_debug(f"Attempt {attempt}/{max_attempts} unexpected error: {type(e).__name__}: {e}")
        raise ConnectionError(f"Failed to get a valid response after {max_attempts} attempts. Ensure the Arduino is connected and a battery is inserted.")

