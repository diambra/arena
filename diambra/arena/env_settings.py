from dataclasses import dataclass, field
from typing import Union, List, Tuple, Any, Dict
from diambra.arena.utils.gym_utils import available_games
from diambra.arena import SpaceTypes, Roles
import numpy as np
import random
from diambra.engine import model
import time
from dacite import from_dict, Config

def load_settings_flat_dict(target_class, settings: dict):
    return from_dict(target_class, settings, config=Config(strict=True))

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

def check_type(key, value, expected_type, admit_none=True):
    error_message = "ERROR: \"{}\" ({}) is of type {}, admissible types are {}".format(key, value, type(value), expected_type)
    if value is not None:
        assert isinstance(value, expected_type), error_message
    else:
        assert admit_none==True, "ERROR: \"{}\" ({}) cannot be NoneType".format(key, value)

def check_space_type(key, value, valid_list):
    error_message = "ERROR: \"{}\" ({}) admissible values are {}".format(key, SpaceTypes.Name(value), [SpaceTypes.Name(elem) for elem in valid_list])
    assert (value in valid_list), error_message

def check_roles(key, value, valid_list):
    error_message = "ERROR: \"{}\" ({}) admissible values are {}".format(key, Roles.Name(value), [Roles.Name(elem) for elem in valid_list])
    assert (value in valid_list), error_message

