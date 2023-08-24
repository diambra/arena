#!/usr/bin/env python3
import diambra.arena

def main():
    # Environment creation
    env = diambra.arena.make("doapp", render_mode="human")

    # Environment reset
    observation, info = env.reset(seed=42)

    # Agent-Environment interaction loop
    while True:
        # (Optional) Environment rendering
        env.render()

        # Action random sampling
        actions = env.action_space.sample()

        # Environment stepping
        observation, reward, terminated, truncated, info = env.step(actions)

        # Episode end (Done condition) check
        if terminated or truncated:
            observation, info = env.reset()
            break

    # Environment shutdown
    env.close()

    # Return success
    return 0

if __name__ == '__main__':
    main()