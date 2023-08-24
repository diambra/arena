import os
from os.path import expanduser
import diambra.arena
from diambra.arena.utils.controller import get_diambra_controller
import argparse

def main(use_controller):
    # Environment Settings
    settings = {}
    settings["n_players"] = 1
    settings["role"] = "Random"
    settings["step_ratio"] = 1
    settings["frame_shape"] = (256, 256, 1)
    settings["action_space"] = "multi_discrete"

    # Recording settings
    home_dir = expanduser("~")
    game_id = "doapp"
    recording_settings = {}
    recording_settings["dataset_path"] = os.path.join(home_dir, "DIAMBRA/episode_recording", game_id if use_controller else "mock")
    recording_settings["username"] = "alexpalms"

    env = diambra.arena.make(game_id, settings, episode_recording_settings=recording_settings, render_mode="human")

    if use_controller is True:
        # Controller initialization
        controller = get_diambra_controller(env.get_actions_tuples())
        controller.start()

    observation, info = env.reset(seed=42)

    while True:
        env.render()
        if use_controller is True:
            actions = controller.get_actions()
        else:
            actions = env.action_space.sample()
        observation, reward, terminated, truncated, info = env.step(actions)
        done = terminated or truncated
        if done:
            observation, info = env.reset()
            break

    if use_controller is True:
        controller.stop()
    env.close()

    # Return success
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--use_controller', type=int, default=1, help='Flag to activate use of controller')
    opt = parser.parse_args()
    print(opt)

    main(bool(opt.use_controller))
