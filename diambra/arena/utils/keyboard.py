import os
import numpy as np
from threading import Thread, Event
from collections import defaultdict
from inputs import devices
import pickle
from os.path import expanduser
home_dir = expanduser("~")

# Function to retrieve available GamePads and select one
def available_keyboards():

    print("Available keyboards:\n")

    for idx, keyboard in enumerate(devices.keyboards):
        print("Keyboard {}: {}".format(idx, keyboard))

    return len(devices.keyboards)


# Class to manage keyboard
class DiambraKeyboard(Thread):  # def class type thread
    def __init__(self, action_list=(("NoMove", "Left", "UpLeft", "Up",
                                     "UpRight", "Right", "DownRight",
                                     "Down", "DownLeft"),
                                    ("But0", "But1", "But2", "But3",
                                     "But4", "But5", "But6", "But7",
                                     "But8")),
                 cfg=["But1", "But2", "But3", "But4", "But5", "But6", "But7", "But8"],
                 keyboard_num=0, force=False, skip_configure=False):
        # thread init class (don't forget this)
        Thread.__init__(self, daemon=True)

        self.stop_event = Event()

        self.start_code = ""
        self.select_code = ""
        self.start_but = 0
        self.select_but = 0
        self.event_hash_move = np.zeros(4)
        self.event_hash_attack = np.zeros(8)
        self.keyboard_config_file_name = os.path.join(home_dir, '.diambra/config/keyboardConfig.cfg')

        self.all_actions_list = (("NoMove", "Left", "UpLeft", "Up", "UpRight",
                                  "Right", "DownRight", "Down", "DownLeft"),
                                 ("But0", "But1", "But2", "But3", "But4",
                                  "But5", "But6", "But7", "But8"))
        self.action_list = action_list

        self.cfg = cfg
        self.keyboard_num = keyboard_num

        self.init_action_list(self.action_list)

        try:
            self.keyboard = devices.keyboards[self.keyboard_num]
        except IndexError:
            raise Exception("No keyboard found.")

        print("Initializing keyboard # {}, named: {}".format(self.keyboard_num, self.keyboard))

        configure = False

        if not skip_configure:
            if force:
                configure = True
            else:
                if not self.load_keyboard_configuration():
                    configure = True

        if configure:
            # Run keyboard configuration
            self.configure()

            configuration_ok = False
            while configuration_ok is False:

                ans = input("Want to test the configuration? (n/y): ")
                ans = input("Want to test the configuration? (n/y): ")
                ans = input("Want to test the configuration? (n/y): ")

                if ans == "y":
                    self.init_action_list(self.all_actions_list)
                    self.config_test()
                    self.init_action_list(self.action_list)

                    ans = input("Want to reconfigure the GamePad? (y/n): ")
                    if ans == "y":
                        print("Restarting keyboard configuration")
                        # Run keyboard configuration
                        self.configure()
                    else:
                        configuration_ok = True
                else:
                    configuration_ok = True

            self.save_keyboard_configuration()

        print("Diambra Keyboard initialized on device # {}, named: {}".format(self.keyboard_num, self.keyboard))

    # Show keyboard events
    def show_keyboard_events(self, event_codes_to_skip=[], event_code_to_show=None):

        print("Use keyboard to see events")
        while True:
            for event in self.keyboard.read():
                if event.ev_type != "Sync" and event.ev_type != "Misc":
                    if event.code not in event_codes_to_skip:
                        if event_code_to_show is not None:
                            if event.code != event_code_to_show:
                                continue
                        print("Event type: {}, event code: {}, event state: {}".format(event.ev_type, event.code, event.state))

    # Prepare keyboard config dict to be saved
    def process_keyboard_dict_for_save(self):

        cfg_dict_to_save = {}
        cfg_dict_to_save["name"] = self.keyboard.name

        # Keys
        key_list_dict = []
        for key, value in self.keyboard_dict["Key"].items():
            key_list_dict.append([key, value])

        cfg_dict_to_save["key_values_list"] = key_list_dict

        return cfg_dict_to_save

    # Save keyboard configuration
    def save_keyboard_configuration(self):

        print("Saving configuration in {}".format(self.keyboard_config_file_name))

        # Convert keyboard config dictionary
        cfg_dict_to_save = self.process_keyboard_dict_for_save()

        # Load all keyboards configuration
        self.load_all_keyboard_configurations()

        # Append all previous configurations but this one
        new_cfg_file_dict_list = []
        for cfg_file_dict in self.cfg_file_dict_list:
            if cfg_file_dict["name"] != self.keyboard.name:
                new_cfg_file_dict_list.append(cfg_file_dict)
        cfg_file_dict_list = new_cfg_file_dict_list

        cfg_file_dict_list.append(cfg_dict_to_save)

        # Open file (new or overwrite previous one)
        cfg_file = open(self.keyboard_config_file_name, "wb")
        pickle.dump(cfg_file_dict_list, cfg_file)
        cfg_file.close()

    # Load all keyboards configuration
    def load_all_keyboard_configurations(self):

        try:
            cfg_file = open(self.keyboard_config_file_name, "rb")

            # Load Pickle Dict
            cfg_file_dict_list = pickle.load(cfg_file)

            cfg_file.close()

        except OSError:
            print("No keyboard configuration file found in: {}".format(os.path.join(home_dir, '.diambra/config/')))
            config_file_folder = os.path.join(home_dir, '.diambra/')
            os.makedirs(config_file_folder, exist_ok=True)
            config_file_folder = os.path.join(home_dir, '.diambra/config/')
            os.makedirs(config_file_folder, exist_ok=True)
            cfg_file_dict_list = []

        self.cfg_file_dict_list = cfg_file_dict_list

    # Load keyboard configuration
    def load_keyboard_configuration(self):

        config_found = False

        # Read all keyboards configurations
        self.load_all_keyboard_configurations()

        # Loop among all stored GamePads
        for cfg_file_dict in self.cfg_file_dict_list:
            if cfg_file_dict["name"] == self.keyboard.name:

                try:
                    # Initialize keyboard dict
                    self.keyboard_dict = {}
                    self.keyboard_dict["Key"] = defaultdict(lambda: 7)

                    # Read "Key" info
                    for item in cfg_file_dict["key_values_list"]:
                        self.keyboard_dict["Key"][item[0]] = item[1]

                    config_found = True
                    print("Keyboard configuration file found in: {}".format(os.path.join(home_dir, '.diambra/config/')))
                    print("Keyboard configuration file loaded.")
                except:
                    print("Invalid keyboard configuration file found in: {}".format(os.path.join(home_dir, '.diambra/config/')))

        if not config_found:
            print("Configuration for this keyboard not present in keyboard configuration file")

        return config_found

    # Configure keyboard buttons
    def configure(self):

        print("")
        print("")
        print("Configuring keyboard {}".format(self.keyboard))
        print("")
        print("# Buttons CFG file")
        print("                _______            ")
        print("       B7    __|digital|__   B8    ")
        print("       B5      |buttons|     B6    ")
        print("                 /    \            ")
        print("             SELECT  START         ")
        print("        UP                   B1    ")
        print("        |                          ")
        print(" LEFT--   --RIGHT        B4      B2")
        print("        |                          ")
        print("      DOWN                   B3    ")
        print("  __/____                          ")
        print(" |digital|                         ")
        print(" | move  |                         ")
        print("  -------                          ")
        print("")
        print("")

        self.keyboard_dict = {}
        self.keyboard_dict["Key"] = defaultdict(lambda: 7)

        # Buttons configuration
        # Start and Select
        print("Press START button")
        but_not_set = True
        start_set = False
        while but_not_set:
            for event in self.keyboard.read():
                if event.ev_type == "Key":
                    if event.state == 1:
                        self.start_code = event.code
                        start_set = True
                        print("Start associated with {}".format(event.code))
                    else:
                        if start_set == True:
                            but_not_set = False
                            break

        print("Press SELECT button (Start to skip)")
        but_not_set = True
        while but_not_set:
            for event in self.keyboard.read():
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

                for event in self.keyboard.read():
                    if event.ev_type == "Key":
                        if (event.code != self.start_code and event.code != self.select_code):
                            if event.state > 0:
                                print("Button B{}, event code = {}".format(idx+1, event.code))
                                self.keyboard_dict["Key"][event.code] = idx
                            elif event.state == 0:
                                but_not_set = False
                        else:
                            if event.state == 0:
                                print("Remaining buttons configuration skipped")
                                end_flag = True
                                break

        # Moves
        end_flag = False
        print("Configuring moves")
        moves_list = ["UP", "RIGHT", "DOWN", "LEFT"]

        for idx, move in enumerate(moves_list):

            if end_flag:
                break

            print("Press {} arrow (Start / Select to skip)".format(move))

            but_not_set = True

            while but_not_set:

                if end_flag:
                    break

                for event in self.keyboard.read():
                    if event.ev_type == "Key":
                        if (event.code != self.start_code and event.code != self.select_code):
                            if event.state > 0:
                                print("Move {}, event code = {}".format(move, event.code))
                                self.keyboard_dict["Key"][event.code] = idx
                            elif event.state == 0:
                                but_not_set = False
                        else:
                            if event.state == 0:
                                print("Remaining buttons configuration skipped")
                                end_flag = True
                                break

        print("Keyboard dict : ")
        print("Buttons (Keys) dict : ", self.keyboard_dict["Key"])

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
                print("Move action = {}. (Press START to end configuration test).".format(self.all_actions_list[0][actions[0]]))
            if actions[1] != 0:
                print("Attack action = {}. (Press START to end configuration test).".format(self.all_actions_list[1][actions[1]]))
            #if actions[2] != 0:
            #    ans = input("Want to end configuration? (N/y)")
            #    if ans == "y":
            #        break

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

    # Retrieve all keyboard actions
    def get_all_actions(self):
        return [self.action_dict_move[tuple(self.event_hash_move)],
                self.action_dict_attack[tuple(self.event_hash_attack)],
                self.start_but, self.select_but]

    # Retrieve keyboard actions
    def get_actions(self):
        return self.get_all_actions()[0:2]

    # Retrieve keyboard events
    def run(self):      # run is a default Thread function
        while not self.stop_event.is_set():   # loop until stop is called
            for event in self.keyboard.read():   # check events of gamepads, if not event, all is stop
                if event.ev_type == "Key":   # category of binary respond values

                    # Select
                    if event.code == self.select_code:
                        self.select_but = min(event.state, 1)
                    # Start
                    elif event.code == self.start_code:
                        self.start_but = min(event.state, 1)
                    else:
                        self.event_hash_attack[self.keyboard_dict[event.ev_type][event.code]] = min(event.state, 1)

    # Stop the thread
    def stop(self):
        self.stop_event.set()

if __name__ == "__main__":

    print("\nWhat do you want to do:")
    print("  1 - Show keyboard events")
    print("  2 - Configure keyboard")
    print("  3 - Normal Initialization")
    choice = input("\nYour choice: ")
    print("\n")

    if choice == "1":
        num_keyboards = available_keyboards()

        print("\n")
        if num_keyboards > 0:
            keyboard_num = int(input("Keyboard idx: "))
            keyboard = DiambraKeyboard(keyboard_num=keyboard_num, skip_configure=True)
            keyboard.show_keyboard_events()
    elif choice == "2":
        num_keyboards = available_keyboards()

        print("\n")
        if num_keyboards > 0:
            keyboard_num = int(input("Keyboard idx: "))
            keyboard = DiambraKeyboard(keyboard_num=keyboard_num, skip_configure=True)
            keyboard.configure()
    elif choice == "3":
        num_keyboards = available_keyboards()

        print("\n")
        if num_keyboards > 0:
            keyboard_num = int(input("Keyboard idx: "))
            keyboard = DiambraKeyboard(keyboard_num=keyboard_num, force=True)