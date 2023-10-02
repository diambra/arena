import os
import tkinter as tk
import screeninfo
from screeninfo.common import ScreenInfoError, Monitor


gif_file_path = os.path.join(os.path.dirname(__file__), ".splash_screen.gif")

def get_monitor_from_coord(x, y):
    try:
        monitors = screeninfo.get_monitors()
        if not monitors:
            raise ScreenInfoError("No enumerators available")
    except ScreenInfoError:
        # Fallback to a dummy monitor if no monitors are available
        width = 1024
        height = 768
        width_mm = 361
        height_mm = 203
        return Monitor(0, 0, width, height, width_mm, height_mm)

    for m in reversed(monitors):
        if m.x <= x <= m.width + m.x and m.y <= y <= m.height + m.y:
            return m
    return monitors[0]

class SplashScreen():
    def __init__(self, time_interval=100, timeout=5000):
        self.timeout = timeout
        self.time_interval = time_interval
        # self.labels = (t*"\u25AE" for t in range(int((timeout-750)/time_interval)))
        self.labels = (t*"" for t in range(int((timeout-750)/time_interval)))
        self.labels_empty = (int((timeout-750)/time_interval)-1)*"\u25AF"

        self.window = tk.Tk()
        self.window.overrideredirect(True)
        self.window.wm_attributes("-topmost", True)

        # Get the screen which contains top
        current_screen = get_monitor_from_coord(self.window.winfo_x(), self.window.winfo_y())

        # Get the monitor's size
        width = current_screen.width
        height = current_screen.height

        image = tk.PhotoImage(master=self.window, file=gif_file_path)
        hw_dim = [image.height(), image.width()]
        self.window.geometry(
            '%dx%d+%d+%d' % (hw_dim[1], hw_dim[0],
                             (width - hw_dim[1])/2, (height - hw_dim[0])/2))

        self.canvas = tk.Canvas(
            self.window, height=hw_dim[0], width=hw_dim[1],
            bg="brown", bd=0, highlightthickness=0)
        self.canvas.create_image(hw_dim[1]/2, hw_dim[0]/2, image=image)
        self.empty_text = self.canvas.create_text(
            30, hw_dim[0]-12, anchor="w", fill="#911503", font="Verdana 10")
        # self.canvas.itemconfigure(self.empty_text, text=self.labels_empty)
        self.loadText = self.canvas.create_text(
            30, hw_dim[0]-12, anchor="w", fill="#911503", font="Verdana 10")

        self.canvas.pack()
        self.update_text()
        self.window.after(self.timeout, self.window.destroy)
        self.window.mainloop()

        return

    def update_text(self):
        try:
            self.canvas.itemconfigure(self.loadText, text=next(self.labels))
            self.window.after(self.time_interval, self.update_text)
        except StopIteration:
            pass


if __name__ == "__main__":

    splash_screen = SplashScreen()
