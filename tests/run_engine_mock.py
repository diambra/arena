#!/usr/bin/env python3
import argparse
from diambra.arena.env_settings import EnvironmentSettings1P, EnvironmentSettings2P
from diambra.arena.utils.engine_mock import DiambraEngineMock
from dacite import from_dict
import random

def print_response(response):
    print("---")
    print("Obs =", {key: response.observation.ram_states[key].val for key in sorted(response.observation.ram_states.keys())})
    print("Reward =", response.reward)
    print("Info =", {key: response.info.game_states[key] for key in sorted(response.info.game_states.keys())})
    print("---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gameId", type=str, default="doapp", help="Game ID [(doapp), sfiii3n, tektagt, umk3]")
    parser.add_argument("--nPlayers", type=int, default=1, help="Number of Agents (1)")
    parser.add_argument("--role0", type=str, default="Random", help="agent_0 role (Random)")
    parser.add_argument("--role1", type=str, default="Random", help="agent_1 role (Random)")
    parser.add_argument("--character0", type=str, default="Random", help="Character agent_0 (Random)")
    parser.add_argument("--character1", type=str, default="Random", help="Character agent (Random)")
    parser.add_argument("--character0_2", type=str, default="Random", help="Character P1_2 (Random)")
    parser.add_argument("--character1_2", type=str, default="Random", help="Character P2_2 (Random)")
    parser.add_argument("--character0_3", type=str, default="Random", help="Character P1_3 (Random)")
    parser.add_argument("--character1_3", type=str, default="Random", help="Character P2_3 (Random)")
    parser.add_argument("--difficulty", type=int, default=0, help="Game difficulty (0)")
    parser.add_argument("--stepRatio", type=int, default=3, help="Frame ratio")
    parser.add_argument("--continueGame", type=float, default=-1.0, help="ContinueGame flag (-inf,+1.0]")
    parser.add_argument("--noAction", type=int, default=0, help="If to use no action policy (0=False)")
    parser.add_argument("--interactive", type=int, default=0, help="Interactive Visualization (False)")
    parser.add_argument("--render", type=int, default=1, help="Render frame (False)")
    opt = parser.parse_args()
    print(opt)

    # Settings
    settings = {}
    settings["game_id"] = opt.gameId
    settings["n_players"] = opt.nPlayers
    settings["role"] = (opt.role0, opt.role1)
    settings["difficulty"] = opt.difficulty
    settings["characters"] = ((opt.character0, opt.character0_2, opt.character0_3),
                              (opt.character1, opt.character1_2, opt.character1_3))
    settings["step_ratio"] = opt.stepRatio
    settings["continue_game"] = opt.continueGame
    if settings["n_players"] == 1:
        settings["role"] = settings["role"][0]
        settings["characters"] = settings["characters"][0]

    # Checking settings and setting up default ones
    if "n_players" in settings.keys() and settings["n_players"] == 2:
        settings = from_dict(EnvironmentSettings2P, settings)
    else:
        settings["n_players"] = 1
        settings = from_dict(EnvironmentSettings1P, settings)
    settings.sanity_check()

    engine_mock = DiambraEngineMock()
    env_info = engine_mock.mock_env_init(settings.get_pb_request())
    print("Env info =", env_info)

    reset_response = engine_mock.mock_reset()
    print_response(reset_response)

    action = [[0, 0],[0, 0]]
    cumulative_reward = 0.0
    while True:
        for idx in range(settings.n_players):
            action[idx] = [random.randint(0, 8), random.randint(0, 4)]
            if bool(opt.noAction) is True:
                action[idx] = [0, 0]
        print("Action =", action)

        step_response = engine_mock.mock_step(action)
        cumulative_reward += step_response.reward
        print_response(step_response)
        print("Cumulative reward =", cumulative_reward)

        done = step_response.info.game_states["episode_done"] if settings.n_players == 1 else step_response.info.game_states["game_done"]
        if done:
            print("Total cumulative reward =", cumulative_reward)
            reset_response = engine_mock.mock_reset()
            print_response(reset_response)
            break
