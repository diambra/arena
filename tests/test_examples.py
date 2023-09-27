import pytest
import sys
from os.path import expanduser
import os
from diambra.arena.utils.engine_mock import load_mocker

# Add the scripts directory to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples"))
sys.path.append(root_dir)

import diambra_arena_gist, episode_data_loader, episode_recording, multi_player_env, single_player_env, wrappers_options

def func(script, mocker, *args):

    load_mocker(mocker)

    try:
        return script.main(*args)
    except Exception as e:
        print(e)
        return 1

home_dir = expanduser("~")
dataset_path = os.path.join(home_dir, "DIAMBRA/episode_recording/mock")
use_controller = False
#[episode_data_loader, (dataset_path,)] # Removing episode data loader from tests because of unavailability of trajectories
scripts = [[diambra_arena_gist, ()], [single_player_env, ()], [multi_player_env, ()], [wrappers_options, ()],
           [episode_recording, (use_controller,)]]

@pytest.mark.parametrize("script", scripts)
def test_example_scripts(script, mocker):

    assert func(script[0], mocker, *script[1]) == 0