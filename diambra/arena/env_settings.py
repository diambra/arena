from dataclasses import dataclass
from typing import Union, List, Tuple
from diambra.arena.utils.gym_utils import available_games

MAX_VAL = float("inf")
MIX_VAL = float("-inf")

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
    grpc_timeout: int = 60

    # Game level
    player: str = "Random"
    continue_game: float = 0.0
    show_final: bool = True
    difficulty: int = 3
    frame_shape: Tuple[int, int, int] = (0, 0, 0)

    tower: int = 3  # UMK3 Specific

    # Environment level
    hardcore: bool = False

    def __init__(self):
        self.games_dict = available_games(False)

        check_num_in_range("step_ratio", self.step_ratio, [1, 6])
        check_num_in_range("rank", self.rank, [0, MAX_VAL])
        check_num_in_range("seed", self.seed, [-1, MAX_VAL])
        check_num_in_range("grpc_timeout", self.grpc_timeout, [0, 120])

        check_val_in_list("game_id", self.game_id, self.games_dict.keys())
        check_val_in_list("player", self.player, ["P1", "P2", "Random", "P1P2"])
        check_num_in_range("continue_game", self.continue_game, [MIN_VAL, 1.0])
        check_num_in_range("difficulty", self.difficulty, self.games_dict[self.game_id]["difficulty"][:2])

        check_num_in_range("frame_shape[0]", self.frame_shape[0], [0, MAX_VAL])
        check_num_in_range("frame_shape[1]", self.frame_shape[1], [0, MAX_VAL])
        if (min(self.frame_shape[0], self.frame_shape[1]) == 0 and
            max(self.frame_shape[0], self.frame_shape[1]) != 0):
            raise Exception("\"frame_shape[0] and frame_shape[1]\" must be either both different from or equal to 0")

        check_val_in_list("frame_shape[2]", self.frame_shape[2], [0, 1, 3])

        check_num_in_range("tower", self.tower, [1, 4])

@dataclass
class EnvironmentSettings1P(EnvironmentSettings):

    # Player level
    characters: Union[str, Tuple[str], Tuple[str, str], Tuple[str, str, str]] = ("Random", "Random", "Random")
    char_outfits: int = 2
    action_space: str = "multi_discrete"
    attack_but_combination: bool = True

    super_art: int = 0  # SFIII Specific

    fighting_style: int = 0 # KOF Specific
    ultimate_style: Tuple[int, int, int] = (0, 0, 0) # KOF Specific

    def __init__(self):
        super().__init__()

        # Check for characters
        if type(self.characters) == str:
            self.characters = (self.characters, "Random", "Random")
        elif type(self.characters) == Tuple[str]:
            self.characters = (self.characters[0], "Random", "Random")
        elif type(self.characters) == Tuple[str, str]:
            self.characters = (self.characters[0], self.characters[1], "Random")

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
    char_outfits: Tuple[int, int] = (2, 2)
    action_space: Tuple[int, int] = ("multi_discrete", "multi_discrete")
    attack_but_combination: Tuple[bool, bool] = (True, True)

    super_art: Tuple[int, int] = (0, 0)  # SFIII Specific

    fighting_style: Tuple[int, int] = (0, 0)  # KOF Specific
    ultimate_style: Tuple[Tuple[int, int, int], Tuple[int, int, int]] = ((0, 0, 0), (0, 0, 0))  # KOF Specific

    def __init__(self):
        super().__init__()

        # Check for characters
        if type(self.characters[0]) == str:
            self.characters = ((self.characters[0], "Random", "Random"),
                               (self.characters[1], "Random", "Random"))
        elif type(self.characters[0]) == Tuple[str]:
            self.characters = ((self.characters[0][0], "Random", "Random"),
                               (self.characters[1][0], "Random", "Random"))
        elif type(self.characters[0]) == Tuple[str, str]:
            self.characters = ((self.characters[0][0], self.characters[0][1], "Random"),
                               (self.characters[1][0], self.characters[1][1], "Random"))

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
