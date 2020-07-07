import sys
import json
import os
from . import utils

class Config:
    
    def __init__(self, filename):
        with open(filename, 'r', encoding='utf-8') as config_f:
            config_dict = json.load(config_f)
        self.permission_level = config_dict['permission-level']
        self.max_backup_num = config_dict['max-backup-num']
        self.save_path = config_dict['save-path']
        self.format = config_dict['format']
        self.restore_waiting = config_dict['restore-waiting-sec']
        self.restore_countdown = config_dict['restore-countdown-sec']
        self.auto_backup_interval = config_dict['auto-backup-hours']
        utils.init_assert((self.permission_level == 'op') or (self.permission_level == 'any'), 'permission-level should be op or any')
        utils.init_assert(isinstance(self.max_backup_num, int) and (self.max_backup_num > 0), 'max-backup-num should be positive integer')
        utils.init_assert(os.path.isdir(self.save_path), 'save-path is not a valid directory')
        utils.init_assert(self.format == 'zip', 'currently support zip format only')
        utils.init_assert(isinstance(self.restore_waiting, int) and (self.restore_waiting > 0), 'restore-waiting-sec should be positive integer')
        utils.init_assert(isinstance(self.restore_countdown, int) and (self.restore_countdown > 0), 'restore-countdown-sec should be positive integer')
        utils.init_assert(isinstance(self.auto_backup_interval, int) and (self.auto_backup_interval > 0), 'auto-backup-hours should be positive integer')


def load_text():
    return ('"!sl help": show this help message.\n'
    '"!sl list": list the existing backups.\n'
    '"!sl backup [description]": make a backup for the current server status. You can add description by adding optional argument to the end.\n'
    '"!sl restore <last | int:id>": use the selected backup to restore the server. You can use keyword "last" to indicate the latest backup. This command requires confirmation.\n'
    '"!sl confirm": confirm the restoration. Once confirmed, the count down will start immediately.\n'
    '"!sl cancel": cancel the restoration. Can be called before or after confirmation.\n'
    '"!sl rm <int:id>": remove a backup by id')