import os
import numpy as np
from threading import Thread, Event
from collections import defaultdict
from inputs import devices
import pickle
from os.path import expanduser
import logging

home_dir = expanduser("~")
CONFIG_FILE_PATH = os.path.join(home_dir, '.diambra/config/deviceConfig.cfg')

# Create devices list
def create_devices_list():
    devices_list = {}

    idx = 0
    for gamepad in devices.gamepads:
        _, identifier, _ = gamepad._get_path_infomation()
        devices_list[idx] = {"type": "Gamepad",
                             "device": gamepad,
                             "id": identifier}
        idx += 1

    for keyboard in devices.keyboards:
        _, identifier, _ = keyboard._get_path_infomation()
        devices_list[idx] = {"type": "Keyboard",
                             "device": keyboard,
                             "id": identifier}
        idx += 1

    return devices_list

# Function to retrieve available devices and select one
def available_devices():
    devices_list = create_devices_list()
    print("Available devices:\n")
    for idx, device_dict in devices_list.items():
        print("{} - {} ({}) [{}]".format(idx, device_dict["device"].name, device_dict["type"], device_dict["id"]))

    return len(devices_list)

# Initialize input device
def get_diambra_controller(action_list, cfg=["But1", "But2", "But3", "But4", "But5", "But6", "But7", "But8"],
                         force_configure=False, skip_configure=False):

    devices_list = create_devices_list()
    devices_num = available_devices()

    if devices_num > 0:
        print("\nWarning: unplugging devices during execution can cause errors.")
        device_idx = int(input("Select device idx (you may need to repeat the input twice): "))
        try:
            device_dict = devices_list[device_idx]
            print("Initializing device # {}, named: {}".format(device_idx, device_dict["device"].name))
            if device_dict["type"] == "Keyboard":
                return DiambraKeyboard(device_dict["device"], action_list, cfg, force_configure, skip_configure)
            else:
                return DiambraGamepad(device_dict["device"], action_list, cfg, force_configure, skip_configure)
        except:
            raise Exception("Unable to initialize device, have you unplugged it during execution?")
    else:
        raise Exception("No devices found.")

