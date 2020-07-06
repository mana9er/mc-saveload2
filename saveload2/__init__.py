import os
from . import main, conf, utils
dependencies = ['mcBasicLib']

def load(log, core):
    root_dir = os.path.join(core.root_dir, 'saveload2')
    config_filename = os.path.join(root_dir, 'config.json')
    info_filename = os.path.join(root_dir, 'info.json')
    try:
        main.SaveLoad.config = conf.Config(config_filename)
    except utils.InitError as e:
        log.error(e)
        log.error('Plugin saveload is not going to work.')
        return
    main.SaveLoad.info_filename = info_filename
    main.SaveLoad(log, core)
    return None