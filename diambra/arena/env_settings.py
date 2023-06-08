from dataclasses import dataclass
from typing import Union, List, Tuple
from diambra.arena.utils.gym_utils import available_games
import numpy as np

MAX_VAL = float("inf")
MIN_VAL = float("-inf")
MAX_FRAME_RES = 512
MAX_STACK_VALUE = 48

def check_num_in_range(key, value, bounds):
    assert (value >= bounds[0] and value <= bounds[1]), "\"{}\" ({}) value must be in the range {}".format(key, value, bounds)

def check_val_in_list(key, value, valid_list):
    assert (value in valid_list), "\"{}\" ({}) admissible values are {}".format(key, value, valid_list)


@dataclass
class EnvironmentSettings:

    game_id: str

    # System level
    step_ratio: int = 6
    disable_keyboard:bool = True
    disable_joystick: bool = True
    rank: int = 0
    seed: int = -1
    env_address: str = "localhost:50051"
    grpc_timeout: int = 600

    # Game level
    player: str = "Random"
    continue_game: float = 0.0
    show_final: bool = True
    difficulty: int = 3
    frame_shape: Tuple[int, int, int] = (0, 0, 0)

    tower: int = 3  # UMK3 Specific

    # Environment level
    hardcore: bool = False

    def sanity_check(self):
        self.games_dict = available_games(False)

        # TODO: consider using typing.Literal to specify lists of admissible values: NOTE: It requires Python 3.8+
        check_num_in_range("step_ratio", self.step_ratio, [1, 6])
        check_num_in_range("rank", self.rank, [0, MAX_VAL])
        check_num_in_range("seed", self.seed, [-1, MAX_VAL])
        check_num_in_range("grpc_timeout", self.grpc_timeout, [0, 3600])

        check_val_in_list("game_id", self.game_id, self.games_dict.keys())
        check_val_in_list("player", self.player, ["P1", "P2", "Random", "P1P2"])
        check_num_in_range("continue_game", self.continue_game, [MIN_VAL, 1.0])
        check_num_in_range("difficulty", self.difficulty, self.games_dict[self.game_id]["difficulty"][:2])

        check_num_in_range("frame_shape[0]", self.frame_shape[0], [0, MAX_FRAME_RES])
        check_num_in_range("frame_shape[1]", self.frame_shape[1], [0, MAX_FRAME_RES])
        if (min(self.frame_shape[0], self.frame_shape[1]) == 0 and
            max(self.frame_shape[0], self.frame_shape[1]) != 0):
            raise Exception("\"frame_shape[0] and frame_shape[1]\" must be either both different from or equal to 0")

        check_val_in_list("frame_shape[2]", self.frame_shape[2], [0, 1])

        check_num_in_range("tower", self.tower, [1, 4])

@dataclass
class EnvironmentSettings1P(EnvironmentSettings):

    # Player level
    characters: Union[str, Tuple[str], Tuple[str, str], Tuple[str, str, str]] = ("Random", "Random", "Random")
    char_outfits: int = 1
    action_space: str = "multi_discrete"
    attack_but_combination: bool = True

    super_art: int = 0  # SFIII Specific

    fighting_style: int = 0 # KOF Specific
    ultimate_style: Tuple[int, int, int] = (0, 0, 0) # KOF Specific

    def sanity_check(self):
        super().sanity_check()

        # Check for characters
        if isinstance(self.characters, str):
            self.characters = (self.characters, "Random", "Random")
        else:
            for idx in range(len(self.characters), 3):
                self.characters += ("Random", )

        check_num_in_range("char_outfits", self.char_outfits, self.games_dict[self.game_id]["outfits"])
        for idx in range(3):
            check_val_in_list("characters[{}]".format(idx), self.characters[idx],
                              np.append(self.games_dict[self.game_id]["char_list"], "Random"))
        check_val_in_list("action_space", self.action_space, ["discrete", "multi_discrete"])

        check_num_in_range("super_art", self.super_art, [0, 3])

        check_num_in_range("fighting_style", self.fighting_style, [0, 3])
        for idx in range(3):
            check_num_in_range("ultimate_style[{}]".format(idx), self.ultimate_style[idx], [0, 2])