# Class to manage device
class DiambraDevice(Thread):  # def class type thread
    def __init__(self, device, action_list=(("NoMove", "Left", "UpLeft", "Up", "UpRight", "Right", "DownRight", "Down", "DownLeft"),
                                            ("But0", "But1", "But2", "But3", "But4", "But5", "But6", "But7", "But8")),
                 cfg=["But1", "But2", "But3", "But4", "But5", "But6", "But7", "But8"],
                 force_configure=False, skip_configure=False, logging_level=logging.INFO):
        # thread init class (don't forget this)
        Thread.__init__(self, daemon=True)
        self.logger = logging.getLogger(__name__)
        self.logger.basicConfig(logging_level)

        self.stop_event = Event()

        self.start_code = ""
        self.select_code = ""
        self.start_but = 0
        self.select_but = 0
        self.event_hash_move = np.zeros(4)
        self.event_hash_attack = np.zeros(8)
        self.device_config_file_path = CONFIG_FILE_PATH

        self.all_actions_list = (("NoMove", "Left", "UpLeft", "Up", "UpRight",
                                  "Right", "DownRight", "Down", "DownLeft"),
                                 ("But0", "But1", "But2", "But3", "But4",
                                  "But5", "But6", "But7", "But8"))
        self.action_list = action_list

        self.cfg = cfg
        self.device = device
        _, self.device_id, _ = self.device._get_path_infomation()

        self.init_action_list(self.action_list)

        configure = False

        if not skip_configure:
            if force_configure:
                configure = True
            else:
                if not self.load_device_configuration():
                    configure = True

        if configure:
            # Run device configuration
            self.configure()

            configuration_ok = False
            while configuration_ok is False:

                ans = input("Want to test the configuration? (n/y): ")

                if ans == "y":
                    self.init_action_list(self.all_actions_list)
                    self.config_test()
                    self.init_action_list(self.action_list)

                    ans = input("Want to reconfigure the device? (y/n): ")
                    if ans == "y":
                        self.logger.info("Restarting device configuration")
                        # Run device configuration
                        self.configure()
                    else:
                        configuration_ok = True
                else:
                    configuration_ok = True

            self.save_device_configuration()

        self.logger.info("Diambra device initialized on device {} [{}]".format(self.device.name, self.device_id))

    # Show device events
    def show_device_events(self, event_codes_to_skip=[], event_code_to_show=None):
        self.logger.info("Use device to see events")
        while True:
            for event in self.device.read():
                if event.ev_type != "Sync" and event.ev_type != "Misc":
                    if event.code not in event_codes_to_skip:
                        if event_code_to_show is not None:
                            if event.code != event_code_to_show:
                                continue
                        self.logger.info("Event type: {}, event code: {}, event state: {}".format(event.ev_type, event.code, event.state))

    # Prepare device config dict to be saved
    def process_device_dict_for_save(self):
        raise NotImplementedError("This method needs to be implemented in a derived class")

    # Save device configuration
    def save_device_configuration(self):

        self.logger.info("Saving configuration in {}".format(self.device_config_file_path))

        # Convert device config dictionary
        cfg_dict_to_save = self.process_device_dict_for_save()

        # Load all devices configuration
        self.load_all_device_configurations()

        # Append all previous configurations but this one
        new_cfg_file_dict_list = []
        for cfg_file_dict in self.cfg_file_dict_list:
            if cfg_file_dict["device_id"] != self.device_id:
                new_cfg_file_dict_list.append(cfg_file_dict)
        cfg_file_dict_list = new_cfg_file_dict_list

        cfg_file_dict_list.append(cfg_dict_to_save)

        # Open file (new or overwrite previous one)
        cfg_file = open(self.device_config_file_path, "wb")
        pickle.dump(cfg_file_dict_list, cfg_file)
        cfg_file.close()

    # Load all devices configuration
    def load_all_device_configurations(self):
        if os.path.exists(self.device_config_file_path):
            with open(self.device_config_file_path, "rb") as cfg_file:
                cfg_file_dict_list = pickle.load(cfg_file)
        else:
            self.logger.info("No device configuration file found in: {}".format(os.path.dirname(self.device_config_file_path)))
            os.makedirs(os.path.dirname(self.device_config_file_path), exist_ok=True)
            cfg_file_dict_list = []

        self.cfg_file_dict_list = cfg_file_dict_list

    # Load device configuration
    def load_device_configuration(self):
        raise NotImplementedError("This method needs to be implemented in a derived class")

    # Configure device buttons
    def configure(self):
        raise NotImplementedError("This method needs to be implemented in a derived class")

    # Configuration Test
    def config_test(self):
        self.logger.info("Press Start to end configuration test")

        # Execute run function in thread mode
        thread = Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

        while True:
            actions = self.get_all_actions()

            if actions[0] != 0:
                self.logger.info("Move action = {}. (Press START to end configuration test).".format(self.all_actions_list[0][actions[0]]))
            if actions[1] != 0:
                self.logger.info("Attack action = {}. (Press START to end configuration test).".format(self.all_actions_list[1][actions[1]]))
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

    # Initialize action list
    def init_action_list(self, action_list):

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

    # Retrieve all device actions
    def get_all_actions(self):
        return [self.action_dict_move[tuple(self.event_hash_move)],
                self.action_dict_attack[tuple(self.event_hash_attack)],
                self.start_but, self.select_but]

    # Retrieve device actions
    def get_actions(self):
        return self.get_all_actions()[0:2]

    # Retrieve device events
    def run(self):      # run is a default Thread function
        raise NotImplementedError("This method needs to be implemented in a derived class")

    # Stop the thread
    def stop(self):
        self.stop_event.set()


