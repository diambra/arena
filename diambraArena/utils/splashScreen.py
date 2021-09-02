import sys, os
import tkinter as tk
import screeninfo, time
from threading import Thread
import sys, os

gifFilePath = os.path.join(os.path.dirname(__file__), "./.splashScreen.gif")

def getMonitorFromCoord(x, y):
    monitors = screeninfo.get_monitors()

    for m in reversed(monitors):
        if m.x <= x <= m.width + m.x and m.y <= y <= m.height + m.y:
            return m
    return monitors[0]

# Class to manage gampad
class DIAMBRASplashScreen(Thread): # def class typr thread
    def __init__(self, version="0000000", imgTimeout=5000):
        #Thread.__init__(self)   # thread init class (don't forget this)

        self.version = version
        self.imgTimeout = imgTimeout

    def run(self):      # run is a default Thread function

        self.window = tk.Tk()
        self.window.overrideredirect(True)
        self.window.wm_attributes("-topmost", True)

        # Get the screen which contains top
        currentScreen = getMonitorFromCoord(self.window.winfo_x(), self.window.winfo_y())

        # Get the monitor's size
        width = currentScreen.width
        height = currentScreen.height

        image = tk.PhotoImage(file=gifFilePath)
        hwDim = [image.height(), image.width()]
        self.window.geometry('%dx%d+%d+%d' % (hwDim[1], hwDim[0], (width - hwDim[1])/2, (height - hwDim[0])/2))

        self.canvas = tk.Canvas(self.window, height=hwDim[0], width=hwDim[1], bg="brown")
        self.canvas.create_image(hwDim[1]/2, hwDim[0]/2, image=image)
        #canvas.create_text(hwDim[1]-45, hwDim[0]-12, fill="#888888", font="Verdana 8",
        #                   text="v. " + self.version)
        self.iptext = self.canvas.create_text(hwDim[1]-45, hwDim[0]-12, fill="#888888", font="Verdana 20")

        self.ips = (t for t in ('111', '222', '333', '444'))
        self.canvas.pack()
        self.updateText()
        self.window.after(self.imgTimeout, self.window.destroy)
        self.window.mainloop()

        return

    def updateText(self):
        try:
            self.canvas.itemconfigure(self.iptext, text=next(self.ips))
            self.window.after(1000, self.updateText)
        except StopIteration:
            pass

if __name__ == "__main__":

    splashScreen = DIAMBRASplashScreen()
    #splashScreen.start() # Thread deactivated
    splashScreen.run()
