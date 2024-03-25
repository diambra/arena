#!/usr/bin/env python3
import diambra.arena
from diambra.arena import SpaceTypes, EnvironmentSettingsMultiAgent
from stable_baselines3 import PPO
import numpy as np

def main():
    # Environment Settings
    settings = EnvironmentSettingsMultiAgent() # Multi Agents environment

    # --- Environment settings ---

    # If to use discrete or multi_discrete action space
    settings.action_space = (SpaceTypes.DISCRETE, SpaceTypes.DISCRETE)

    # --- Episode settings ---

    # Characters to be used, automatically extended with None for games
    # requiring to select more than one character (e.g. Tekken Tag Tournament)
    settings.characters = ("Ken", "Ken")

    # Characters outfit
    settings.outfits = (2, 2)

    # Create environment
    env = diambra.arena.make("sfiii3n", settings, render_mode="human")

    # Load model
    model_path = "/path/to/model"

    # Load agent without passing the environment
    agent = PPO.load(model_path)
    
    # Begin evaluation
    observation, info = env.reset(seed=42)
    env.show_obs(observation)

    while True:
        env.render()

        # Extract observations for player 1 (P1), including shared environment information
        observation_p1 = {
            key: value for key, value in observation.items()
            if key.startswith('P1_') or key in ['frame', 'stage']
        }

        # Initialize player 2 (P2) observation with shared environment information
        observation_p2 = {'frame': observation['frame'], 'stage': observation['stage']}
        
        # Swap P1 and P2 keys for P2 observation
        # Modify P2 keys to match P1 format for the model, as it was trained with P1 observations
        observation_p2.update({
            key.replace('P2_', 'P1_'): value for key, value in observation.items()
            if key.startswith('P2_')
        })

        # Model prediction for P1 actions based on P1 observation
        action_p1, _ = agent.predict(observation_p1, deterministic=True)
        # Model prediction for P2 actions, using modified P2 observation
        action_p2, _ = agent.predict(observation_p2, deterministic=True)

        # Combine actions for both players
        actions = np.append(action_p1, action_p2)
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
            options["characters"] = (None, None)
            options["char_outfits"] = (5, 5)
            observation, info = env.reset(options=options)
            env.show_obs(observation)
            break

    env.close()

    # Return success
    return 0

if __name__ == '__main__':
    main()