import numpy as np
import os

import grpc
import diambra.arena.engine.interface_pb2 as interface_pb2
import diambra.arena.engine.interface_pb2_grpc as interface_pb2_grpc

# DIAMBRA Env Gym


class DiambraEngine:
    """Diambra Environment gym interface"""

    def __init__(self, env_address):

        # Opening gRPC channel
        self.channel = grpc.insecure_channel(env_address)
        self.stub = interface_pb2_grpc.EnvServerStub(self.channel)

        # Wait for grpc server to be ready
        print("Trying to connect to DIAMBRA Engine server ...")
        try:
            grpc.channel_ready_future(self.channel).result(timeout=60)
        except grpc.FutureTimeoutError:
            print("... failed.")
            exceptionMessage = "DIAMBRA Arena failed to connect to the Engine Server."
            print(exceptionMessage)
            print(" - If you are running a Python script, are you running with DIAMBRA CLI: `diambra run python script.py`?")
            print(" - If you are running a Python Notebook, have you started Jupyter Notebook with DIAMBRA CLI: `diambra run jupyter notebook`?")
            raise Exception(exceptionMessage)
        print("... done.")

        # Splash Screen
        if 'DISPLAY' in os.environ:
            from ..utils.splash_screen import SplashScreen
            SplashScreen()

    # Transforming env settings dict to pb request
    def env_settings_to_pb_request(self, env_settings):

        characters = {
            "P1": [env_settings["characters"][0][0], env_settings["characters"][0][1], env_settings["characters"][0][2]],
            "P2": [env_settings["characters"][1][0], env_settings["characters"][1][1], env_settings["characters"][1][2]]
        }
        char_outfits = {
            "first": env_settings["char_outfits"][0],
            "second": env_settings["char_outfits"][1]
        }
        frame_shape = {
            "h": env_settings["frame_shape"][0],
            "w": env_settings["frame_shape"][1],
            "c": env_settings["frame_shape"][2]
        }
        action_space = {
            "first": env_settings["action_space"][0],
            "second": env_settings["action_space"][1]
        }
        attack_but_combination = {
            "first": env_settings["attack_but_combination"][0],
            "second": env_settings["attack_but_combination"][1]
        }
        super_art = {
            "first": env_settings["super_art"][0],
            "second": env_settings["super_art"][1]
        }
        fighting_style = {
            "first": env_settings["fighting_style"][0],
            "second": env_settings["fighting_style"][1]
        }
        ultimate_style = {
            "P1": {
                "dash": env_settings["ultimate_style"][0][0],
                "evade": env_settings["ultimate_style"][0][1],
                "bar": env_settings["ultimate_style"][0][2]
            },
            "P2": {
                "dash": env_settings["ultimate_style"][1][0],
                "evade": env_settings["ultimate_style"][1][1],
                "bar": env_settings["ultimate_style"][1][2]
            }
        }

        request = interface_pb2.EnvSettings(
            gameId=env_settings["game_id"],
            continueGame=env_settings["continue_game"],
            showFinal=env_settings["show_final"],
            stepRatio=env_settings["step_ratio"],
            player=env_settings["player"],
            difficulty=env_settings["difficulty"],
            characters=characters,
            charOutfits=char_outfits,
            frameShape=frame_shape,
            actionSpace=action_space,
            attackButCombination=attack_but_combination,
            hardcore=env_settings["hardcore"],
            disableKeyboard=env_settings["disable_keyboard"],
            disableJoystick=env_settings["disable_joystick"],
            rank=env_settings["rank"],
            randomSeed=env_settings["seed"],
            superArt=super_art,
            tower=env_settings["tower"],
            fightingStyle=fighting_style,
            ultimateStyle=ultimate_style
        )

        return request

    # Send env settings, retrieve env info and int variables list [pb low level]
    def _env_init(self, env_settings_pb):
        try:
            response = self.stub.EnvInit(env_settings_pb)
        except:
            try:
                response = self.stub.GetError(interface_pb2.Empty())
                exceptionMessage = "Received error message from engine: " + response.errorMessage
                print(exceptionMessage)
            except:
                exceptionMessage = "DIAMBRA Arena failed to connect to the Engine Server."
                print(exceptionMessage)
                print(" - If you are running a Python script, are you running with DIAMBRA CLI: `diambra run python script.py`?")
                print(" - If you are running a Python Notebook, have you started Jupyter Notebook with DIAMBRA CLI: `diambra run jupyter notebook`?")

            print("See the docs (https://docs.diambra.ai) for additional details, or join DIAMBRA Discord Server (https://discord.gg/tFDS2UN5sv) for support.")
            raise Exception(exceptionMessage)

        return response

    # Send env settings, retrieve env info and int variables list
    def env_init(self, env_settings):
        env_settings_pb = self.env_settings_to_pb_request(env_settings)
        response = self._env_init(env_settings_pb)

        move_dict = {}
        for idx in range(0, len(response.actionsDict.moves), 2):
            move_dict[response.actionsDict.moves[idx]]: response.actionsDict.moves[idx + 1]
        att_dict = {}
        for idx in range(0, len(response.actionsDict.attacks), 2):
            att_dict[response.actionsDict.attacks[idx]]: response.actionsDict.attacks[idx + 1]

        env_info_dict = {
            "n_actions": [[response.nActions.butComb.first, response.nActions.butComb.second],
                          [response.nActions.noButComb.first, response.nActions.noButComb.second]],
            "frame_shape": [response.frameShape.h, response.frameShape.w, response.frameShape.c],
            "delta_health": response.deltaHealth,
            "max_stage": response.maxStage,
            "min_max_rew": [response.minMaxRew.first, response.minMaxRew.second],
            "char_list": response.charList,
            "actions_list": [response.actionsList.moves, response.actionsList.attacks],
            "actions_dict": [move_dict, att_dict],
            "additional_obs": [
                {
                    "name": response.additionalObs[idx].name,
                    "type": response.additionalObs[idx].type,
                    "min": response.additionalObs[idx].min,
                    "max": response.additionalObs[idx].max,
                } for idx in range(len(response.additionalObs))
            ]
        }
        self.int_data_vars_list = response.intDataList
        return env_info_dict

    # Set frame size
    def set_frame_size(self, hwc_dim):
        self.height = hwc_dim[0]
        self.width = hwc_dim[1]
        self.n_chan = hwc_dim[2]
        self.frame_dim = hwc_dim[0] * hwc_dim[1] * hwc_dim[2]

    # Read data
    def read_data(self, int_var, done_conds):
        int_var = int_var.split(",")

        data = {"round_done": done_conds.round,
                "stage_done": done_conds.stage,
                "game_done": done_conds.game,
                "ep_done": done_conds.episode}

        idx = 0
        for var in self.int_data_vars_list:
            data[var] = int(int_var[idx])
            idx += 1

        return data

    # Read frame
    def read_frame(self, frame):
        # return cv2.imdecode(np.frombuffer(frame, dtype='uint8'),
        #                     cv2.IMREAD_COLOR)
        return np.frombuffer(frame, dtype='uint8').reshape(self.height,
                                                           self.width,
                                                           self.n_chan)

    # Reset the environment [pb low level]
    def _reset(self):
        return self.stub.Reset(interface_pb2.Empty())

    # Reset the environment
    def reset(self):
        response = self._reset()
        data = self.read_data(response.intVar, response.doneConditions)
        frame = self.read_frame(response.frame)
        return frame, data, response.player

    # Step the environment (1P) [pb low level]
    def _step_1p(self, mov_p1, att_p1):
        command = interface_pb2.Command()
        command.P1.mov = mov_p1
        command.P1.att = att_p1
        return self.stub.Step1P(command)

    # Step the environment (1P)
    def step_1p(self, mov_p1, att_p1):
        response = self._step_1p(mov_p1, att_p1)
        data = self.read_data(response.intVar, response.doneConditions)
        frame = self.read_frame(response.frame)
        return frame, response.reward, data

    # Step the environment (2P) [pb low level]
    def _step_2p(self, mov_p1, att_p1, mov_p2, att_p2):
        command = interface_pb2.Command()
        command.P1.mov = mov_p1
        command.P1.att = att_p1
        command.P2.mov = mov_p2
        command.P2.att = att_p2
        return self.stub.Step2P(command)

    # Step the environment (2P)
    def step_2p(self, mov_p1, att_p1, mov_p2, att_p2):
        response = self._step_2p(self, mov_p1, att_p1, mov_p2, att_p2)
        data = self.read_data(response.intVar, response.doneConditions)
        frame = self.read_frame(response.frame)
        return frame, response.reward, data

    # Closing DIAMBRA Arena
    def close(self):
        response = self.stub.Close(interface_pb2.Empty())
        self.channel.close()
        return response
