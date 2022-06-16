import sys
import os
import tkinter as tk
import screeninfo
import time
import sys
import os

gifFilePath = os.path.join(os.path.dirname(__file__), ".splashScreen.gif")


def getMonitorFromCoord(x, y):
    monitors = screeninfo.get_monitors()

    for m in reversed(monitors):
        if m.x <= x <= m.width + m.x and m.y <= y <= m.height + m.y:
            return m
    return monitors[0]

# Class to manage gampad


class DIAMBRASplashScreen():
    def __init__(self, timeInterval=100, timeout=5000):

        self.timeout = timeout
        self.timeInterval = timeInterval
        # self.labels = (t*"\u25AE" for t in range(int((timeout-750)/timeInterval)))
        self.labels = (t*"" for t in range(int((timeout-750)/timeInterval)))
        self.labelsEmpty = (int((timeout-750)/timeInterval)-1)*"\u25AF"

        self.window = tk.Tk()
        self.window.overrideredirect(True)
        self.window.wm_attributes("-topmost", True)

        # Get the screen which contains top
        currentScreen = getMonitorFromCoord(
            self.window.winfo_x(), self.window.winfo_y())

        # Get the monitor's size
        width = currentScreen.width
        height = currentScreen.height

        image = tk.PhotoImage(file=gifFilePath)
        hwDim = [image.height(), image.width()]
        self.window.geometry(
            '%dx%d+%d+%d' % (hwDim[1], hwDim[0],
                             (width - hwDim[1])/2, (height - hwDim[0])/2))

        self.canvas = tk.Canvas(
            self.window, height=hwDim[0], width=hwDim[1],
            bg="brown", bd=0, highlightthickness=0)
        self.canvas.create_image(hwDim[1]/2, hwDim[0]/2, image=image)
        self.emptyText = self.canvas.create_text(
            30, hwDim[0]-12, anchor="w", fill="#911503", font="Verdana 10")
        # self.canvas.itemconfigure(self.emptyText, text=self.labelsEmpty)
        self.loadText = self.canvas.create_text(
            30, hwDim[0]-12, anchor="w", fill="#911503", font="Verdana 10")

        self.canvas.pack()
        self.updateText()
        self.window.after(self.timeout, self.window.destroy)
        self.window.mainloop()

        return

    def updateText(self):
        try:
            self.canvas.itemconfigure(self.loadText, text=next(self.labels))
            self.window.after(self.timeInterval, self.updateText)
        except StopIteration:
            pass


if __name__ == "__main__":

    splashScreen = DIAMBRASplashScreen()
