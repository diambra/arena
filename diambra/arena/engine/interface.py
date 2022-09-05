import numpy as np
import os

import grpc
import diambra.arena.engine.interface_pb2 as interface_pb2
import diambra.arena.engine.interface_pb2_grpc as interface_pb2_grpc

# DIAMBRA Env Gym


class DiambraEngine:
    """Diambra Environment gym interface"""

    def __init__(self, env_address, grpc_timeout=60):

        # Opening gRPC channel
        self.channel = grpc.insecure_channel(env_address)
        self.stub = interface_pb2_grpc.EnvServerStub(self.channel)

        # Wait for grpc server to be ready
        print("Trying to connect to DIAMBRA Engine server (timeout={}s)...".format(grpc_timeout))
        try:
            grpc.channel_ready_future(self.channel).result(timeout=grpc_timeout)
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
            "p1": [env_settings["characters"][0][0], env_settings["characters"][0][1], env_settings["characters"][0][2]],
            "p2": [env_settings["characters"][1][0], env_settings["characters"][1][1], env_settings["characters"][1][2]]
        }
        outfits = {
            "p1": env_settings["char_outfits"][0],
            "p2": env_settings["char_outfits"][1]
        }
        frame_shape = {
            "h": env_settings["frame_shape"][0],
            "w": env_settings["frame_shape"][1],
            "c": env_settings["frame_shape"][2]
        }
        action_spaces = {
            "p1": interface_pb2.ACTION_SPACE_DISCRETE if env_settings["action_space"][0] == "discrete" else interface_pb2.ACTION_SPACE_MULTI_DISCRETE,
            "p2": interface_pb2.ACTION_SPACE_DISCRETE if env_settings["action_space"][1] == "discrete" else interface_pb2.ACTION_SPACE_MULTI_DISCRETE,
        }
        attack_buttons_combinations = {
            "p1": env_settings["attack_but_combination"][0],
            "p2": env_settings["attack_but_combination"][1]
        }
        super_arts = {
            "p1": env_settings["super_art"][0],
            "p2": env_settings["super_art"][1]
        }
        fighting_styles = {
            "p1": env_settings["fighting_style"][0],
            "p2": env_settings["fighting_style"][1]
        }
        ultimate_styles = {
            "p1": {
                "dash": env_settings["ultimate_style"][0][0],
                "evade": env_settings["ultimate_style"][0][1],
                "bar": env_settings["ultimate_style"][0][2]
            },
            "p2": {
                "dash": env_settings["ultimate_style"][1][0],
                "evade": env_settings["ultimate_style"][1][1],
                "bar": env_settings["ultimate_style"][1][2]
            }
        }

        request = interface_pb2.EnvSettings(
            game_id=env_settings["game_id"],
            continue_game=env_settings["continue_game"],
            show_final=env_settings["show_final"],
            step_ratio=env_settings["step_ratio"],
            player=env_settings["player"],
            difficulty=env_settings["difficulty"],
            characters=characters,
            outfits=outfits,
            frame_shape=frame_shape,
            action_spaces=action_spaces,
            attack_buttons_combinations=attack_buttons_combinations,
            hardcore=env_settings["hardcore"],
            disable_keyboard=env_settings["disable_keyboard"],
            disable_joystick=env_settings["disable_joystick"],
            rank=env_settings["rank"],
            random_seed=env_settings["seed"],
            super_arts=super_arts,
            tower=env_settings["tower"],
            fighting_styles=fighting_styles,
            ultimate_styles=ultimate_styles
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
        for idx in range(0, len(response.button_mapping.moves), 2):
            move_dict[int(response.button_mapping.moves[idx])] = response.button_mapping.moves[idx + 1]
        att_dict = {}
        for idx in range(0, len(response.button_mapping.attacks), 2):
            att_dict[int(response.button_mapping.attacks[idx])] = response.button_mapping.attacks[idx + 1]

        env_info_dict = {
            "n_actions": [[response.available_actions.with_buttons_combination.moves,
                           response.available_actions.with_buttons_combination.attacks],
                          [response.available_actions.without_buttons_combination.moves,
                           response.available_actions.without_buttons_combination.attacks]],
            "frame_shape": [response.frame_shape.h, response.frame_shape.w, response.frame_shape.c],
            "delta_health": response.delta_health,
            "max_stage": response.max_stage,
            "cumulative_reward_bounds": [response.cumulative_reward_bounds.min, response.cumulative_reward_bounds.max],
            "char_list": list(response.char_list),
            "actions_list": [list(response.buttons.moves), list(response.buttons.attacks)],
            "actions_dict": [move_dict, att_dict],
            "ram_states": response.ram_states
        }

        # Set frame size
        self.height = env_info_dict["frame_shape"][0]
        self.width = env_info_dict["frame_shape"][1]
        self.n_chan = env_info_dict["frame_shape"][2]
        self.frame_dim = self.height * self.width * self.n_chan

        return env_info_dict

    # Read data
    def read_data(self, response):

        # Adding boolean flags
        data = {"round_done": response.game_state.round_done,
                "stage_done": response.game_state.stage_done,
                "game_done": response.game_state.game_done,
                "ep_done": response.game_state.episode_done}

        # Adding int variables
        # Actions
        data["moveActionP1"] = response.actions.p1.move
        data["attackActionP1"] = response.actions.p1.attack
        data["moveActionP2"] = response.actions.p2.move
        data["attackActionP2"] = response.actions.p2.attack

        # Ram states
        for k, v in response.ram_states.items():
            data[k] = v.val

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
        data = self.read_data(response)
        frame = self.read_frame(response.frame)
        return frame, data, response.player

    # Step the environment (1P) [pb low level]
    def _step_1p(self, mov_p1, att_p1):
        actions = interface_pb2.Actions()
        actions.p1.move = mov_p1
        actions.p1.attack = att_p1
        return self.stub.Step1P(actions)

    # Step the environment (1P)
    def step_1p(self, mov_p1, att_p1):
        response = self._step_1p(mov_p1, att_p1)
        data = self.read_data(response)
        frame = self.read_frame(response.frame)
        return frame, response.reward, data

    # Step the environment (2P) [pb low level]
    def _step_2p(self, mov_p1, att_p1, mov_p2, att_p2):
        actions = interface_pb2.Actions()
        actions.p1.move = mov_p1
        actions.p1.attack = att_p1
        actions.p2.move = mov_p2
        actions.p2.attack = att_p2
        return self.stub.Step2P(actions)

    # Step the environment (2P)
    def step_2p(self, mov_p1, att_p1, mov_p2, att_p2):
        response = self._step_2p(mov_p1, att_p1, mov_p2, att_p2)
        data = self.read_data(response)
        frame = self.read_frame(response.frame)
        return frame, response.reward, data

    # Closing DIAMBRA Arena
    def close(self):
        response = self.stub.Close(interface_pb2.Empty())
        self.channel.close()
        return response
