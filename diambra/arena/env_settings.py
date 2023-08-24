from dataclasses import dataclass
from typing import Union, List, Tuple, Any, Dict
from diambra.arena.utils.gym_utils import available_games
import numpy as np
import random
from diambra.engine import model
import time

MAX_VAL = float("inf")
MIN_VAL = float("-inf")
MAX_FRAME_RES = 512
MAX_STACK_VALUE = 48

def check_num_in_range(key, value, bounds):
    error_message = "ERROR: \"{}\" ({}) value must be in the range {}".format(key, value, bounds)
    assert (value >= bounds[0] and value <= bounds[1]), error_message
    assert (type(value)==type(bounds[0])), error_message

def check_val_in_list(key, value, valid_list):
    error_message = "ERROR: \"{}\" ({}) admissible values are {}".format(key, value, valid_list)
    assert (value in valid_list), error_message
    assert (type(value)==type(valid_list[valid_list.index(value)])), error_message

@dataclass
class EnvironmentSettings:
    env_info = None
    games_dict = None

    # Fixed at startup
    game_id: str
    frame_shape: Tuple[int, int, int] = (0, 0, 0)
    step_ratio: int = 6
    n_players: int = 1
    disable_keyboard: bool = True
    disable_joystick: bool = True
    render_mode: Union[str, None] = None
    rank: int = 0
    env_address: str = "localhost:50051"
    grpc_timeout: int = 600

    # Variable at reset
    seed: Union[int, None] = None
    difficulty: Union[int, str] = "Random"
    continue_game: float = 0.0
    show_final: bool = False
    tower: int = 3  # UMK3 Specific

    # Bookeeping variables
    _last_seed: int = None
    pb_model: model = None

    variable_env_settings = ["seed", "difficulty", "continue_game", "show_final", "tower", "role",
                             "characters", "outfits", "super_art", "fighting_style", "ultimate_style"]

    # Transforming env settings dict to pb request
    def get_pb_request(self, init=False):
        frame_shape = {
            "h": self.frame_shape[0],
            "w": self.frame_shape[1],
            "c": self.frame_shape[2]
        }

        if self.seed == None:
            self.seed = int(time.time())

        if self._last_seed != self.seed:
            random.seed(self.seed)
            np.random.seed(self.seed)
            self._last_seed = self.seed

        action_spaces = self._get_action_spaces()

        if init is False:
            self._process_random_values()

            player_env_settings = self._get_player_specific_values()

            variable_env_settings = model.EnvSettings.VariableEnvSettings(
                random_seed=self.seed,
                difficulty=self.difficulty,
                continue_game=self.continue_game,
                show_final=self.show_final,
                tower=self.tower,
                player_env_settings=player_env_settings,
            )
        else:
            variable_env_settings = model.EnvSettings.VariableEnvSettings()

        request = model.EnvSettings(
            game_id=self.game_id,
            frame_shape=frame_shape,
            step_ratio=self.step_ratio,
            n_players=self.n_players,
            disable_keyboard=self.disable_keyboard,
            disable_joystick=self.disable_joystick,
            rank=self.rank,
            action_spaces=action_spaces,
            variable_env_settings=variable_env_settings,
        )

        self.pb_model = request

        return request

    def finalize_init(self, env_info):
        self.env_info = env_info
        self.games_dict = available_games(False)

        # Create list of valid characters
        self.valid_characters = [character for character in self.env_info.characters_info.char_list \
                                           if character not in self.env_info.characters_info.char_forbidden_list]

    def update_variable_env_settings(self, options: Dict[str, Any] = None):
        for k, v in options.items():
            if k in self.variable_env_settings:
                setattr(self, k, v)

        self._sanity_check()

        # Storing original attributes before sampling random ones
        original_settings_values =  {}
        for k in self.variable_env_settings:
            original_settings_values[k] = getattr(self, k)

        request = self.get_pb_request()

        # Restoring original attributes after random sampling
        for k, v in original_settings_values.items():
            setattr(self, k, v)

        return request

    def _sample_characters(self, n_characters=3):
        random.shuffle(self.valid_characters)
        sampled_characters = []
        for _ in range(n_characters):
            for character in self.valid_characters:
                valid = True
                for sampled_character in sampled_characters:
                    if sampled_character == character:
                        valid = False
                    elif character in self.env_info.characters_info.char_homonymy_map.keys() and \
                       sampled_character in self.env_info.characters_info.char_homonymy_map.keys():
                        if self.env_info.characters_info.char_homonymy_map[character] == sampled_character:
                            valid = False
                if valid is True:
                    sampled_characters.append(character)
                    break

        return sampled_characters

    def _sanity_check(self):
        if self.env_info is None or self.games_dict is None:
            raise("EnvironmentSettings class not correctly initialized")

        # TODO: consider using typing.Literal to specify lists of admissible values: NOTE: It requires Python 3.8+
        check_val_in_list("game_id", self.game_id, list(self.games_dict.keys()))
        if self.render_mode is not None:
            check_val_in_list("render_mode", self.render_mode, ["human", "rgb_array"])
        check_num_in_range("frame_shape[0]", self.frame_shape[0], [0, MAX_FRAME_RES])
        check_num_in_range("frame_shape[1]", self.frame_shape[1], [0, MAX_FRAME_RES])
        if (min(self.frame_shape[0], self.frame_shape[1]) == 0 and
            max(self.frame_shape[0], self.frame_shape[1]) != 0):
            raise Exception("\"frame_shape[0] and frame_shape[1]\" must be either both different from or equal to 0")
        check_val_in_list("frame_shape[2]", self.frame_shape[2], [0, 1])
        check_num_in_range("step_ratio", self.step_ratio, [1, 6])
        check_num_in_range("grpc_timeout", self.grpc_timeout, [0, 3600])
        check_num_in_range("rank", self.rank, [0, MAX_VAL])

        if self.seed is not None:
            check_num_in_range("seed", self.seed, [-1, MAX_VAL])
        difficulty_admissible_values = list(range(self.env_info.difficulty_bounds.min, self.env_info.difficulty_bounds.max + 1))
        difficulty_admissible_values.append("Random")
        check_val_in_list("difficulty", self.difficulty, difficulty_admissible_values)
        check_num_in_range("continue_game", self.continue_game, [MIN_VAL, 1.0])
        check_val_in_list("tower", self.tower, ["Random", 1, 2, 3, 4])

    def _process_random_values(self):
        if self.difficulty == "Random":
            self.difficulty = random.choice(list(range(self.env_info.difficulty_bounds.min, self.env_info.difficulty_bounds.max + 1)))
        if self.tower == "Random":
            self.tower = random.choice(list(range(1, 5)))

