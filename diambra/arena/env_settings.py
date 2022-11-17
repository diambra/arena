from dataclasses import dataclass
from typing import Union, List, Tuple

@dataclass
class EnvironmentSettings:

    # System level
    step_ratio: int = 6
    disable_keyboard:bool = True
    disable_joystick: bool = True
    rank: int = 0
    seed: int = -1
    grpc_timeout: int = 60

    # Game level
    game_id: str = "doapp"
    player: str = "Random"
    continue_game: float = 0.0
    show_final: bool = True
    difficulty: int = 3
    frame_shape: Tuple[int, int, int] = (0, 0, 0)

    tower: int = 3  # UMK3 Specific

    # Environment level
    hardcore: bool = False

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

    def sanity_check(self):

        # Check for characters
        if type(self.characters) == str:
            self.characters = (self.characters, "Random", "Random")
        elif type(self.characters) == Tuple[str]:
            self.characters = (self.characters[0], "Random", "Random")
        elif type(self.characters) == Tuple[str, str]:
            self.characters = (self.characters[0], self.characters[1], "Random")

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

    def sanity_check(self):

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