# Class to manage keyboard
class DiambraKeyboard(DiambraDevice):
    def __init__(self, device, action_list=(("NoMove", "Left", "UpLeft", "Up", "UpRight", "Right", "DownRight", "Down", "DownLeft"),
                                    ("But0", "But1", "But2", "But3", "But4", "But5", "But6", "But7", "But8")),
                 cfg=["But1", "But2", "But3", "But4", "But5", "But6", "But7", "But8"],
                 force_configure=False, skip_configure=False):
        super().__init__(device, action_list, cfg, force_configure, skip_configure)

    # Prepare device config dict to be saved
    def process_device_dict_for_save(self):
        cfg_dict_to_save = {}
        cfg_dict_to_save["device_id"] = self.device_id

        # Start and select
        start_select_list = ["", ""]
        start_select_list[0] = self.start_code
        start_select_list[1] = self.select_code

        cfg_dict_to_save["start_select_list"] = start_select_list

        # Code2Group Map
        code_group_list = []
        for key, value in self.code_to_group_map.items():
            code_group_list.append([key, value])
        cfg_dict_to_save["code_group_list"] = code_group_list

        # Keys
        key_list_dict = []
        for key, value in self.device_dict["Key"].items():
            key_list_dict.append([key, value])

        cfg_dict_to_save["key_values_list"] = key_list_dict

        # Arrows
        arrow_list_dict = []
        for key, value in self.device_dict["Arrow"].items():
            arrow_list_dict.append([key, value])

        cfg_dict_to_save["arrow_values_list"] = arrow_list_dict

        return cfg_dict_to_save

    # Load device configuration
    def load_device_configuration(self):
        config_found = False

        # Read all devices configurations
        self.load_all_device_configurations()

        # Loop among all stored devices
        for cfg_file_dict in self.cfg_file_dict_list:
            if cfg_file_dict["device_id"] == self.device_id:

                try:
                    # Read Start/Select info
                    self.start_code = cfg_file_dict["start_select_list"][0]
                    self.select_code = cfg_file_dict["start_select_list"][1]

                    # Read Code2Group Map
                    self.code_to_group_map = defaultdict(lambda: "")
                    for item in cfg_file_dict["code_group_list"]:
                        self.code_to_group_map[item[0]] = item[1]

                    # Initialize device dict
                    self.device_dict = {}
                    self.device_dict["Key"] = defaultdict(lambda: 7)
                    self.device_dict["Arrow"] = defaultdict(lambda: 3)

                    # Read "Key" info
                    for item in cfg_file_dict["key_values_list"]:
                        self.device_dict["Key"][item[0]] = item[1]

                    # Read "Arrow" info
                    for item in cfg_file_dict["arrow_values_list"]:
                        self.device_dict["Arrow"][item[0]] = item[1]

                    config_found = True
                    self.logger.info("Device configuration file found in: {}".format(os.path.dirname(self.device_config_file_path)))
                    self.logger.info("Device configuration file loaded.")
                except:
                    self.logger.info("Invalid device configuration file found in: {}".format(os.path.dirname(self.device_config_file_path)))

        if not config_found:
            self.logger.info("Configuration for this device not present in device configuration file")

        return config_found

    # Configure device buttons
    def configure(self):

        self.logger.info("")
        self.logger.info("")
        self.logger.info("Configuring device {}".format(self.device))
        self.logger.info("")
        self.logger.info("# Buttons CFG file")
        self.logger.info("                _______            ")
        self.logger.info("       B7    __|digital|__   B8    ")
        self.logger.info("       B5      |buttons|     B6    ")
        self.logger.info("                 /    \            ")
        self.logger.info("             SELECT  START         ")
        self.logger.info("        UP                   B1    ")
        self.logger.info("        |                          ")
        self.logger.info(" LEFT--   --RIGHT        B4      B2")
        self.logger.info("        |                          ")
        self.logger.info("      DOWN                   B3    ")
        self.logger.info("  __/____                          ")
        self.logger.info(" |digital|                         ")
        self.logger.info(" | move  |                         ")
        self.logger.info("  -------                          ")
        self.logger.info("")
        self.logger.info("")

        self.code_to_group_map = defaultdict(lambda: "")
        self.device_dict = {}
        self.device_dict["Key"] = defaultdict(lambda: 7)
        self.device_dict["Arrow"] = defaultdict(lambda: 3)

        # Buttons configuration
        # Start and Select
        self.logger.info("Return/Enter key is not-allowed and would cause the program to stop.")
        self.logger.info("Press START button")
        but_not_set = True
        start_set = False
        while but_not_set:
            for event in self.device.read():
                if event.ev_type == "Key":
                    if event.state > 0:
                        if (event.code == "KEY_ENTER"):
                            raise Exception("Return/Enter not-allowed, aborting.")
                        self.start_code = event.code
                        start_set = True
                        self.logger.info("Start associated with {}".format(event.code))
                    else:
                        if start_set == True:
                            but_not_set = False
                            break

        self.logger.info("Press SELECT button (Start to skip)")
        but_not_set = True
        while but_not_set:
            for event in self.device.read():
                if event.ev_type == "Key":
                    if event.code != self.start_code and event.state > 0:
                        if (event.code == "KEY_ENTER"):
                            raise Exception("Return/Enter not-allowed, aborting.")
                        self.select_code = event.code
                        self.logger.info("Select associated with {}".format(event.code))
                    else:
                        but_not_set = False
                        if event.code == self.start_code:
                            self.logger.info("Select association skipped")
                        break

        # Attack buttons
        end_flag = False
        for idx in range(8):

            if end_flag:
                break

            self.logger.info("Press B{} button (SELECT / START to end configuration)".format(idx+1))

            but_not_set = True

            while but_not_set:

                if end_flag:
                    break

                for event in self.device.read():
                    if event.ev_type == "Key":
                        if (event.code != self.start_code and event.code != self.select_code):
                            if event.state > 0:
                                self.logger.info("Button B{}, event code = {}".format(idx+1, event.code))
                                self.device_dict["Key"][event.code] = idx
                                self.code_to_group_map[event.code] = "Key"
                            elif event.state == 0:
                                but_not_set = False
                        else:
                            if event.state == 0:
                                self.logger.info("Remaining buttons configuration skipped")
                                end_flag = True
                                break

        # Moves
        end_flag = False
        self.logger.info("Configuring moves")
        moves_list = ["UP", "RIGHT", "DOWN", "LEFT"]

        for idx, move in enumerate(moves_list):

            if end_flag:
                break

            self.logger.info("Press {} arrow (SELECT / START to skip)".format(move))

            but_not_set = True

            while but_not_set:

                if end_flag:
                    break

                for event in self.device.read():
                    if event.ev_type == "Key":
                        if (event.code != self.start_code and event.code != self.select_code):
                            if event.state > 0:
                                self.logger.info("Move {}, event code = {}".format(move, event.code))
                                self.device_dict["Arrow"][event.code] = idx
                                self.code_to_group_map[event.code] = "Arrow"
                            elif event.state == 0:
                                but_not_set = False
                        else:
                            if event.state == 0:
                                self.logger.info("Remaining buttons configuration skipped")
                                end_flag = True
                                break

        self.logger.info("Device dict : ")
        self.logger.info("Buttons (Keys) dict : ", self.device_dict["Key"])
        self.logger.info("Arrows (Keys) dict : ", self.device_dict["Arrow"])

        input("Configuration completed, press Enter to continue.")

        return

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

    # Retrieve device events
    def run(self):      # run is a default Thread function
        while not self.stop_event.is_set():   # loop until stop is called
            for event in self.device.read():   # check events of device, if not event, all is stop
                # Select
                if event.code == self.select_code:
                    self.select_but = min(event.state, 1)
                # Start
                elif event.code == self.start_code:
                    self.start_but = min(event.state, 1)
                else:
                    group = self.code_to_group_map[event.code]
                    if group == "Arrow":
                        self.event_hash_move[self.device_dict[group][event.code]] = min(event.state, 1)
                    elif group == "Key":
                        self.event_hash_attack[self.device_dict[group][event.code]] = min(event.state, 1)