@dataclass
class EnvironmentSettings1P(EnvironmentSettings):
    # Player level
    role: str = "Random"
    characters: Union[str, Tuple[str], Tuple[str, str], Tuple[str, str, str]] = ("Random", "Random", "Random")
    outfits: int = 1
    action_space: str = "multi_discrete"
    super_art: Union[int, str] = "Random"  # SFIII Specific
    fighting_style: Union[int, str] = "Random" # KOF Specific
    ultimate_style: Union[Tuple[str, str, str], Tuple[int, int, int]] = ("Random", "Random", "Random") # KOF Specific

    def _sanity_check(self):
        super()._sanity_check()

        if isinstance(self.characters, str):
            self.characters = (self.characters, "Random", "Random")
        else:
            for _ in range(len(self.characters), 3):
                self.characters += ("Random", )

        check_num_in_range("n_players", self.n_players, [1, 1])
        check_val_in_list("action_space", self.action_space, ["discrete", "multi_discrete"])
        check_val_in_list("role", self.role, ["P1", "P2", "Random"])
        # Check for characters
        char_list = list(self.env_info.characters_info.char_list)
        char_list.append("Random")
        for idx in range(3):
            check_val_in_list("characters[{}]".format(idx), self.characters[idx], char_list)
        check_num_in_range("outfits", self.outfits, self.games_dict[self.game_id]["outfits"])
        check_val_in_list("super_art", self.super_art, ["Random", 1, 2, 3])
        check_val_in_list("fighting_style", self.fighting_style, ["Random", 1, 2, 3])
        for idx in range(3):
            check_val_in_list("ultimate_style[{}]".format(idx), self.ultimate_style[idx], ["Random", 1, 2])

    def _get_action_spaces(self):
        action_space = model.EnvSettings.ActionSpace.ACTION_SPACE_DISCRETE if self.action_space == "discrete" else \
                       model.EnvSettings.ActionSpace.ACTION_SPACE_MULTI_DISCRETE

        return [action_space]

    def _process_random_values(self):
        super()._process_random_values()

        sampled_characters = self._sample_characters()
        characters_tmp = []
        for idx in range(3):
            if self.characters[idx] == "Random":
                characters_tmp.append(sampled_characters[idx])
            else:
                characters_tmp.append(self.characters[idx])
        self.characters = tuple(characters_tmp)

        if self.role == "Random":
            self.role = random.choice(["P1", "P2"])
        if self.super_art == "Random":
            self.super_art = random.choice(list(range(1, 4)))
        if self.fighting_style == "Random":
            self.fighting_style = random.choice(list(range(1, 4)))
        self.ultimate_style = tuple([random.choice(list(range(1, 3))) if self.ultimate_style[idx] == "Random" else self.ultimate_style[idx] for idx in range(3)])

    def _get_player_specific_values(self):
        player_env_settings = model.EnvSettings.VariableEnvSettings.PlayerEnvSettings(
            role=self.role,
            characters=[self.characters[0], self.characters[1], self.characters[2]],
            outfits=self.outfits,
            super_art=self.super_art,
            fighting_style=self.fighting_style,
            ultimate_style={"dash": self.ultimate_style[0], "evade": self.ultimate_style[1], "bar": self.ultimate_style[2]}
        )

        return [player_env_settings]

