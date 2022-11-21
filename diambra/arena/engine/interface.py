import numpy as np
import os
import logging

from diambra.engine import Client, model
import grpc

CONNECTION_FAILED_ERROR_TEXT = """DIAMBRA Arena failed to connect to the Engine Server.
 - If you are running a Python script, are you running with DIAMBRA CLI: `diambra run python script.py`?
 - If you are running a Python Notebook, have you started Jupyter Notebook with DIAMBRA CLI: `diambra run jupyter notebook`?

See the docs (https://docs.diambra.ai) for additional details, or join DIAMBRA Discord Server (https://discord.gg/tFDS2UN5sv) for support."""

# DIAMBRA Env Gym
class DiambraEngine:
    """Diambra Environment gym interface"""

    def __init__(self, env_address, grpc_timeout=60):
        self.logger = logging.getLogger(__name__)

        try:
            # Opening gRPC channel
            self.client = Client(env_address, grpc_timeout)
            self.logger.info("Trying to connect to DIAMBRA Engine server (timeout={}s)...".format(grpc_timeout))
        except grpc.FutureTimeoutError as e:
            raise Exception(CONNECTION_FAILED_ERROR_TEXT) from e

        self.logger.info("... done.")

        # Splash Screen
        if 'DISPLAY' in os.environ:
            from ..utils.splash_screen import SplashScreen
            SplashScreen()

    # Transforming env settings dict to pb request
    def env_settings_to_pb_request(self, env_settings):

        frame_shape = {
            "h": env_settings.frame_shape[0],
            "w": env_settings.frame_shape[1],
            "c": env_settings.frame_shape[2]
        }

        if env_settings.player == "P1P2":
            characters = {
                "p1": [env_settings.characters[0][0], env_settings.characters[0][1], env_settings.characters[0][2]],
                "p2": [env_settings.characters[1][0], env_settings.characters[1][1], env_settings.characters[1][2]]
            }
            outfits = {
                "p1": env_settings.char_outfits[0],
                "p2": env_settings.char_outfits[1]
            }
            action_spaces = {
                "p1": model.ACTION_SPACE_DISCRETE if env_settings.action_space[0] == "discrete" else model.ACTION_SPACE_MULTI_DISCRETE,
                "p2": model.ACTION_SPACE_DISCRETE if env_settings.action_space[1] == "discrete" else model.ACTION_SPACE_MULTI_DISCRETE,
            }
            attack_buttons_combinations = {
                "p1": env_settings.attack_but_combination[0],
                "p2": env_settings.attack_but_combination[1]
            }
            super_arts = {
                "p1": env_settings.super_art[0],
                "p2": env_settings.super_art[1]
            }
            fighting_styles = {
                "p1": env_settings.fighting_style[0],
                "p2": env_settings.fighting_style[1]
            }
            ultimate_styles = {
                "p1": {
                    "dash": env_settings.ultimate_style[0][0],
                    "evade": env_settings.ultimate_style[0][1],
                    "bar": env_settings.ultimate_style[0][2]
                },
                "p2": {
                    "dash": env_settings.ultimate_style[1][0],
                    "evade": env_settings.ultimate_style[1][1],
                    "bar": env_settings.ultimate_style[1][2]
                }
            }
        else:
            characters = {
                "p1": [env_settings.characters[0], env_settings.characters[1], env_settings.characters[2]],
                "p2": [env_settings.characters[0], env_settings.characters[1], env_settings.characters[2]]
            }
            outfits = {
                "p1": env_settings.char_outfits,
                "p2": env_settings.char_outfits
            }
            action_spaces = {
                "p1": model.ACTION_SPACE_DISCRETE if env_settings.action_space == "discrete" else model.ACTION_SPACE_MULTI_DISCRETE,
                "p2": model.ACTION_SPACE_DISCRETE if env_settings.action_space == "discrete" else model.ACTION_SPACE_MULTI_DISCRETE,
            }
            attack_buttons_combinations = {
                "p1": env_settings.attack_but_combination,
                "p2": env_settings.attack_but_combination
            }
            super_arts = {
                "p1": env_settings.super_art,
                "p2": env_settings.super_art
            }
            fighting_styles = {
                "p1": env_settings.fighting_style,
                "p2": env_settings.fighting_style
            }
            ultimate_styles = {
                "p1": {
                    "dash": env_settings.ultimate_style[0],
                    "evade": env_settings.ultimate_style[1],
                    "bar": env_settings.ultimate_style[2]
                },
                "p2": {
                    "dash": env_settings.ultimate_style[0],
                    "evade": env_settings.ultimate_style[1],
                    "bar": env_settings.ultimate_style[2]
                }
            }

        request = model.EnvSettings(
            game_id=env_settings.game_id,
            continue_game=env_settings.continue_game,
            show_final=env_settings.show_final,
            step_ratio=env_settings.step_ratio,
            player=env_settings.player,
            difficulty=env_settings.difficulty,
            characters=characters,
            outfits=outfits,
            frame_shape=frame_shape,
            action_spaces=action_spaces,
            attack_buttons_combinations=attack_buttons_combinations,
            hardcore=env_settings.hardcore,
            disable_keyboard=env_settings.disable_keyboard,
            disable_joystick=env_settings.disable_joystick,
            rank=env_settings.rank,
            random_seed=env_settings.seed,
            super_arts=super_arts,
            tower=env_settings.tower,
            fighting_styles=fighting_styles,
            ultimate_styles=ultimate_styles
        )

        return request

    # Send env settings, retrieve env info and int variables list [pb low level]
    def _env_init(self, env_settings_pb):
        try:
            response = self.client.EnvInit(env_settings_pb)
        except:
            try:
                response = self.client.GetError(model.Empty())
                exceptionMessage = "Received error message from engine: " + response.errorMessage
                self.logger.error(exceptionMessage)
            except:
                raise Exception(CONNECTION_FAILED_ERROR_TEXT)

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
                "ep_done": response.game_state.episode_done,
                "env_done": response.game_state.env_done}

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
        return self.client.Reset(model.Empty())

    # Reset the environment
    def reset(self):
        response = self._reset()
        data = self.read_data(response)
        frame = self.read_frame(response.frame)
        return frame, data, response.player

    # Step the environment (1P) [pb low level]
    def _step_1p(self, mov_p1, att_p1):
        actions = model.Actions()
        actions.p1.move = mov_p1
        actions.p1.attack = att_p1
        return self.client.Step1P(actions)

    # Step the environment (1P)
    def step_1p(self, mov_p1, att_p1):
        response = self._step_1p(mov_p1, att_p1)
        data = self.read_data(response)
        frame = self.read_frame(response.frame)
        return frame, response.reward, data

    # Step the environment (2P) [pb low level]
    def _step_2p(self, mov_p1, att_p1, mov_p2, att_p2):
        actions = model.Actions()
        actions.p1.move = mov_p1
        actions.p1.attack = att_p1
        actions.p2.move = mov_p2
        actions.p2.attack = att_p2
        return self.client.Step2P(actions)

    # Step the environment (2P)
    def step_2p(self, mov_p1, att_p1, mov_p2, att_p2):
        response = self._step_2p(mov_p1, att_p1, mov_p2, att_p2)
        data = self.read_data(response)
        frame = self.read_frame(response.frame)
        return frame, response.reward, data

    # Closing DIAMBRA Arena
    def close(self):
        response = self.client.Close(model.Empty())
        self.client.channel.close()
        return response