@dataclass
class EnvironmentSettings2P(EnvironmentSettings):

    # Player level
    characters: Union[Tuple[str, str], Tuple[Tuple[str], Tuple[str]],
                      Tuple[Tuple[str, str], Tuple[str, str]],
                      Tuple[Tuple[str, str, str], Tuple[str, str, str]]] =\
                    (("Random", "Random", "Random"), ("Random", "Random", "Random"))
    char_outfits: Tuple[int, int] = (1, 1)
    action_space: Tuple[str, str] = ("multi_discrete", "multi_discrete")
    attack_but_combination: Tuple[bool, bool] = (True, True)

    super_art: Tuple[int, int] = (0, 0)  # SFIII Specific

    fighting_style: Tuple[int, int] = (0, 0)  # KOF Specific
    ultimate_style: Tuple[Tuple[int, int, int], Tuple[int, int, int]] = ((0, 0, 0), (0, 0, 0))  # KOF Specific

    def sanity_check(self):
        super().sanity_check()

        # Check for characters
        if isinstance(self.characters[0], str):
            self.characters = ((self.characters[0], "Random", "Random"),
                               (self.characters[1], "Random", "Random"))
        else:
            tmp_chars = [self.characters[0], self.characters[1]]
            for idx in range(len(self.characters[0]), 3):
                for jdx in range(2):
                    tmp_chars[jdx] += ("Random", )
            self.characters = tuple(tmp_chars)

        for jdx in range(2):
            check_num_in_range("char_outfits[{}]".format(jdx), self.char_outfits[jdx],
                               self.games_dict[self.game_id]["outfits"])
            for idx in range(3):
                check_val_in_list("characters[{}][{}]".format(jdx, idx), self.characters[jdx][idx],
                                  np.append(self.games_dict[self.game_id]["char_list"], "Random"))
            check_val_in_list("action_space[{}]".format(jdx), self.action_space[jdx], ["discrete", "multi_discrete"])

            check_num_in_range("super_art[{}]".format(jdx), self.super_art[jdx], [0, 3])

            check_num_in_range("fighting_style[{}]".format(jdx), self.fighting_style[jdx], [0, 3])
            for idx in range(3):
                check_num_in_range("ultimate_style[{}][{}]".format(jdx, idx), self.ultimate_style[jdx][idx], [0, 2])

@dataclass
class WrappersSettings:

    no_op_max: int = 0
    sticky_actions: int = 1
    clip_rewards: bool = False
    reward_normalization: bool = False
    reward_normalization_factor: float = 0.5
    frame_stack: int = 1
    actions_stack: int = 1
    scale: bool = False
    exclude_image_scaling: bool = False
    process_discrete_binary: bool = False
    scale_mod: int = 0
    hwc_obs_resize: Tuple[int, int, int] = (84, 84, 0)
    dilation: int = 1
    flatten: bool = False
    filter_keys: List[str] = None

    def sanity_check(self):

        no_op_max: int = 0
        sticky_actions: int = 1
        reward_normalization_factor: float = 0.5
        frame_stack: int = 1
        actions_stack: int = 1
        scale_mod: int = 0
        hwc_obs_resize: Tuple[int, int, int] = (84, 84, 0)
        dilation: int = 1

        check_num_in_range("no_op_max", self.no_op_max, [0, 12])
        check_num_in_range("sticky_actions", self.sticky_actions, [1, 12])
        check_num_in_range("frame_stack", self.frame_stack, [1, MAX_STACK_VALUE])
        check_num_in_range("actions_stack", self.actions_stack, [1, MAX_STACK_VALUE])
        check_num_in_range("dilation", self.dilation, [1, MAX_STACK_VALUE])
        check_num_in_range("scale_mod", self.scale_mod, [0, 0])

        check_val_in_list("hwc_obs_resize[2]", self.hwc_obs_resize[2], [0, 1, 3])
        if self.hwc_obs_resize[2] != 0:
            check_num_in_range("hwc_obs_resize[0]", self.hwc_obs_resize[0], [1, MAX_FRAME_RES])
            check_num_in_range("hwc_obs_resize[1]", self.hwc_obs_resize[1], [1, MAX_FRAME_RES])
            if (min(self.hwc_obs_resize[0], self.hwc_obs_resize[1]) == 0 and
                max(self.hwc_obs_resize[0], self.hwc_obs_resize[1]) != 0):
                raise Exception("\"hwc_obs_resize[0] and hwc_obs_resize[1]\" must be both different from 0")


@dataclass
class RecordingSettings:

    file_path: str
    username: str = "username"
    ignore_p2: bool = False
