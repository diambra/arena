import os, stat
from pathlib import Path
from queue import Queue
import threading
import numpy as np
import ctypes, ctypes.util
import time

# A thread used for reading data from a pipe
# pipes don't have very good time out functionality,
# so this is used in combination with a queue
class StreamGobbler(threading.Thread):

    def __init__(self, pipe, queue):
        threading.Thread.__init__(self)
        self.pipe = pipe
        self.queue = queue
        self.stopEvent = threading.Event()

    def run(self):
        while True:
            line = self.pipe.readline()
            while (line[-4:] != b"DeS\n"):
                line += self.pipe.readline()
            #if self.debug:
            #    print(line)
            self.queue.put(line[:-4])
            if self.stopEvent.is_set():
                break

    def stop(self):
        self.stopEvent.set()

def openPipe(pipeQueue, path, mode):
    pipeQueue.put(open(path, mode + "b"))

# A class used for creating and interacting with a Linux FIFO pipe
class Pipe(object):

    def __init__(self, env_id, pipe_id, mode, pipes_path):
        self.pipeId = pipe_id + "Pipe"
        self.mode = mode
        self.pipes_path = Path(pipes_path)
        if not self.pipes_path.exists():
            self.pipes_path.mkdir()

        # Pipe path definition
        self.path = self.pipes_path.joinpath(Path(pipe_id + "-" + str(env_id) + ".pipe"))

    # Opens the pipe in the toolkit and in the Lua engine
    # When a pipe is opened in read mode, it will block the thread until the
    # same pipe is opened in write mode on a different thread
    def open(self):
        try:

            # Create pipe
            pipe_queue = Queue()
            open_thread = threading.Thread(target=openPipe, args=[pipe_queue,
                                                                  str(self.path.absolute()), self.mode])
            open_thread.start()
            open_thread.join(timeout=3)
            self.fifo = pipe_queue.get(timeout=3)

            if self.mode == "r":
                self.read_queue = Queue()
                self.gobbler = StreamGobbler(self.fifo, self.read_queue)
                self.gobbler.start()
        except Exception as e:
            error = "Failed to open pipe '" + str(self.path.absolute()) + "'"
            raise IOError(error)

    def close(self):
        if self.mode == "r":
            # Stop the gobbler
            self.gobbler.stop()
            self.gobbler.join()

        self.fifo.close()

    def sendEnvSettings(self, string):
        self.writeln(string)

    def sendComm(self, commType, movP1=0, attP1=0, movP2=0, attP2=0):
        commString = str(commType) + "+" + str(movP1) + "+" + str(attP1) + "+"\
                                         + str(movP2) + "+" + str(attP2) + "+"
        self.writeln(commString);

    # Writes to the pipe
    def writeln(self, line):
        self.fifo.write(line.encode("utf-8")+b'\n')
        self.fifo.flush()

    # Reads to the pipe
    # timeout specifies how long the pipe should wait before there is likely
    # to be a problem on the DIAMBRA Env side
    def readln(self, timeout=None):
        try:
            return self.read_queue.get(timeout=timeout)
        except Exception as e:
            error = "Failed to read value from '" + self.pipeId + "'"
            raise IOError(error)

# A special implementation of a Linux FIFO pipe which is used for reading all
# of the frame data and memory address values from the emulator
class DataPipe(object):

    def __init__(self, env_id, pipe_id, mode, pipes_path):
        self.pipe = Pipe(env_id, pipe_id, mode, pipes_path)
        self.boolDataVarsList = ["roundDone", "stageDone", "gameDone", "epDone"]

    def open(self):
        self.pipe.open()

    def close(self):
        self.pipe.close()

    # Initialize frame dims inside read pipe
    def setFrameSize(self, hwcDim):
        self.height = hwcDim[0]
        self.width  = hwcDim[1]
        self.nChan  = hwcDim[2]
        self.frameDim = hwcDim[0] * hwcDim[1] * hwcDim[2]

    def readEnvInfo(self, timeout=None):
        line = self.pipe.readln(timeout=timeout)
        line = line.decode('utf-8')
        return line.split(",")

    def readEnvIntDataVarsList(self, timeout=None):
        line = self.pipe.readln(timeout=timeout)
        line = line.decode('utf-8')
        self.intDataVarsList = line.split(",")
        self.intDataVarsList.remove("")

    # Read data
    def readData (self, timeout=None):
        line = self.pipe.readln(timeout=timeout)
        line = line.decode('utf-8')
        line = line.split(",")

        data = {}

        idx = 0
        for var in self.intDataVarsList:
            data[var] = int(line[idx])
            idx += 1

        for var in self.boolDataVarsList:
            data[var] = bool(int(line[idx]))
            idx += 1

        return data, line[-2]

    # Read frame
    def readFrame(self, timeout=None):
        line = self.pipe.readln(timeout=timeout)
        frame = np.frombuffer(line[:self.frameDim], dtype='uint8').reshape(self.height, self.width, self.nChan)
        return frame

    # Read reset data
    def readResetData(self, timeout=None):
        data, playerSide = self.readData(timeout)
        frame = self.readFrame(timeout)
        return frame, data, playerSide

    # Read step data
    def readStepData(self, timeout=None):
        data, _ = self.readData(timeout)
        frame = self.readFrame(timeout)
        return frame, data
