import os
from . import main
dependencies = ['mcBasicLib']

def load(log, core):
    root_dir = os.path.join(core.root_dir, 'saveload2')
    config_filename = os.path.join(root_dir, 'config.json')
    info_filename = os.path.join(root_dir, 'info.json')
    main.SaveLoad(log, core, config_filename, info_filename)
    return None