#!/usr/bin/env python3
import diambra.arena
from diambra.arena import SpaceTypes, Roles, EnvironmentSettings

def main():
    # Settings
    settings = EnvironmentSettings() # Single agent environment

    # --- Environment settings ---

    # Number of steps performed by the game
    # for every environment step, bounds: [1, 6]
    settings.step_ratio = 6

    # Native frame resize operation
    settings.frame_shape = (128, 128, 0)  # RBG with 128x128 size
    # settings.frame_shape = (0, 0, 1) # Grayscale with original size
    # settings.frame_shape = (0, 0, 0) # Deactivated (Original size RBG)

    # If to use discrete or multi_discrete action space
    settings.action_space = SpaceTypes.MULTI_DISCRETE

    # --- Episode settings ---

    # Player role selection: P1 (left), P2 (right), None (50% P1, 50% P2)
    settings.role = Roles.P1

    # Game continue logic (0.0 by default):
    # - [0.0, 1.0]: probability of continuing game at game over
    # - int((-inf, -1.0]): number of continues at game over
    #                      before episode to be considered done
    settings.continue_game = 0.0

    # If to show game final when game is completed
    settings.show_final = False

    # Game-specific options (see documentation for details)
    # Game difficulty level
    settings.difficulty = 4

    # Character to be used, automatically extended with None for games
    # requiring to select more than one character (e.g. Tekken Tag Tournament)
    settings.characters = "Kasumi"

    # Character outfit
    settings.outfits = 2

    env = diambra.arena.make("doapp", settings, render_mode="human")

    observation, info = env.reset(seed=42)
    env.show_obs(observation)

    while True:
        actions = env.action_space.sample()
        print("Actions: {}".format(actions))

        observation, reward, terminated, truncated, info = env.step(actions)
        done = terminated or truncated
        env.show_obs(observation)
        print("Reward: {}".format(reward))
        print("Done: {}".format(done))
        print("Info: {}".format(info))

        if done:
            # Optionally, change episode settings here
            options = {}
            options["role"] = Roles.P2
            options["continue_game"] = 0.0
            options["difficulty"] = None
            options["characters"] = None
            options["outfits"] = 4

            observation, info = env.reset(options=options)
            env.show_obs(observation)
            break

    env.close()

    # Return success
    return 0

if __name__ == '__main__':
    main()