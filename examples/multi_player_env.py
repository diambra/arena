#!/usr/bin/env python3
import diambra.arena

def main():
    # Environment Settings
    settings = {}

    # --- Environment settings ---

    # 2 Players game
    settings["n_players"] = 2

    # If to use discrete or multi_discrete action space
    settings["action_space"] = (diambra.arena.SpaceType.DISCRETE, diambra.arena.SpaceType.DISCRETE)

    # --- Episode settings ---

    # Characters to be used, automatically extended with "Random" for games
    # required to select more than one character (e.g. Tekken Tag Tournament)
    settings["characters"] = ("Random", "Random")

    # Characters outfit
    settings["outfits"] = (2, 2)

    env = diambra.arena.make("sfiii3n", settings, render_mode="human")

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
            options["characters"] = ("Ryu", "Ken")
            options["char_outfits"] = (5, 5)
            observation, info = env.reset(options=options)
            env.show_obs(observation)
            break

    env.close()

    # Return success
    return 0

if __name__ == '__main__':
    main()