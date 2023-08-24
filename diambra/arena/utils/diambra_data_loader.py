import pickle
import bz2
import cv2
import os
import logging
import numpy as np
import sys

# Diambra dataloader
class DiambraDataLoader:
    def __init__(self, dataset_path: str, log_level=logging.INFO):
        logging.basicConfig(level=log_level)
        self.logger = logging.getLogger(__name__)

        # List of RL trajectories files
        self.dataset_path = dataset_path
        self.episode_files = []

        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"The path '{self.dataset_path}' does not exist.")

        if not os.path.isdir(self.dataset_path):
            raise NotADirectoryError(f"'{self.dataset_path}' is not a directory.")

        episode_files = [filename for filename in os.listdir(self.dataset_path) if filename.endswith(".diambra")]

        if not episode_files:
            raise Exception("No '.diambra' files found in the specified directory.")

        self.episode_files = episode_files

        # Idx of trajectory file to read
        self.file_idx = 0
        self.n_loops = 0
        self.frame = np.zeros((128, 128, 1), dtype=np.uint8)

    # Step the environment
    def step(self):

        step_data = self.episode_data[self.step_idx]
        self.frame = cv2.imdecode(np.frombuffer(step_data["obs"]["frame"], dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        step_data["obs"]["frame"] = self.frame
        self.step_idx += 1

        return step_data["obs"], step_data["action"], step_data["reward"], step_data["terminated"], step_data["truncated"], step_data["info"],

    # Resetting the environment
    def reset(self):

        self.n_loops += int(self.file_idx / len(self.episode_files))
        self.file_idx = self.file_idx % len(self.episode_files)

        # Open the next episode file
        episode_file = self.episode_files[self.file_idx]
        # Idx of trajectory file to read
        self.file_idx += 1
        self.frame = np.zeros((128, 128, 1), dtype=np.uint8)

        # Read compressed RL Traj file
        in_file = bz2.BZ2File(os.path.join(self.dataset_path, episode_file), 'r')
        self.episode = pickle.load(in_file)
        in_file.close()

        self.logger.info("Episode summary = {}".format(self.episode["episode_summary"]))
        self.episode_data = self.episode["data"]

        # Reset run step
        self.step_idx = 0

        return self.n_loops

    # Rendering the environment
    def render(self, waitKey=1):
        if (sys.platform.startswith('linux') is False or 'DISPLAY' in os.environ):
            try:
                window_name = "Diambra Data Loader"
                cv2.namedWindow(window_name, cv2.WINDOW_GUI_NORMAL)
                cv2.imshow(window_name, self.frame)
                cv2.waitKey(waitKey)
                return True
            except:
                return False

