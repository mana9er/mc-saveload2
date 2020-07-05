import sys
import os
import json
from .main import SaveLoad


class InitError(Exception):
    pass

def init_assert(expr, msg):
    if not expr:
        raise InitError(msg)

class Config:
    
    def __init__(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as config_f:
                config_dict = json.load(config_f)
            self.permission_level = config_dict['permission-level']
            self.max_backup_num = config_dict['max-backup-num']
            self.save_path = config_dict['save-path']
            self.format = config_dict['format']
            self.restore_waiting = config_dict['restore-waiting-sec']
            self.restore_countdown = config_dict['restore-countdown-sec']
        except:
            raise InitError(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        init_assert((permission_level == 'op') or (permission_level == 'any'), 'permission-level should be op or any')
        init_assert(isinstance(self.max_backup_num, int) and (self.max_backup_num > 0), 'max-backup-num should be positive integer')
        init_assert(os.path.isdir(self.save_path), 'save-path is not a valid directory')
        init_assert(self.format == 'zip', 'currently support zip format only')
        init_assert(isinstance(self.restore_waiting, int) and (self.restore_waiting > 0), 'restore-waiting-sec should be positive integer')
        init_assert(isinstance(self.restore_countdown, int) and (self.restore_countdown > 0), 'restore-countdown-sec should be positive integer')
        
def dump_info(info):
    filename = SaveLoad.info_filename
    with open(filename, 'w', encoding='utf-8') as info_f:
        json.dump(info, info_f, indent=2)

def load_info():
    '''
    load a list of dict, containing key:
        time (time stamp, int)
        creator (player name, string)
        description (string)
    '''
    filename = SaveLoad.info_filename
    if not os.path.exists(filename):
        SaveLoad.logger.warning('Failed to find previous backup infomation')
        SaveLoad.logger.info('Creating empty info file...')
        info = []
        dump_info(info)
        return info
    try:
        with open(filename, 'r', encoding='utf-8') as info_f:
            info = json.load(info_f)
        init_assert(isinstance(info, list), 'When loading info file: top-level entity should be a list.')
        for backup in info:
            init_assert(isinstance(backup['time'], int), 'When loading info file: time should be integer')
            init_assert(isinstance(backup['creator'], str), 'When loading info file: creator should be string')
            init_assert(isinstance(backup['description'], str), 'When loading info file: description should be string')
    except InitError:
        raise
    except:
        raise InitError(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
    return info

def getfile(info_dict):
    return os.path.join(SaveLoad.config.save_path, 'backup-{}.zip'.format(info_dict['time']))

def confirm_backup_list(info_list):
    for i in reversed(range(len(info_list))):
        if not os.path.isfile(getfile(info_list[i])):
            info_list.pop(i)

def pack(target):
    with ZipFile(target, 'w', compression=ZIP_DEFLATED, allowZip64=True, compresslevel=1) as zipf:
        for root, dirs, files in os.walk('.'):
            for f in files:
                zipf.write(os.path.join(root, f))

def unpack(target):
    for filename in os.listdir('.'):
        if os.path.isdir(filename):
            shutil.rmtree(filename)
        else:
            os.remove(filename)
    shutil.unpack_archive(target, '.')

def try_remove(backup):
    filename = getfile(backup)
    if os.path.isfile(filename):
        os.remove(filename)

def format_description(backup):
    time_string = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(backup['time']))
    return 'Backup made at {} by {}. Description: {}'.format(time_string, backup['creator'], backup['description'])