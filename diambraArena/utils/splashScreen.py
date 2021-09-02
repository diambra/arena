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
    def __init__(self, version="0000000", imgTimeout=3000):
        #Thread.__init__(self)   # thread init class (don't forget this)

        self.version = version
        self.imgTimeout = imgTimeout

    def run(self):      # run is a default Thread function

        window = tk.Tk()
        window.overrideredirect(True)
        window.wm_attributes("-topmost", True)

        # Get the screen which contains top
        currentScreen = getMonitorFromCoord(window.winfo_x(), window.winfo_y())

        # Get the monitor's size
        width = currentScreen.width
        height = currentScreen.height

        image = tk.PhotoImage(file=gifFilePath)
        hwDim = [image.height(), image.width()]
        window.geometry('%dx%d+%d+%d' % (hwDim[1], hwDim[0], (width - hwDim[1])/2, (height - hwDim[0])/2))

        canvas = tk.Canvas(window, height=hwDim[0], width=hwDim[1], bg="brown")
        canvas.create_image(hwDim[1]/2, hwDim[0]/2, image=image)
        canvas.create_text(hwDim[1]-45, hwDim[0]-12, fill="#888888", font="Verdana 8",
                           text="v. " + self.version)
        canvas.pack()
        window.after(self.imgTimeout, window.destroy)
        window.mainloop()

        return

if __name__ == "__main__":

    splashScreen = DIAMBRASplashScreen()
    #splashScreen.start() # Thread deactivated
    splashScreen.run()
