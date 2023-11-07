# Diambra Agents

import importlib_resources
import sheeprl.utils.env

from diambra.arena.sheeprl.make_sheeprl_env import make_sheeprl_env

sheeprl.utils.env.make_env = make_sheeprl_env
CONFIGS_PATH = str(importlib_resources.files("sheeprl.configs"))