@dataclass
class EnvironmentSettings2P(EnvironmentSettings):
    # Player level
    role: Tuple[str, str] = ("Random", "Random")
    characters: Union[Tuple[str, str], Tuple[Tuple[str], Tuple[str]],
                      Tuple[Tuple[str, str], Tuple[str, str]],
                      Tuple[Tuple[str, str, str], Tuple[str, str, str]]] =\
                    (("Random", "Random", "Random"), ("Random", "Random", "Random"))
    outfits: Tuple[int, int] = (1, 1)
    action_space: Tuple[str, str] = ("multi_discrete", "multi_discrete")
    super_art: Union[Tuple[str, str], Tuple[int, int], Tuple[str, int], Tuple[int, str]] = ("Random", "Random")  # SFIII Specific
    fighting_style: Union[Tuple[str, str], Tuple[int, int], Tuple[str, int], Tuple[int, str]] = ("Random", "Random")  # KOF Specific
    ultimate_style: Union[Tuple[Tuple[str, str, str], Tuple[str, str, str]], Tuple[Tuple[int, int, int], Tuple[int, int, int]]] =\
                        (("Random", "Random", "Random"), ("Random", "Random", "Random"))  # KOF Specific

    def _sanity_check(self):
        super()._sanity_check()

        if isinstance(self.characters[0], str):
            self.characters = ((self.characters[0], "Random", "Random"),
                            (self.characters[1], "Random", "Random"))
        else:
            tmp_chars = [self.characters[0], self.characters[1]]
            for _ in range(len(self.characters[0]), 3):
                for jdx in range(2):
                    tmp_chars[jdx] += ("Random", )
            self.characters = tuple(tmp_chars)

        check_num_in_range("n_players", self.n_players, [2, 2])
        char_list = list(self.env_info.characters_info.char_list)
        char_list.append("Random")
        for idx in range(2):
            check_val_in_list("action_space[{}]".format(idx), self.action_space[idx], ["discrete", "multi_discrete"])
            check_val_in_list("role[{}]".format(idx), self.role[idx], ["P1", "P2", "Random"])
            for jdx in range(3):
                check_val_in_list("characters[{}][{}]".format(idx, jdx), self.characters[idx][jdx], char_list)
            check_num_in_range("outfits[{}]".format(idx), self.outfits[idx], self.games_dict[self.game_id]["outfits"])
            check_val_in_list("super_art[{}]".format(idx), self.super_art[idx], ["Random", 1, 2, 3])
            check_val_in_list("fighting_style[{}]".format(idx), self.fighting_style[idx], ["Random", 1, 2, 3])
            for jdx in range(3):
                check_val_in_list("ultimate_style[{}][{}]".format(idx, jdx), self.ultimate_style[idx][jdx], ["Random", 1, 2])

    def _process_random_values(self):
        super()._process_random_values()

        characters_tmp = [[],[]]
        for idx in range(2):
            sampled_characters = self._sample_characters()

            for jdx in range(3):
                if self.characters[idx][jdx] == "Random":
                    characters_tmp[idx].append(sampled_characters[jdx])
                else:
                    characters_tmp[idx].append(self.characters[idx][jdx])

        self.characters = (tuple(characters_tmp[0]), tuple(characters_tmp[1]))

        if self.role[0] == "Random":
            if self.role[1] == "Random":
                idx = random.choice([1, 2])
                self.role = ("P{}".format(idx), "P{}".format((idx % 2) + 1))
            else:
                self.role = ("P1" if self.role[1] == "P2" else "P2", self.role[1])
        else:
            if self.role[1] == "Random":
                self.role = (self.role[0], "P1" if self.role[0] == "P2" else "P2")
        self.super_art = tuple([random.choice(list(range(1, 4))) if self.super_art[idx] == "Random" else self.super_art[idx] for idx in range(2)])
        self.fighting_style = tuple([random.choice(list(range(1, 4))) if self.fighting_style[idx] == "Random" else self.fighting_style[idx] for idx in range(2)])
        self.ultimate_style = tuple([[random.choice(list(range(1, 3))) if self.ultimate_style[idx][jdx] == "Random" else self.ultimate_style[idx][jdx] for jdx in range(3)] for idx in range(2)])

    def _get_action_spaces(self):
        action_spaces = [model.EnvSettings.ActionSpace.ACTION_SPACE_DISCRETE if self.action_space[idx] == "discrete" else \
                         model.EnvSettings.ActionSpace.ACTION_SPACE_MULTI_DISCRETE for idx in range(2)]

        return action_spaces

    def _get_player_specific_values(self):
        players_env_settings = []

        for idx in range(2):

            player_env_settings = model.EnvSettings.VariableEnvSettings.PlayerEnvSettings(
                role=self.role[idx],
                characters=[self.characters[idx][0], self.characters[idx][1], self.characters[idx][2]],
                outfits=self.outfits[idx],
                super_art=self.super_art[idx],
                fighting_style=self.fighting_style[idx],
                ultimate_style={"dash": self.ultimate_style[idx][0], "evade": self.ultimate_style[idx][1], "bar": self.ultimate_style[idx][2]}
            )

            players_env_settings.append(player_env_settings)

        return players_env_settings

