import numpy as np

from ..utils.splash_screen import SplashScreen
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

        # Splash Screen
        SplashScreen()

    # Transforming env kwargs to string
    def env_settings_to_string(self, env_settings):

        max_char_to_select = 3
        sep = ","
        end_char = "+"

        output = ""

        output += "gameId" + sep+"2"+sep + env_settings["game_id"] + sep
        output += "continueGame" + sep+"3"+sep + \
            str(env_settings["continue_game"]) + sep
        output += "showFinal" + sep+"0"+sep + \
            str(int(env_settings["show_final"])) + sep
        output += "stepRatio" + sep+"1"+sep + \
            str(env_settings["step_ratio"]) + sep
        output += "player" + sep+"2"+sep + env_settings["player"] + sep
        output += "difficulty" + sep+"1"+sep + \
            str(env_settings["difficulty"]) + sep
        output += "character1" + sep+"2"+sep + \
            env_settings["characters"][0][0] + sep
        output += "character2" + sep+"2"+sep + \
            env_settings["characters"][1][0] + sep
        for i_char in range(1, max_char_to_select):
            output += "character1_{}".format(i_char+1) + sep + \
                "2"+sep + env_settings["characters"][0][i_char] + sep
            output += "character2_{}".format(i_char+1) + sep + \
                "2"+sep + env_settings["characters"][1][i_char] + sep
        output += "charOutfits1" + sep+"1"+sep + \
            str(env_settings["char_outfits"][0]) + sep
        output += "charOutfits2" + sep+"1"+sep + \
            str(env_settings["char_outfits"][1]) + sep
        output += "frameShape1" + sep+"1"+sep + \
            str(env_settings["frame_shape"][0]) + sep
        output += "frameShape2" + sep+"1"+sep + \
            str(env_settings["frame_shape"][1]) + sep
        output += "frameShape3" + sep+"1"+sep + \
            str(env_settings["frame_shape"][2]) + sep

        # SFIII Specific
        output += "superArt1" + sep+"1"+sep + \
            str(env_settings["super_art"][0]) + sep
        output += "superArt2" + sep+"1"+sep + \
            str(env_settings["super_art"][1]) + sep
        # UMK3 Specific
        output += "tower" + sep+"1"+sep + str(env_settings["tower"]) + sep
        # KOF Specific
        output += "fightingStyle1" + sep+"1"+sep + \
            str(env_settings["fighting_style"][0]) + sep
        output += "fightingStyle2" + sep+"1"+sep + \
            str(env_settings["fighting_style"][1]) + sep
        for idx in range(2):
            output += "ultimateStyleDash" + \
                str(idx+1) + sep+"1"+sep + \
                str(env_settings["ultimate_style"][idx][0]) + sep
            output += "ultimateStyleEvade" + \
                str(idx+1) + sep+"1"+sep + \
                str(env_settings["ultimate_style"][idx][1]) + sep
            output += "ultimateStyleBar" + \
                str(idx+1) + sep+"1"+sep + \
                str(env_settings["ultimate_style"][idx][2]) + sep

        output += "disableKeyboard" + sep+"0"+sep + \
            str(int(env_settings["disable_keyboard"])) + sep
        output += "disableJoystick" + sep+"0"+sep + \
            str(int(env_settings["disable_joystick"])) + sep
        output += "rank" + sep+"1"+sep + str(env_settings["rank"]) + sep
        output += "recordConfigFile" + sep+"2"+sep + \
            env_settings["record_config_file"] + sep

        output += end_char

        return output

    # Send env settings, retrieve env info and int variables list
    def env_init(self, env_settings):
        env_settings_string = self.env_settings_to_string(env_settings)
        response = self.stub.EnvInit(
            interface_pb2.EnvSettings(settings=env_settings_string))
        self.int_data_vars_list = response.intDataList.split(",")
        self.int_data_vars_list.remove("")
        return response.envInfo.split(",")

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

    # Reset the environment
    def reset(self):
        response = self.stub.Reset(interface_pb2.Empty())
        data = self.read_data(response.intVar, response.doneConditions)
        frame = self.read_frame(response.frame)
        return frame, data, response.player

    # Step the environment (1P)
    def step_1p(self, mov_p1, att_p1):
        command = interface_pb2.Command()
        command.P1.mov = mov_p1
        command.P1.att = att_p1
        response = self.stub.Step1P(command)
        data = self.read_data(response.intVar, response.doneConditions)
        frame = self.read_frame(response.frame)
        return frame, data

    # Step the environment (2P)
    def step_2p(self, mov_p1, att_p1, mov_p2, att_p2):
        command = interface_pb2.Command()
        command.P1.mov = mov_p1
        command.P1.att = att_p1
        command.P2.mov = mov_p2
        command.P2.att = att_p2
        response = self.stub.Step2P(command)
        data = self.read_data(response.intVar, response.doneConditions)
        frame = self.read_frame(response.frame)
        return frame, data

    # Closing DIAMBRA Arena
    def close(self):
        self.stub.Close(interface_pb2.Empty())
        self.channel.close()
