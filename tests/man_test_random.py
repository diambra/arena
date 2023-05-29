#!/usr/bin/env python3
import argparse
from env_exec_interface import env_exec
import time
import os
from os.path import expanduser

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--gameId", type=str, default="doapp", help="Game ID [(doapp), sfiii3n, tektagt, umk3]")
    parser.add_argument("--player", type=str, default="Random", help="Player (Random)")
    parser.add_argument("--character1", type=str, default="Random", help="Character P1 (Random)")
    parser.add_argument("--character2", type=str, default="Random", help="Character P2 (Random)")
    parser.add_argument("--character1_2", type=str, default="Random", help="Character P1_2 (Random)")
    parser.add_argument("--character2_2", type=str, default="Random", help="Character P2_2 (Random)")
    parser.add_argument("--character1_3", type=str, default="Random", help="Character P1_3 (Random)")
    parser.add_argument("--character2_3", type=str, default="Random", help="Character P2_3 (Random)")
    parser.add_argument("--difficulty", type=int, default=3, help="Game difficulty")
    parser.add_argument("--stepRatio", type=int, default=3, help="Frame ratio")
    parser.add_argument("--nEpisodes", type=int, default=1, help="Number of episodes")
    parser.add_argument("--continueGame", type=float, default=-1.0, help="ContinueGame flag (-inf,+1.0]")
    parser.add_argument("--actionSpace", type=str, default="discrete", help="discrete/multi_discrete")
    parser.add_argument("--attButComb", type=bool, default=False, help="Use attack button combinations (0=F)/1=T")
    parser.add_argument("--noAction", type=int, default=0, help="If to use no action policy (0=False)")
    parser.add_argument("--recordTraj", type=bool, default=False, help="If to record trajectories")
    parser.add_argument("--hardcore", type=bool, default=False, help="Hard core mode")
    parser.add_argument("--interactiveViz", type=int, default=0, help="Interactive Visualization (0=False)")
    parser.add_argument("--envAddress", type=str, default="", help="diambraEngine Address")
    parser.add_argument("--wrappers", type=bool, default=False, help="If to use wrappers")
    opt = parser.parse_args()
    print(opt)

    time_dep_seed = int((time.time() - int(time.time() - 0.5)) * 1000)

    # Settings
    settings = {}
    settings["game_id"] = opt.gameId
    if opt.envAddress != "":
        settings["env_address"] = opt.envAddress
    settings["player"] = opt.player
    settings["difficulty"] = opt.difficulty
    settings["characters"] = ((opt.character1, opt.character1_2, opt.character1_3),
                              (opt.character2, opt.character2_2, opt.character2_3))
    settings["step_ratio"] = opt.stepRatio
    settings["continue_game"] = opt.continueGame
    settings["action_space"] = (opt.actionSpace, opt.actionSpace)
    settings["attack_but_combination"] = (opt.attButComb, opt.attButComb)
    if settings["player"] != "P1P2":
        settings["characters"] = settings["characters"][0]
        settings["action_space"] = settings["action_space"][0]
        settings["attack_but_combination"] = settings["attack_but_combination"][0]
    settings["hardcore"] = opt.hardcore

    # Env wrappers settings
    wrappers_settings = {}
    wrappers_settings["no_op_max"] = 0
    wrappers_settings["sticky_actions"] = 1
    wrappers_settings["hwc_obs_resize"] = (128, 128, 1)
    wrappers_settings["reward_normalization"] = True
    wrappers_settings["clip_rewards"] = False
    wrappers_settings["frame_stack"] = 4
    wrappers_settings["dilation"] = 1
    wrappers_settings["actions_stack"] = 12
    wrappers_settings["scale"] = True
    wrappers_settings["scale_mod"] = 0
    wrappers_settings["flatten"] = True
    if opt.gameId != "tektagt":
        wrappers_settings["filter_keys"] = ["stage", "P1_ownSide", "P1_oppSide", "P1_oppSide",
                                            "P1_ownHealth", "P1_oppHealth", "P1_oppChar",
                                            "P1_actions_move", "P1_actions_attack"]
    else:
        wrappers_settings["filter_keys"] = ["stage", "P1_ownSide", "P1_oppSide", "P1_oppSide",
                                            "P1_ownHealth1", "P1_oppHealth1", "P1_oppChar",
                                            "P1_ownHealth2", "P1_oppHealth2",
                                            "P1_actions_move", "P1_actions_attack"]
    if opt.wrappers is False:
        wrappers_settings = {}

    # Recording settings
    traj_rec_settings = {}
    traj_rec_settings["user_name"] = "Alex"
    traj_rec_settings["file_path"] = os.path.join(expanduser("~"), "DIAMBRA/trajRecordings", opt.gameId)
    traj_rec_settings["ignore_p2"] = False
    if opt.recordTraj is False:
        traj_rec_settings = {}
    else:
        wrappers_settings["flatten"] = False

    # Args
    args = {}
    args["interactive_viz"] = bool(opt.interactiveViz)
    args["no_action"] = True if opt.noAction == 1 else False
    args["n_episodes"] = opt.nEpisodes

    env_exec(settings, wrappers_settings, traj_rec_settings, args)