@dataclass
class WrappersSettings:
    no_op_max: int = 0
    sticky_actions: int = 1
    clip_rewards: bool = False
    reward_normalization: bool = False
    reward_normalization_factor: float = 0.5
    frame_stack: int = 1
    dilation: int = 1
    actions_stack: int = 1
    scale: bool = False
    exclude_image_scaling: bool = False
    process_discrete_binary: bool = False
    scale_mod: int = 0
    frame_shape: Tuple[int, int, int] = (0, 0, 0)
    flatten: bool = False
    filter_keys: List[str] = None

    def sanity_check(self):
        check_num_in_range("no_op_max", self.no_op_max, [0, 12])
        check_num_in_range("sticky_actions", self.sticky_actions, [1, 12])
        check_num_in_range("frame_stack", self.frame_stack, [1, MAX_STACK_VALUE])
        check_num_in_range("dilation", self.dilation, [1, MAX_STACK_VALUE])
        check_num_in_range("actions_stack", self.actions_stack, [1, MAX_STACK_VALUE])
        check_num_in_range("scale_mod", self.scale_mod, [0, 0])
        check_num_in_range("reward_normalization_factor", self.reward_normalization_factor, [0.0, 1000000])

        check_val_in_list("frame_shape[2]", self.frame_shape[2], [0, 1, 3])
        check_num_in_range("frame_shape[0]", self.frame_shape[0], [0, MAX_FRAME_RES])
        check_num_in_range("frame_shape[1]", self.frame_shape[1], [0, MAX_FRAME_RES])
        if (min(self.frame_shape[0], self.frame_shape[1]) == 0 and
            max(self.frame_shape[0], self.frame_shape[1]) != 0):
            raise Exception("\"frame_shape[0] and frame_shape[1]\" must be both different from 0")

@dataclass
class RecordingSettings:
    dataset_path: str = "./"
    username: str = "username"
