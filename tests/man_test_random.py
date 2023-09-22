#!/usr/bin/env python3
import argparse
from env_exec_interface import env_exec
import os
from os.path import expanduser
import random
from diambra.arena import SpaceTypes, Roles, EnvironmentSettings, EnvironmentSettingsMultiAgent, WrappersSettings, RecordingSettings

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
    parser.add_argument("--nEpisodes", type=int, default=1, help="Number of episodes")
    parser.add_argument("--continueGame", type=float, default=-1.0, help="ContinueGame flag (-inf,+1.0]")
    parser.add_argument("--actionSpace", type=str, default="discrete", help="discrete/multi_discrete")
    parser.add_argument("--noAction", type=int, default=0, help="If to use no action policy (0=False)")
    parser.add_argument("--recordEpisode", type=int, default=0, help="If to record episode")
    parser.add_argument("--interactive", type=int, default=0, help="Interactive Visualization (False)")
    parser.add_argument("--render", type=int, default=1, help="Render frame (False)")
    parser.add_argument("--wrappers", type=int, default=0, help="If to use wrappers")
    parser.add_argument("--envAddress", type=str, default="", help="diambraEngine Address")
    opt = parser.parse_args()
    print(opt)

    # Settings
    if (opt.nPlayers == 1):
        settings = EnvironmentSettings()
    else:
        settings = EnvironmentSettingsMultiAgent()
    settings.game_id = opt.gameId
    settings.frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
    if opt.envAddress != "":
        settings.env_address = opt.envAddress
    settings.role = (Roles.P1 if opt.role0 == "P1" else Roles.P2 if opt.role0 == "P2" else None,
                     Roles.P1 if opt.role1 == "P1" else Roles.P2 if opt.role1 == "P2" else None)
    settings.difficulty = opt.difficulty if opt.difficulty != 0 else None
    settings.characters = ((opt.character0, opt.character0_2, opt.character0_3),
                           (opt.character1, opt.character1_2, opt.character1_3))
    settings.characters = tuple([None if "Random" in settings["characters"][idx] else settings["characters"] for idx in range(2)])
    settings.step_ratio = opt.stepRatio
    settings.continue_game = opt.continueGame
    settings.action_space = (SpaceTypes.DISCRETE, SpaceTypes.DISCRETE) if opt.actionSpace == "discrete" else \
                               (SpaceTypes.MULTI_DISCRETE, SpaceTypes.MULTI_DISCRETE)
    if settings.n_players == 1:
        settings.role = settings.role[0]
        settings.characters = settings.characters[0]
        settings.action_space = settings.action_space[0]

    # Env wrappers settings
    wrappers_settings = WrappersSettings()
    wrappers_settings["no_op_max"] = 0
    wrappers_settings["sticky_actions"] = 1
    wrappers_settings["frame_shape"] = random.choice([(128, 128, 1), (256, 256, 0)])
    wrappers_settings["reward_normalization"] = True
    wrappers_settings["clip_rewards"] = False
    wrappers_settings["frame_stack"] = 4
    wrappers_settings["dilation"] = 1
    wrappers_settings["actions_stack"] = 12
    wrappers_settings["scale"] = True
    wrappers_settings["flatten"] = True
    suffix = ""
    if opt.nPlayers == 2:
        suffix = "agent_0_"
    if opt.gameId != "tektagt":
        wrappers_settings["filter_keys"] = ["stage", "timer", suffix+"own_side", suffix+"opp_side",
                                            suffix+"own_health", suffix+"opp_health",
                                            suffix+"action_move", suffix+"action_attack"]
    else:
        wrappers_settings["filter_keys"] = ["stage", "timer", suffix+"own_side", suffix+"opp_side",
                                            suffix+"own_health_1", suffix+"opp_health_1",
                                            suffix+"own_health_2", suffix+"opp_health_2",
                                            suffix+"action_move", suffix+"action_attack"]


        # Env wrappers settings
    wrappers_settings = WrappersSettings()
    if bool(opt.wrappers) is True:
        wrappers_settings.no_op_max = 0
        wrappers_settings.sticky_actions = 1
        wrappers_settings.frame_shape = random.choice([(128, 128, 1), (256, 256, 0)])
        wrappers_settings.reward_normalization = True
        wrappers_settings.clip_rewards = False
        wrappers_settings.frame_stack = 4
        wrappers_settings.dilation = 1
        wrappers_settings.add_last_action_to_observation = True
        wrappers_settings.actions_stack = 12
        wrappers_settings.scale = True
        wrappers_settings.role_relative_observation = True
        wrappers_settings.flatten = True
        suffix = ""
        if settings.n_players == 2:
            suffix = "agent_0_"
        wrappers_settings.filter_keys = ["stage", "timer", suffix + "own_side", suffix + "opp_side",
                                        suffix + "opp_character", suffix + "action"]

    # Recording settings
    episode_recording_settings = RecordingSettings()
    if bool(opt.recordEpisode) is True:
        home_dir = expanduser("~")
        episode_recording_settings["username"] = "alexpalms"
        episode_recording_settings["dataset_path"] = os.path.join(home_dir, "DIAMBRA/episode_recording", opt.gameId)

    # Args
    args = {}
    args["interactive"] = bool(opt.interactive)
    args["no_action_probability"] = 1.0 if opt.noAction == 1 else 0.0
    args["n_episodes"] = opt.nEpisodes
    args["render"] = bool(opt.render)
    args["log_output"] = True

    env_exec(settings, [{}], wrappers_settings, episode_recording_settings, args)
