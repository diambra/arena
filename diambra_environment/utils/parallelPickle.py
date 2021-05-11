import pickle, bz2
from threading import Thread

# Class to manage gampad
class parallelPickleWriter(Thread): # def class typr thread
   def __init__(self, savePath, to_save):
      Thread.__init__(self)   # thread init class (don't forget this)

      self.savePath = savePath
      self.to_save = to_save

   def run(self):      # run is a default Thread function
       outfile = bz2.BZ2File(self.savePath, 'w')
       print("Writing RL Trajectory to {} ...".format(self.savePath))
       pickle.dump(self.to_save, outfile)
       print("... done.")
       outfile.close()