# Class to manage gamepad
class DiambraGamepad(DiambraDevice):
    def __init__(self, device, action_list=(("NoMove", "Left", "UpLeft", "Up", "UpRight", "Right", "DownRight", "Down", "DownLeft"),
                                    ("But0", "But1", "But2", "But3", "But4", "But5", "But6", "But7", "But8")),
                 cfg=["But1", "But2", "But3", "But4", "But5", "But6", "But7", "But8"],
                 force_configure=False, skip_configure=False):
        super().__init__(device, action_list, cfg, force_configure, skip_configure)

    # Prepare device config dict to be saved
    def process_device_dict_for_save(self):
        cfg_dict_to_save = {}
        cfg_dict_to_save["device_id"] = self.device_id

        # Start and select
        start_select_list = ["", ""]
        start_select_list[0] = self.start_code
        start_select_list[1] = self.select_code

        cfg_dict_to_save["start_select_list"] = start_select_list

        # Keys
        key_list_dict = []
        for key, value in self.device_dict["Key"].items():
            key_list_dict.append([key, value])

        cfg_dict_to_save["key_values_list"] = key_list_dict

        # Digital and Analog moves
        abs_list_dict_digital = []
        abs_list_dict_analog = []
        for key1, value1 in self.device_dict["Absolute"].items():

            if "ABS_HAT0" in key1:
                # Digital moves
                for key2, value2 in self.device_dict["Absolute"][key1].items():
                    abs_list_dict_digital.append([key1, key2, value2[0]])

            else:
                # Analog moves
                abs_list_dict_analog.append(
                    [key1, value1[0], value1[1], value1[2], value1[3]])

        cfg_dict_to_save["absolute_values_list_digital"] = abs_list_dict_digital
        cfg_dict_to_save["absolute_values_list_analog"] = abs_list_dict_analog

        return cfg_dict_to_save

    # Load device configuration
    def load_device_configuration(self):
        config_found = False

        # Read all devices configurations
        self.load_all_device_configurations()

        # Loop among all stored devices
        for cfg_file_dict in self.cfg_file_dict_list:
            if cfg_file_dict["device_id"] == self.device_id:

                try:
                    # Read Start/Select info
                    self.start_code = cfg_file_dict["start_select_list"][0]
                    self.select_code = cfg_file_dict["start_select_list"][1]

                    # Initialize device dict
                    self.device_dict = {}
                    self.device_dict["Key"] = defaultdict(lambda: 7)
                    self.device_dict["Absolute"] = defaultdict(lambda: defaultdict(lambda: [[], 0]))
                    self.device_dict["Absolute"]["ABS_HAT0Y"] = defaultdict(lambda: [[], 0])  # No-op action = 0
                    self.device_dict["Absolute"]["ABS_HAT0X"] = defaultdict(lambda: [[], 0])  # No-op action = 0
                    self.device_dict["Absolute"]["ABS_HAT0Y"][0] = [[0, 2], 0]
                    self.device_dict["Absolute"]["ABS_HAT0X"][0] = [[1, 3], 0]

                    # Read "Key" info
                    for item in cfg_file_dict["key_values_list"]:
                        self.device_dict["Key"][item[0]] = item[1]

                    # Read "Absolute" info DIGITAL
                    for item in cfg_file_dict["absolute_values_list_digital"]:
                        self.device_dict["Absolute"][item[0]][item[1]] = [item[2],
                                                                           abs(item[1])]

                    # Read "Absolute" info ANALOG
                    for item in cfg_file_dict["absolute_values_list_analog"]:
                        self.device_dict["Absolute"][item[0]] = [
                            item[1], item[2], item[3], item[4]]

                    config_found = True
                    self.logger.info("Device configuration file found in: {}".format(os.path.dirname(self.device_config_file_path)))
                    self.logger.info("Device configuration file loaded.")
                except:
                    self.logger.info("Invalid device configuration file found in: {}".format(os.path.dirname(self.device_config_file_path)))

        if not config_found:
            self.logger.info("Configuration for this device not present in device configuration file")

        return config_found

    # Configure device buttons
    def configure(self):
        self.logger.info("")
        self.logger.info("")
        self.logger.info("Configuring device {}".format(self.device))
        self.logger.info("")
        self.logger.info("# Buttons CFG file")
        self.logger.info("               _______            ")
        self.logger.info("      B7    __|digital|__   B8    ")
        self.logger.info("      B5      |buttons|     B6    ")
        self.logger.info("                /    \            ")
        self.logger.info("                            B1    ")
        self.logger.info("      |     SELECT  START         ")
        self.logger.info("   --   --              B4      B2")
        self.logger.info("      |      -                    ")
        self.logger.info(" __/____   ( + )            B3    ")
        self.logger.info("|digital|    -                    ")
        self.logger.info("| move  |      \______            ")
        self.logger.info(" -------       |analog|           ")
        self.logger.info("               | move |           ")
        self.logger.info("                ------            ")
        self.logger.info("")
        self.logger.info("NB: Be sure to have your analog switch on before starting.")
        self.logger.info("")

        self.device_dict = {}
        self.device_dict["Key"] = defaultdict(lambda: 7)
        self.device_dict["Absolute"] = defaultdict(lambda: defaultdict(lambda: [[], 0]))

        # Buttons configuration
        # Start and Select
        self.logger.info("Press START button")
        but_not_set = True
        while but_not_set:
            for event in self.device.read():
                if event.ev_type == "Key":
                    if event.state == 1:
                        self.start_code = event.code
                        self.logger.info("Start associated with {}".format(event.code))
                    else:
                        but_not_set = False
                        break

        self.logger.info("Press SELECT button (Start to skip)")
        but_not_set = True
        while but_not_set:
            for event in self.device.read():
                if event.ev_type == "Key":
                    if event.code != self.start_code and event.state == 1:
                        self.select_code = event.code
                        self.logger.info("Select associated with {}".format(event.code))
                    else:
                        but_not_set = False
                        if event.code == self.start_code:
                            self.logger.info("Select association skipped")
                        break

        # Attack buttons
        end_flag = False
        for idx in range(8):

            if end_flag:
                break

            self.logger.info("Press B{} button (SELECT / START to end configuration)".format(idx+1))

            but_not_set = True

            while but_not_set:

                if end_flag:
                    break

                for event in self.device.read():
                    if event.ev_type == "Key":
                        if (event.code != self.start_code and event.code != self.select_code):
                            if event.state == 1:
                                self.logger.info("Button B{}, event code = {}".format(idx+1, event.code))
                                self.device_dict["Key"][event.code] = idx
                            elif event.state == 0:
                                but_not_set = False
                        else:
                            if event.state == 0:
                                self.logger.info("Remaining buttons configuration skipped")
                                end_flag = True
                                break

        # Move sticks
        # Digital
        end_flag = False
        self.logger.info("Configuring digital move")
        moves_list = ["UP", "RIGHT", "DOWN", "LEFT"]
        event_codes_list = ["Y", "X", "Y", "X"]
        self.device_dict["Absolute"]["ABS_HAT0Y"] = defaultdict(lambda: [
                                                                [], 0])
        self.device_dict["Absolute"]["ABS_HAT0X"] = defaultdict(lambda: [
                                                                [], 0])
        self.device_dict["Absolute"]["ABS_HAT0Y"][0] = [[0, 2], 0]
        self.device_dict["Absolute"]["ABS_HAT0X"][0] = [[1, 3], 0]

        for idx, move in enumerate(moves_list):

            if end_flag:
                break

            self.logger.info("Press {} arrow (SELECT / START to skip)".format(move))

            but_not_set = True

            while but_not_set:

                if end_flag:
                    break

                for event in self.device.read():

                    if event.ev_type == "Absolute":
                        if event.code == "ABS_HAT0" + event_codes_list[idx]:
                            if abs(event.state) == 1:
                                self.logger.info("{} move event code = {}, event state = {}".format(
                                    move, event.code, event.state))
                                self.device_dict["Absolute"][event.code][event.state] = [
                                    idx, abs(event.state)]
                            elif event.state == 0:
                                but_not_set = False
                            else:
                                self.logger.info("Digital Move Stick assumes not admissible values: {}".format(
                                    event.state))
                                self.logger.info(
                                    "Digital Move Stick not supported, configuration skipped")
                                end_flag = True
                                break
                    else:
                        if (event.code == self.start_code
                                or event.code == self.select_code):
                            if event.state == 0:
                                self.logger.info("Digital Move Stick configuration skipped")
                                end_flag = True
                                break

        # Move sticks
        # Analog
        self.logger.info("Configuring analog move")
        moves_list = ["UP", "RIGHT", "DOWN", "LEFT"]
        event_codes_list = ["Y", "X", "Y", "X"]
        self.max_analog_val = {}
        self.origin_analog_val = {}

        for idx, move in enumerate(moves_list):

            self.logger.info("Move left analog in {} position, keep it there and press Start".format(move))

            but_not_set = True

            self.max_analog_val[move] = 0

            while but_not_set:

                for event in self.device.read():

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

        self.logger.info("Delta perc = ", self.delta_perc)

        # Addressing Y-X axis
        for idx in range(2):
            self.logger.info("{} move event code = ABS_{}, ".format(moves_list[idx],
                                                         event_codes_list[idx]) +
                  "event state = {}".format(self.max_analog_val[moves_list[idx]]))
            self.logger.info("{} move event code = ABS_{}, ".format(moves_list[idx+2],
                                                         event_codes_list[idx+2]) +
                  " event state = {}".format(self.max_analog_val[moves_list[idx+2]]))
            self.logger.info("NO {}-{} move event code =".format(moves_list[idx],
                                                      moves_list[idx+2]) +
                  " ABS_{}, ".format(event_codes_list[idx]) +
                  "event state = {}".format(self.origin_analog_val[moves_list[idx]]))

            event_code = "ABS_{}".format(event_codes_list[idx])
            if self.delta_perc[idx] > 0:
                self.device_dict["Absolute"][event_code] = [
                    [self.origin_analog_val[moves_list[idx]] - self.delta_perc[idx],
                        self.origin_analog_val[moves_list[idx]] + self.delta_perc[idx]],
                    [[idx+2], 1], [[idx, idx+2], 0], [[idx], 1]]

            elif self.delta_perc[idx] < 0:
                self.device_dict["Absolute"][event_code] = [
                    [self.origin_analog_val[moves_list[idx]] - self.delta_perc[idx+2],
                        self.origin_analog_val[moves_list[idx]] + self.delta_perc[idx+2]],
                    [[idx], 1], [[idx, idx+2], 0], [[idx+2], 1]]

            else:
                self.logger.info("Not admissible values found in analog stick configuration, skipping")

        self.logger.info("device dict : ")
        self.logger.info("Buttons (Keys) dict : ", self.device_dict["Key"])
        self.logger.info("Moves (Absolute) dict : ", self.device_dict["Absolute"])

        self.logger.info("Configuration completed.")

        return

    # Retrieve device events
    def run(self):      # run is a default Thread function
        while not self.stop_event.is_set():   # loop until stop is called
            for event in self.device.read():   # check events of devices, if not event, all is stop
                if event.ev_type == "Key":   # category of binary respond values

                    # Select
                    if event.code == self.select_code:
                        self.select_but = event.state
                    # Start
                    elif event.code == self.start_code:
                        self.start_but = event.state
                    else:
                        self.event_hash_attack[self.device_dict[event.ev_type][event.code]] = event.state

                # category of move values (digital moves)
                elif "ABS_HAT0" in event.code:

                    idx = self.device_dict[event.ev_type][event.code][event.state][0]
                    event_state = self.device_dict[event.ev_type][event.code][event.state][1]
                    self.event_hash_move[idx] = event_state

                # category of move values (analog left stick)
                elif event.code == "ABS_X" or event.code == "ABS_Y":

                    thresh_values = self.device_dict[event.ev_type][event.code][0]
                    min_act = self.device_dict[event.ev_type][event.code][1]
                    centr_act = self.device_dict[event.ev_type][event.code][2]
                    max_act = self.device_dict[event.ev_type][event.code][3]

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


if __name__ == "__main__":
    print("\nWhat do you want to do:")
    print("  1 - Show device events")
    print("  2 - Configure device")
    print("  3 - Normal Initialization with forced configuration")
    print("  4 - Normal Initialization with configuration testing")
    choice = input("\nYour choice: ")
    print("\n")

    action_list = (("NoMove", "Left", "UpLeft", "Up", "UpRight", "Right", "DownRight", "Down", "DownLeft"),
                   ("But0", "But1", "But2", "But3", "But4", "But5", "But6", "But7", "But8"))

    if choice == "1":
            DiambraController = get_diambra_controller(action_list, skip_configure=True)
            DiambraController.show_device_events()
    elif choice == "2":
            DiambraController = get_diambra_controller(action_list, skip_configure=True)
            DiambraController.configure()
    elif choice == "3":
            DiambraController = get_diambra_controller(action_list, force_configure=True)
    elif choice == "4":
        DiambraController = get_diambra_controller(action_list)
        DiambraController.config_test()