@dataclass
class EnvironmentSettingsBase:
    """Generic Environment Settings Class"""
    env_info = None
    games_dict = None

    # Environment settings
    game_id: str = "doapp"
    frame_shape: Tuple[int, int, int] = (0, 0, 0)
    step_ratio: int = 6
    disable_keyboard: bool = True
    disable_joystick: bool = True
    render_mode: Union[None, str] = None
    splash_screen: bool = True
    rank: int = 0
    env_address: str = None
    grpc_timeout: int = 600

    # Episode settings
    seed: Union[None, str] = None
    difficulty: Union[None, int] = None
    continue_game: float = 0.0
    show_final: bool = False
    tower: Union[None, int] = 3  # UMK3 Specific

    # Bookkeeping variables
    _last_seed: Union[None, int] = None
    pb_model: model = None

    episode_settings = ["seed", "difficulty", "continue_game", "show_final", "tower", "role",
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

            player_settings = self._get_player_specific_values()

            episode_settings = model.EnvSettings.EpisodeSettings(
                random_seed=self.seed,
                difficulty=self.difficulty,
                continue_game=self.continue_game,
                show_final=self.show_final,
                tower=self.tower,
                player_settings=player_settings,
            )
        else:
            episode_settings = model.EnvSettings.EpisodeSettings()

        request = model.EnvSettings(
            game_id=self.game_id,
            frame_shape=frame_shape,
            step_ratio=self.step_ratio,
            n_players=self.n_players,
            disable_keyboard=self.disable_keyboard,
            disable_joystick=self.disable_joystick,
            rank=self.rank,
            action_spaces=action_spaces,
            episode_settings=episode_settings,
        )

        self.pb_model = request

        return request

    def finalize_init(self, env_info):
        self.env_info = env_info
        self.games_dict = available_games(False)

        # Create list of valid characters
        self.valid_characters = [character for character in self.env_info.characters_info.char_list \
                                           if character not in self.env_info.characters_info.char_forbidden_list]

    def update_episode_settings(self, options: Dict[str, Any] = None):
        for k, v in options.items():
            if k in self.episode_settings:
                setattr(self, k, v)

        self._sanity_check()

        # Storing original attributes before sampling random ones
        original_settings_values =  {}
        for k in self.episode_settings:
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
            raise Exception("EnvironmentSettings class not correctly initialized")

        # TODO: consider using typing.Literal to specify lists of admissible values: NOTE: It requires Python 3.8+
        check_val_in_list("game_id", self.game_id, list(self.games_dict.keys()))
        check_num_in_range("step_ratio", self.step_ratio, [1, 6])
        check_num_in_range("frame_shape[0]", self.frame_shape[0], [0, MAX_FRAME_RES])
        check_num_in_range("frame_shape[1]", self.frame_shape[1], [0, MAX_FRAME_RES])
        if (min(self.frame_shape[0], self.frame_shape[1]) == 0 and
            max(self.frame_shape[0], self.frame_shape[1]) != 0):
            raise Exception("\"frame_shape[0] and frame_shape[1]\" must be either both different from or equal to 0")
        check_val_in_list("frame_shape[2]", self.frame_shape[2], [0, 1])
        if self.render_mode is not None:
            check_val_in_list("render_mode", self.render_mode, ["human", "rgb_array"])
        check_type("splash_screen", self.splash_screen, bool, admit_none=False)
        check_num_in_range("rank", self.rank, [0, MAX_VAL])
        check_type("env_address", self.env_address, str)
        check_num_in_range("grpc_timeout", self.grpc_timeout, [0, 3600])

        if self.seed is not None:
            check_num_in_range("seed", self.seed, [-1, MAX_VAL])
        difficulty_admissible_values = list(range(self.env_info.difficulty_bounds.min, self.env_info.difficulty_bounds.max + 1))
        difficulty_admissible_values.append(None)
        check_val_in_list("difficulty", self.difficulty, difficulty_admissible_values)
        check_num_in_range("continue_game", self.continue_game, [MIN_VAL, 1.0])
        check_type("show_final", self.show_final, bool)
        check_val_in_list("tower", self.tower, [None, 1, 2, 3, 4])

    def _process_random_values(self):
        if self.difficulty is None:
            self.difficulty = random.choice(list(range(self.env_info.difficulty_bounds.min, self.env_info.difficulty_bounds.max + 1)))
        if self.tower is None:
            self.tower = random.choice(list(range(1, 5)))

@dataclass
class EnvironmentSettings(EnvironmentSettingsBase):
    """Single Agent Environment Settings Class"""
    # Env settings
    n_players: int = 1
    action_space: int = SpaceTypes.MULTI_DISCRETE

    # Episode settings
    role: Union[None, int] = None
    characters: Union[None, str, Tuple[str], Tuple[str, str], Tuple[str, str, str]] = None
    outfits: int = 1
    super_art: Union[None, int] = None  # SFIII Specific
    fighting_style: Union[None, int] = None # KOF Specific
    ultimate_style: Union[None, Tuple[int, int, int]] = None # KOF Specific

    def _sanity_check(self):
        super()._sanity_check()

        # Env settings
        check_num_in_range("n_players", self.n_players, [1, 1])
        check_space_type("action_space", self.action_space, [SpaceTypes.DISCRETE, SpaceTypes.MULTI_DISCRETE])

        # Episode settings
        if self.role is not None:
            check_roles("role", self.role, [Roles.P1, Roles.P2])
        if isinstance(self.characters, str) or self.characters is None:
            self.characters = (self.characters, None, None)
        else:
            for _ in range(len(self.characters), 3):
                self.characters += (None, )
        char_list = list(self.env_info.characters_info.char_list)
        char_list.append(None)
        for idx in range(3):
            check_val_in_list("characters[{}]".format(idx), self.characters[idx], char_list)
        check_num_in_range("outfits", self.outfits, self.games_dict[self.game_id]["outfits"])
        check_val_in_list("super_art", self.super_art, [None, 1, 2, 3])
        check_val_in_list("fighting_style", self.fighting_style, [None, 1, 2, 3])
        if self.ultimate_style is not None:
            for idx in range(3):
                check_val_in_list("ultimate_style[{}]".format(idx), self.ultimate_style[idx], [1, 2])

    def _get_action_spaces(self):
        return [self.action_space]

    def _process_random_values(self):
        super()._process_random_values()

        sampled_characters = self._sample_characters()
        characters_tmp = []
        for idx in range(3):
            if self.characters[idx] is None:
                characters_tmp.append(sampled_characters[idx])
            else:
                characters_tmp.append(self.characters[idx])
        self.characters = tuple(characters_tmp)

        if self.role is None:
            self.role = random.choice([Roles.P1, Roles.P2])
        if self.super_art is None:
            self.super_art = random.choice(list(range(1, 4)))
        if self.fighting_style is None:
            self.fighting_style = random.choice(list(range(1, 4)))
        if self.ultimate_style is None:
            self.ultimate_style = tuple([random.choice(list(range(1, 3))) for _ in range(3)])

    def _get_player_specific_values(self):
        player_settings = model.EnvSettings.EpisodeSettings.PlayerSettings(
            role=self.role,
            characters=[self.characters[idx] for idx in range(self.env_info.characters_info.chars_to_select)],
            outfits=self.outfits,
            super_art=self.super_art,
            fighting_style=self.fighting_style,
            ultimate_style={"dash": self.ultimate_style[0], "evade": self.ultimate_style[1], "bar": self.ultimate_style[2]}
        )

        return [player_settings]

@dataclass
class EnvironmentSettingsMultiAgent(EnvironmentSettingsBase):
    """Multi Agent Environment Settings Class"""
    # Env Settings
    n_players: int = 2
    action_space: Tuple[int, int] = (SpaceTypes.MULTI_DISCRETE, SpaceTypes.MULTI_DISCRETE)

    # Episode Settings
    role: Union[Tuple[None, None], Tuple[int, int]] = (None, None)
    characters: Union[Tuple[None, None], Tuple[str, None], Tuple[None, str], Tuple[str, str],
                      Tuple[Tuple[str], Tuple[str]], Tuple[Tuple[str, str], Tuple[str, str]],
                      Tuple[Tuple[str, str, str], Tuple[str, str, str]]] = (None, None)
    outfits: Tuple[int, int] = (1, 1)
    super_art: Union[Tuple[None, None], Tuple[int, int]] = (None, None)  # SFIII Specific
    fighting_style: Union[Tuple[None, None], Tuple[int, int]] = (None, None)  # KOF Specific
    ultimate_style: Union[Tuple[None, None], Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = (None, None)  # KOF Specific

    def _sanity_check(self):
        super()._sanity_check()

        # Env Settings
        check_num_in_range("n_players", self.n_players, [2, 2])
        for idx in range(2):
            check_space_type("action_space[{}]".format(idx), self.action_space[idx], [SpaceTypes.DISCRETE, SpaceTypes.MULTI_DISCRETE])

        # Episode Settings
        if isinstance(self.characters[0], str) or self.characters[0] is None:
            self.characters = ((self.characters[0], None, None), (self.characters[1], None, None))
        else:
            tmp_chars = [self.characters[0], self.characters[1]]
            for _ in range(len(self.characters[0]), 3):
                for jdx in range(2):
                    tmp_chars[jdx] += (None, )
            self.characters = tuple(tmp_chars)
        char_list = list(self.env_info.characters_info.char_list)
        char_list.append(None)
        for idx in range(2):
            if self.role[idx] is not None:
                check_roles("role[{}]".format(idx), self.role[idx], [Roles.P1, Roles.P2])
            for jdx in range(3):
                check_val_in_list("characters[{}][{}]".format(idx, jdx), self.characters[idx][jdx], char_list)
            check_num_in_range("outfits[{}]".format(idx), self.outfits[idx], self.games_dict[self.game_id]["outfits"])
            check_val_in_list("super_art[{}]".format(idx), self.super_art[idx], [None, 1, 2, 3])
            check_val_in_list("fighting_style[{}]".format(idx), self.fighting_style[idx], [None, 1, 2, 3])
            if self.ultimate_style[idx] is not None:
                for jdx in range(3):
                    check_val_in_list("ultimate_style[{}][{}]".format(idx, jdx), self.ultimate_style[idx][jdx], [1, 2])

    def _process_random_values(self):
        super()._process_random_values()

        characters_tmp = [[],[]]

        for idx, characters in enumerate(self.characters):
            sampled_characters = self._sample_characters()
            for jdx in range(3):
                if characters[jdx] is None:
                    characters_tmp[idx].append(sampled_characters[jdx])
                else:
                    characters_tmp[idx].append(characters[jdx])

        self.characters = (tuple(characters_tmp[0]), tuple(characters_tmp[1]))

        if self.role[0] is None:
            if self.role[1] is None:
                coin = random.choice([True, False])
                self.role = (Roles.P1, Roles.P2) if coin is True else (Roles.P2, Roles.P1)
            else:
                self.role = (Roles.P1 if self.role[1] == Roles.P2 else Roles.P2, self.role[1])
        else:
            if self.role[1] is None:
                self.role = (self.role[0], Roles.P1 if self.role[0] == Roles.P2 else Roles.P2)

        self.super_art = tuple([random.choice(list(range(1, 4))) if self.super_art[idx] is None else self.super_art[idx] for idx in range(2)])
        self.fighting_style = tuple([random.choice(list(range(1, 4))) if self.fighting_style[idx] is None else self.fighting_style[idx] for idx in range(2)])
        self.ultimate_style = tuple([[random.choice(list(range(1, 3))) for _ in range(3)] if self.ultimate_style[idx] is None else self.ultimate_style[idx] for idx in range(2)])

    def _get_action_spaces(self):
        return [action_space for action_space in self.action_space]

    def _get_player_specific_values(self):
        players_env_settings = []

        for idx in range(2):
            player_settings = model.EnvSettings.EpisodeSettings.PlayerSettings(
                role=self.role[idx],
                characters=[self.characters[idx][jdx] for jdx in range(self.env_info.characters_info.chars_to_select)],
                outfits=self.outfits[idx],
                super_art=self.super_art[idx],
                fighting_style=self.fighting_style[idx],
                ultimate_style={"dash": self.ultimate_style[idx][0], "evade": self.ultimate_style[idx][1], "bar": self.ultimate_style[idx][2]}
            )

            players_env_settings.append(player_settings)

        return players_env_settings

@dataclass
class WrappersSettings:
    no_op_max: int = 0
    repeat_action: int = 1
    normalize_reward: bool = False
    normalization_factor: float = 0.5
    clip_reward: bool = False
    no_attack_buttons_combinations: bool = False
    frame_shape: Tuple[int, int, int] = (0, 0, 0)
    stack_frames: int = 1
    dilation: int = 1
    add_last_action: bool = False
    stack_actions: int = 1
    scale: bool = False
    exclude_image_scaling: bool = False
    process_discrete_binary: bool = False
    role_relative: bool = False
    flatten: bool = False
    filter_keys: List[str] = field(default_factory=list)
    wrappers: List[List[Any]] = field(default_factory=list)

    def sanity_check(self):
        check_num_in_range("no_op_max", self.no_op_max, [0, 12])
        check_num_in_range("repeat_action", self.repeat_action, [1, 12])
        check_type("normalize_reward", self.normalize_reward, bool, admit_none=False)
        check_num_in_range("normalization_factor", self.normalization_factor, [0.0, 1000000])
        check_type("clip_reward", self.clip_reward, bool, admit_none=False)
        check_type("no_attack_buttons_combinations", self.no_attack_buttons_combinations, bool, admit_none=False)
        check_val_in_list("frame_shape[2]", self.frame_shape[2], [0, 1, 3])
        check_num_in_range("frame_shape[0]", self.frame_shape[0], [0, MAX_FRAME_RES])
        check_num_in_range("frame_shape[1]", self.frame_shape[1], [0, MAX_FRAME_RES])
        if (min(self.frame_shape[0], self.frame_shape[1]) == 0 and
            max(self.frame_shape[0], self.frame_shape[1]) != 0):
            raise Exception("\"frame_shape[0] and frame_shape[1]\" must be both different from 0")
        check_num_in_range("stack_frames", self.stack_frames, [1, MAX_STACK_VALUE])
        check_num_in_range("dilation", self.dilation, [1, MAX_STACK_VALUE])
        check_type("add_last_action", self.add_last_action, bool, admit_none=False)
        stack_actions_bounds = [1, 1]
        if self.add_last_action is True:
            stack_actions_bounds = [1, MAX_STACK_VALUE]
        check_num_in_range("stack_actions", self.stack_actions, stack_actions_bounds)
        check_type("scale", self.scale, bool, admit_none=False)
        check_type("exclude_image_scaling", self.exclude_image_scaling, bool, admit_none=False)
        check_type("process_discrete_binary", self.process_discrete_binary, bool, admit_none=False)
        check_type("role_relative", self.role_relative, bool, admit_none=False)
        check_type("flatten", self.flatten, bool, admit_none=False)
        check_type("filter_keys", self.filter_keys, list, admit_none=False)
        check_type("wrappers", self.wrappers, list, admit_none=False)

@dataclass
class RecordingSettings:
    dataset_path:  Union[None, str] = None
    username: Union[None, str] = None

    def sanity_check(self):
        check_type("dataset_path", self.dataset_path, str)
        check_type("username", self.username, str)
