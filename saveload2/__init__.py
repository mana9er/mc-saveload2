import os
import sys
from . import main, conf, utils
dependencies = ['mcBasicLib']

def load(log, core):
    root_dir = os.path.join(core.root_dir, 'saveload2')
    config_filename = os.path.join(root_dir, 'config.json')
    info_filename = os.path.join(root_dir, 'info.json')
    timer_filename = os.path.join(root_dir, 'auto-backup-timer.txt')
    try:
        conf.config = conf.Config(config_filename)
    except:
        log.error(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        log.error('Plugin saveload is not going to work.')
        return
    conf.config.info_filename = info_filename
    conf.config.timer_filename = timer_filename
    conf.config.log = log
    conf.help_message = conf.load_text()
    main.SaveLoad(log, core)
    return None