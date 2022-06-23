import os
import numpy as np
from threading import Thread, Event
from collections import defaultdict
from inputs import devices
import pickle
from os.path import expanduser
home_dir = expanduser("~")

# Function to retrieve available GamePads and select one


def available_gamepads():

    print("Available USB gamepads:\n")

    for idx, gamepad in enumerate(devices.gamepads):
        print("Gamepad {}: {}".format(idx, gamepad))

# Class to manage gampad


class DiambraGamepad(Thread):  # def class typr thread
    def __init__(self, action_list=(("NoMove", "Left", "UpLeft", "Up",
                                     "UpRight", "Right", "DownRight",
                                     "Down", "DownLeft"),
                                    ("But0", "But1", "But2", "But3",
                                     "But4", "But5", "But6", "But7",
                                     "But8")),
                 cfg=["But1", "But2", "But3", "But4",
                      "But5", "But6", "But7", "But8"],
                 gamepad_num=0, force=False, skip_configure=False):
        # thread init class (don't forget this)
        Thread.__init__(self, daemon=True)

        self.stop_event = Event()

        self.start_code = ""
        self.select_code = ""
        self.start_but = 0
        self.select_but = 0
        self.event_hash_move = np.zeros(4)
        self.event_hash_attack = np.zeros(8)
        self.gamepad_config_file_name = os.path.join(
            home_dir, '.diambra/config/gamepadConfig.cfg')

        self.all_actions_list = (("NoMove", "Left", "UpLeft", "Up", "UpRight",
                                  "Right", "DownRight", "Down", "DownLeft"),
                                 ("But0", "But1", "But2", "But3", "But4",
                                  "But5", "But6", "But7", "But8"))
        self.action_list = action_list

        self.cfg = cfg
        self.gamepad_num = gamepad_num

        self.initaction_list(self.action_list)

        try:
            self.gamepad = devices.gamepads[self.gamepad_num]
        except IndexError:
            raise Exception("No gamepad found.")

        print("Initializing gamepad # {}, named: {}".format(
            self.gamepad_num, self.gamepad))

        configure = False

        if not skip_configure:
            if force:
                configure = True
            else:
                if not self.load_gamepad_configuration():
                    configure = True

        if configure:
            # Run gamepad configuration
            self.configure()

            configuration_ok = False
            while configuration_ok is False:

                ans = input("Want to test the configuration? (n/y): ")

                if ans == "y":
                    self.initaction_list(self.all_actions_list)
                    self.config_test()
                    self.initaction_list(self.action_list)

                    ans = input("Want to reconfigure the GamePad? (y/n): ")
                    if ans == "y":
                        print("Restarting GamePad configuration")
                        # Run gamepad configuration
                        self.configure()
                    else:
                        configuration_ok = True
                else:
                    configuration_ok = True

            self.save_gamepad_configuration()

        print("Diambra GamePad initialized on device # {}, named: {}".format(
            self.gamepad_num, self.gamepad))

    # Show gamepad events
    def show_gamepad_events(self, event_codes_to_skip=[],
                            event_code_to_show=None):

        print("Use Gamepad to see events")
        while True:
            for event in self.gamepad.read():
                if event.ev_type != "Sync" and event.ev_type != "Misc":
                    if event.code not in event_codes_to_skip:
                        if event_code_to_show is not None:
                            if event.code != event_code_to_show:
                                continue
                        print("{} {}".format(event.code, event.state))

    # Prepare gamepad config dict to be saved
    def process_gamepad_dict_for_save(self):

        cfg_dict_to_save = {}
        cfg_dict_to_save["name"] = self.gamepad.name

        # Keys
        key_list_dict = []
        for key, value in self.gamepad_dict["Key"].items():
            key_list_dict.append([key, value])

        cfg_dict_to_save["key_valuesList"] = key_list_dict

        # Start and select
        start_select_list = ["", ""]
        start_select_list[0] = self.start_code
        start_select_list[1] = self.select_code

        cfg_dict_to_save["start_select_list"] = start_select_list

        # Digital and Analog moves
        abs_list_dict_digital = []
        abs_list_dict_analog = []
        for key1, value1 in self.gamepad_dict["Absolute"].items():

            if "ABS_HAT0" in key1:
                # Digital moves
                for key2, value2 in self.gamepad_dict["Absolute"][key1].items():
                    abs_list_dict_digital.append([key1, key2, value2[0]])

            else:
                # Analog moves
                abs_list_dict_analog.append(
                    [key1, value1[0], value1[1], value1[2], value1[3]])

        cfg_dict_to_save["absoluteValuesListDigital"] = abs_list_dict_digital
        cfg_dict_to_save["absoluteValuesListAnalog"] = abs_list_dict_analog

        return cfg_dict_to_save

    # Save gamepad configuration
    def save_gamepad_configuration(self):

        print("Saving configuration in {}".format(self.gamepad_config_file_name))

        # Convert gamepad config dictionary
        cfg_dict_to_save = self.process_gamepad_dict_for_save()

        # Load all gamepads configuration
        self.load_all_gamepad_configurations()

        # Append all previous configurations but this one
        new_cfg_file_dict_list = []
        for cfg_file_dict in self.cfg_file_dict_list:
            if cfg_file_dict["name"] != self.gamepad.name:
                new_cfg_file_dict_list.append(cfg_file_dict)
        cfg_file_dict_list = new_cfg_file_dict_list

        cfg_file_dict_list.append(cfg_dict_to_save)

        # Open file (new or overwrite previous one)
        cfg_file = open(self.gamepad_config_file_name, "wb")
        pickle.dump(cfg_file_dict_list, cfg_file)
        cfg_file.close()

    # Load all gamepads configuration
    def load_all_gamepad_configurations(self):

        try:
            cfg_file = open(self.gamepad_config_file_name, "rb")

            # Load Pickle Dict
            cfg_file_dict_list = pickle.load(cfg_file)

            cfg_file.close()

        except OSError:
            print("No gamepad configuration file found in: {}".format(
                os.path.join(home_dir, '.diambra/config/')))
            config_file_folder = os.path.join(home_dir, '.diambra/')
            os.makedirs(config_file_folder, exist_ok=True)
            config_file_folder = os.path.join(home_dir, '.diambra/config/')
            os.makedirs(config_file_folder, exist_ok=True)
            cfg_file_dict_list = []

        self.cfg_file_dict_list = cfg_file_dict_list

    # Load gamepad configuration
    def load_gamepad_configuration(self):

        config_found = False

        # Read all gamepads configurations
        self.load_all_gamepad_configurations()

        # Loop among all stored GamePads
        for cfg_file_dict in self.cfg_file_dict_list:
            if cfg_file_dict["name"] == self.gamepad.name:

                try:
                    # Initialize GamePad dict
                    self.gamepad_dict = {}
                    self.gamepad_dict["Key"] = defaultdict(lambda: 7)
                    self.gamepad_dict["Absolute"] = defaultdict(
                        lambda: defaultdict(lambda: [[], 0]))
                    self.gamepad_dict["Absolute"]["ABS_HAT0Y"] = defaultdict(
                        lambda: [[], 0])  # No-op action = 0
                    self.gamepad_dict["Absolute"]["ABS_HAT0X"] = defaultdict(
                        lambda: [[], 0])  # No-op action = 0
                    self.gamepad_dict["Absolute"]["ABS_HAT0Y"][0] = [[0, 2], 0]
                    self.gamepad_dict["Absolute"]["ABS_HAT0X"][0] = [[1, 3], 0]

                    # Read Start/Select info
                    self.start_code = cfg_file_dict["start_select_list"][0]
                    self.select_code = cfg_file_dict["start_select_list"][1]

                    # Read "Key" info
                    for item in cfg_file_dict["key_valuesList"]:
                        self.gamepad_dict["Key"][item[0]] = item[1]

                    # Read "Absolute" info DIGITAL
                    for item in cfg_file_dict["absoluteValuesListDigital"]:
                        self.gamepad_dict["Absolute"][item[0]][item[1]] = [item[2],
                                                                           abs(item[1])]

                    # Read "Absolute" info ANALOG
                    for item in cfg_file_dict["absoluteValuesListAnalog"]:
                        self.gamepad_dict["Absolute"][item[0]] = [
                            item[1], item[2], item[3], item[4]]

                    config_found = True
                    print("Gamepad configuration file found in: {}".format(
                        os.path.join(home_dir, '.diambra/config/')))
                    print("Gamepad configuration file loaded.")
                except:
                    print("Invalid gamepad configuration file found in: {}".format(
                        os.path.join(home_dir, '.diambra/config/')))

        if not config_found:
            print(
                "Configuration for this gamepad not present in gamepad configuration file")

        return config_found

    # Configure GamePad buttons
    def configure(self):

        print("")
        print("")
        print("Configuring gamepad {}".format(self.gamepad))
        print("")
        print("# Buttons CFG file")
        print("               _______            ")
        print("      B7    __|digital|__   B8    ")
        print("      B5      |buttons|     B6    ")
        print("                /    \            ")
        print("                            B1    ")
        print("      |     SELECT  START         ")
        print("   --   --              B4      B2")
        print("      |      -                    ")
        print(" __/____   ( + )            B3    ")
        print("|digital|    -                    ")
        print("| move  |      \______            ")
        print(" -------       |analog|           ")
        print("               | move |           ")
        print("                ------            ")
        print("")
        print("NB: Be sure to have your analog switch on before starting.")
        print("")

        self.gamepad_dict = {}
        self.gamepad_dict["Key"] = defaultdict(lambda: 7)
        self.gamepad_dict["Absolute"] = defaultdict(
            lambda: defaultdict(lambda: [[], 0]))

        # Buttons configuration

        # Start and Select
        print("Press START button")
        but_not_set = True
        while but_not_set:
            for event in self.gamepad.read():
                if event.ev_type == "Key":
                    if event.state == 1:
                        self.start_code = event.code
                        print("Start associated with {}".format(event.code))
                    else:
                        but_not_set = False
                        break

        print("Press SELECT button (Start to skip)")
        but_not_set = True
        while but_not_set:
            for event in self.gamepad.read():
                if event.ev_type == "Key":
                    if event.code != self.start_code and event.state == 1:
                        self.select_code = event.code
                        print("Select associated with {}".format(event.code))
                    else:
                        but_not_set = False
                        if event.code == self.start_code:
                            print("Select association skipped")
                        break

        # Attack buttons
        end_flag = False
        for idx in range(8):

            if end_flag:
                break

            print("Press B{} button (Select / Start to end configuration)".format(idx+1))

            but_not_set = True

            while but_not_set:

                if end_flag:
                    break

                for event in self.gamepad.read():
                    if event.ev_type == "Key":
                        if (event.code != self.start_code
                                and event.code != self.select_code):
                            if event.state == 1:
                                print("Button B{}, event code = {}".format(
                                    idx+1, event.code))
                                self.gamepad_dict["Key"][event.code] = idx
                            elif event.state == 0:
                                but_not_set = False
                        else:
                            if event.state == 0:
                                print("Remaining buttons configuration skipped")
                                end_flag = True
                                break

        # Move sticks
        # Digital
        end_flag = False
        print("Configuring digital move")
        moves_list = ["UP", "RIGHT", "DOWN", "LEFT"]
        event_codes_list = ["Y", "X", "Y", "X"]
        self.gamepad_dict["Absolute"]["ABS_HAT0Y"] = defaultdict(lambda: [
                                                                [], 0])
        self.gamepad_dict["Absolute"]["ABS_HAT0X"] = defaultdict(lambda: [
                                                                [], 0])
        self.gamepad_dict["Absolute"]["ABS_HAT0Y"][0] = [[0, 2], 0]
        self.gamepad_dict["Absolute"]["ABS_HAT0X"][0] = [[1, 3], 0]

        for idx, move in enumerate(moves_list):

            if end_flag:
                break

            print("Press {} arrow (Start / Select to skip)".format(move))

            but_not_set = True

            while but_not_set:

                if end_flag:
                    break

                for event in self.gamepad.read():

                    if event.ev_type == "Absolute":
                        if event.code == "ABS_HAT0" + event_codes_list[idx]:
                            if abs(event.state) == 1:
                                print("{} move event code = {}, event state = {}".format(
                                    move, event.code, event.state))
                                self.gamepad_dict["Absolute"][event.code][event.state] = [
                                    idx, abs(event.state)]
                            elif event.state == 0:
                                but_not_set = False
                            else:
                                print("Digital Move Stick assumes not admissible values: {}".format(
                                    event.state))
                                print(
                                    "Digital Move Stick not supported, configuration skipped")
                                end_flag = True
                                break
                    else:
                        if (event.code == self.start_code
                                or event.code == self.select_code):
                            if event.state == 0:
                                print("Digital Move Stick configuration skipped")
                                end_flag = True
                                break

        # Move sticks
        # Analog
        print("Configuring analog move")
        moves_list = ["UP", "RIGHT", "DOWN", "LEFT"]
        event_codes_list = ["Y", "X", "Y", "X"]
        self.max_analog_val = {}
        self.origin_analog_val = {}

        for idx, move in enumerate(moves_list):

            print(
                "Move left analog in {} position, keep it there and press Start".format(move))

            but_not_set = True

            self.max_analog_val[move] = 0

            while but_not_set:

                for event in self.gamepad.read():

                    if event.ev_type == "Absolute":
                        if event.code == "ABS_" + event_codes_list[idx]:
                            self.max_analog_val[move] = event.state
                    else:
                        if event.code == self.start_code:
                            if event.state == 0:
                                but_not_set = False
                                break

        # Setting origin value, analog at rest
        for idx in range(2):
            self.origin_analog_val[moves_list[idx]] = int(
                (self.max_analog_val[moves_list[idx]] +
                 self.max_analog_val[moves_list[idx+2]]) / 2.0)
            self.origin_analog_val[moves_list[idx+2]] = self.origin_analog_val[moves_list[idx]]

        # Setting threshold to discriminate between analog values
        thresh_perc = 0.5
        self.delta_perc = {}
        for idx in range(2):
            self.delta_perc[idx] = (self.max_analog_val[moves_list[idx]] -
                                    self.origin_analog_val[moves_list[idx]]) * thresh_perc
            self.delta_perc[idx+2] = -self.delta_perc[idx]

        print("Delta perc = ", self.delta_perc)

        # Addressing Y-X axis
        for idx in range(2):
            print("{} move event code = ABS_{}, ".format(moves_list[idx],
                                                         event_codes_list[idx]) +
                  "event state = {}".format(self.max_analog_val[moves_list[idx]]))
            print("{} move event code = ABS_{}, ".format(moves_list[idx+2],
                                                         event_codes_list[idx+2]) +
                  " event state = {}".format(self.max_analog_val[moves_list[idx+2]]))
            print("NO {}-{} move event code =".format(moves_list[idx],
                                                      moves_list[idx+2]) +
                  " ABS_{}, ".format(event_codes_list[idx]) +
                  "event state = {}".format(self.origin_analog_val[moves_list[idx]]))

            event_code = "ABS_{}".format(event_codes_list[idx])
            if self.delta_perc[idx] > 0:
                self.gamepad_dict["Absolute"][event_code] = [
                    [self.origin_analog_val[moves_list[idx]] - self.delta_perc[idx],
                        self.origin_analog_val[moves_list[idx]] + self.delta_perc[idx]],
                    [[idx+2], 1], [[idx, idx+2], 0], [[idx], 1]]

            elif self.delta_perc[idx] < 0:
                self.gamepad_dict["Absolute"][event_code] = [
                    [self.origin_analog_val[moves_list[idx]] - self.delta_perc[idx+2],
                        self.origin_analog_val[moves_list[idx]] + self.delta_perc[idx+2]],
                    [[idx], 1], [[idx, idx+2], 0], [[idx+2], 1]]

            else:
                print(
                    "Not admissible values found in analog stick configuration, skipping")

        print("Gamepad dict : ")
        print("Buttons (Keys) dict : ", self.gamepad_dict["Key"])
        print("Moves (Absolute) dict : ", self.gamepad_dict["Absolute"])

        print("Configuration completed.")

        return

    # Configuration Test
    def config_test(self):

        print("Press Start to end configuration test")

        # Execute run function in thread mode
        thread = Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

        while True:

            actions = self.get_all_actions()

            if actions[0] != 0:
                print("Move action = {}. (Press START to end configuration test).".format(
                    self.all_actions_list[0][actions[0]]))
            if actions[1] != 0:
                print("Attack action = {}. (Press START to end configuration test).".format(
                    self.all_actions_list[1][actions[1]]))
            if actions[2] != 0:
                break

    # Creating hash dictionary
    def compose_hash_dict(self, dictionary, hash_elem):

        key_val_list = []
        key_val = ""

        for idx, elem in enumerate(hash_elem):

            if elem == 1:
                key_val_list.append(self.cfg[idx])

        for elem in sorted(key_val_list):
            key_val += elem

        dictionary[key_val] = hash_elem

    # Initializa action list
    def initaction_list(self, action_list):

        self.action_dict_move = defaultdict(lambda: 0)  # No-op action = 0
        self.action_dict_attack = defaultdict(lambda: 0)  # No-op action = 0

        move_action_name_to_hash_dict = {}
        move_action_name_to_hash_dict["NoMove"] = [0, 0, 0, 0]
        move_action_name_to_hash_dict["Up"] = [1, 0, 0, 0]
        move_action_name_to_hash_dict["Right"] = [0, 1, 0, 0]
        move_action_name_to_hash_dict["Down"] = [0, 0, 1, 0]
        move_action_name_to_hash_dict["Left"] = [0, 0, 0, 1]
        move_action_name_to_hash_dict["UpLeft"] = [1, 0, 0, 1]
        move_action_name_to_hash_dict["UpRight"] = [1, 1, 0, 0]
        move_action_name_to_hash_dict["DownRight"] = [0, 1, 1, 0]
        move_action_name_to_hash_dict["DownLeft"] = [0, 0, 1, 1]

        attack_action_name_to_hash_dict = {}
        attack_action_name_to_hash_dict["But0"] = [0, 0, 0, 0, 0, 0, 0, 0]

        # 1 button pressed
        for idx in range(8):
            hash_elem = [0, 0, 0, 0, 0, 0, 0, 0]
            hash_elem[idx] = 1
            self.compose_hash_dict(attack_action_name_to_hash_dict, hash_elem)

        # 2 buttons pressed
        for idx in range(8):
            for idy in range(idx+1, 8):
                hash_elem = [0, 0, 0, 0, 0, 0, 0, 0]
                hash_elem[idx] = 1
                hash_elem[idy] = 1
                self.compose_hash_dict(attack_action_name_to_hash_dict, hash_elem)

        # 3 buttons pressed
        for idx in range(8):
            for idy in range(idx+1, 8):
                for idz in range(idy+1, 8):
                    hash_elem = [0, 0, 0, 0, 0, 0, 0, 0]
                    hash_elem[idx] = 1
                    hash_elem[idy] = 1
                    hash_elem[idz] = 1
                    self.compose_hash_dict(attack_action_name_to_hash_dict, hash_elem)

        # Move actions
        for idx, action in enumerate(action_list[0]):

            hash_val = move_action_name_to_hash_dict[action]
            self.action_dict_move[tuple(hash_val)] = idx

        # Attack actions
        for idx, action in enumerate(action_list[1]):

            hash_val = attack_action_name_to_hash_dict[action]
            self.action_dict_attack[tuple(hash_val)] = idx

    # Retrieve all gamepad actions
    def get_all_actions(self):
        return [self.action_dict_move[tuple(self.event_hash_move)],
                self.action_dict_attack[tuple(self.event_hash_attack)],
                self.start_but, self.select_but]

    # Retrieve gamepad actions
    def get_actions(self):
        return self.get_all_actions()[0:2]

    # Retrieve gamepad events
    def run(self):      # run is a default Thread function
        while not self.stop_event.is_set():   # loop until stop is called
            for event in self.gamepad.read():   # check events of gamepads, if not event, all is stop
                if event.ev_type == "Key":   # category of binary respond values

                    # Select
                    if event.code == self.select_code:
                        self.select_but = event.state
                    # Start
                    elif event.code == self.start_code:
                        self.start_but = event.state
                    else:
                        self.event_hash_attack[self.gamepad_dict[event.ev_type]
                                               [event.code]] = event.state

                # category of move values (digital moves)
                elif "ABS_HAT0" in event.code:

                    idx = self.gamepad_dict[event.ev_type][event.code][event.state][0]
                    event_state = self.gamepad_dict[event.ev_type][event.code][event.state][1]
                    self.event_hash_move[idx] = event_state

                # category of move values (analog left stick)
                elif event.code == "ABS_X" or event.code == "ABS_Y":

                    thresh_values = self.gamepad_dict[event.ev_type][event.code][0]
                    min_act = self.gamepad_dict[event.ev_type][event.code][1]
                    centr_act = self.gamepad_dict[event.ev_type][event.code][2]
                    max_act = self.gamepad_dict[event.ev_type][event.code][3]

                    if event.state < thresh_values[0]:
                        idx = min_act[0]
                        event_state = min_act[1]
                    elif event.state > thresh_values[1]:
                        idx = max_act[0]
                        event_state = max_act[1]
                    else:
                        idx = centr_act[0]
                        event_state = centr_act[1]

                    for elem in idx:
                        self.event_hash_move[elem] = event_state

    # Stop the thread
    def stop(self):
        self.stop_event.set()
