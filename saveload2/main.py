from PyQt5 import QtCore
from . import utils, worker

class SaveLoad(QtCore.QObject):
    cmd_prefix = '!sl '
    sig_prepare_backup = QtCore.pyqtSignal(dict)
    sig_backup_immediately = QtCore.pyqtSignal()
    sig_prepare_restore = QtCore.pyqtSignal(dict)
    sig_confirm_restore = QtCore.pyqtSignal()
    sig_cancel_restore = QtCore.pyqtSignal()
    
    def __init__(self, log, core, config_filename, info_filename):
        super().__init__(core)
        SaveLoad.log = log
        self.core = core
        SaveLoad.info_filename = info_filename
        
        # load config, data and dependency
        try:
            SaveLoad.config = utils.Config(config_filename)
            self.info = utils.load_info()
            utils.confirm_backup_list(self.info)
            self.mclib = core.get_plugin('mcBasicLib')
            if not self.mclib:
                raise utils.InitError('dependency mcBasicLib not found.')
        except utils.InitError as e:
            self.log.error(e)
            self.log.error('Plugin saveload is not going to work.')
            return
        
        # create workers
        worker_thread = QtCore.QThread(self)
        self.backup_worker = worker.BackupWorker()
        self.backup_worker.moveToThread(worker_thread)
        worker_thread.start()
        self.countdown_worker = worker.CountdownWorker()

        # signal-slots and busy state
        # busy state transition is important
        self.busy_backup = False
        self.busy_restore = False
        self.mclib.sig_input.connect(self.on_input)

        self.sig_prepare_backup.connect(self.backup_worker.prepare) # carry backup info, F->T
        self.mclib.sig_input.connect(self.backup_worker.wait_flush) # check if flush is completed
        self.sig_backup_immediately.connect(self.backup_worker.start) # if not running, go ahead
        self.backup_worker.complete.connect(self.on_backup_complete) # carry backup info, T->F

        self.sig_prepare_restore.connect(self.countdown_worker.start) # carry target backup info, F->T
        self.sig_confirm_restore.connect(self.countdown_worker.confirm) # start counting down if in confirming period
        self.countdown_worker.timeout.connect(self.on_restore_timeout) # T->F
        self.countdown_worker.count.connect(self.on_restore_count) # carry second number
        self.countdown_worker.trigger.connect(self.on_restore_trigger) # carry target backup info, shutdown server, unzip, T->F before restarting
        self.sig_cancel_restore.connect(self.countdown_worker.cancel) # T->F
        
        # build callback dict
        self.cmd_list = {
            'help': self.help,
            'list': self.list,
            'backup ': self.prepare_backup,
            'restore ': self.restore,
            'confirm': self.confirm,
            'cancel': self.cancel,
            'rm ': self.remove
        }
    
    def busy(self):
        return self.busy_backup or self.busy_restore
    
    @QtCore.pyqtSlot(tuple)
    def on_input(self, msg):
        player, msg = msg
        if msg.startswith(SaveLoad.cmd_prefix):
            msg = msg[len(SaveLoad.cmd_prefix):]
            found = False
            for key, cmd in self.cmd_list.items():
                if msg.startswith(key):
                    cmd(player, msg[len(key):])
                    found = True
                    break
            if not found:
                self.mclib.tell(player, 'unrecognized command for plugin saveload')
    
    def broadcast(self, msg):
        self.log.info(msg)
        if self.core.server_running:
            self.mclib.tell('@a', msg)
    
    def help(self, player, msg):
        self.mclib.tell(player, SaveLoad.help_message)
    
    def list(self, player, msg):
        message = '\n'.join(['{}: '.format(i) + utils.format_description(backup) for i, backup in enumerate(self.info)])
        self.mclib.tell(player, message)
    
    def prepare_backup(self, player, msg):
        if self.busy():
            self.mclib.tell(player, 'plugin saveload busy')
            return
        if (self.config.permission_level == 'op') and not player.is_op():
            self.mclib.tell(player, 'permission denied')
            return
        self.busy_backup = True
        backup_name = msg.strip()
        if len(backup_name) == 0:
            backup_name = 'unnamed backup'
        backup_info = {
            'time': int(time.time()),
            'creator': player.name,
            'description': backup_name
        }
        self.broadcast('Start making backup')
        self.sig_prepare_backup.emit(backup_info)
        if self.core.server_running:
            self.core.write_server('/save-off')
            self.core.write_server('/save-all flush')
        else:
            self.sig_backup_immediately.emit()
    
    @QtCore.pyqtSlot(dict)
    def on_backup_complete(self, backup_info):
        self.busy_backup = False
        self.info.append(backup_info)
        while len(self.info) > self.config.max_backup_num:
            utils.try_remove(self.info[0])
            self.info.pop(0)
        utils.dump_info(self.info)
        message = 'Backup complete!\n' + utils.format_description(backup_info)
        if self.core.server_running:
            self.core.write_server('/save-on')
        self.broadcast(message)
        
    def restore(self, player, msg):
        if self.busy():
            self.mclib.tell(player, 'plugin busy')
            return
        if (self.config.permission_level == 'op') and not player.is_op():
            self.mclib.tell(player, 'permission denied')
            return
        msg = msg.strip()
        if msg == 'last':
            target = -1
        else:
            try:
                target = int(msg)
            except:
                self.mclib.tell(player, '"{}" is not a valid integer'.format(msg))
                return
        try:
            target = self.info[target]
        except IndexError:
            self.mclib.tell(player, 'target backup does not exist')
            return

        self.busy_restore = True
        self.broadcast('Preparing restoration, waiting for confirmation for {}s'.format(SaveLoad.config.restore_waiting))
        self.sig_prepare_restore.emit(target)
    
    def confirm(self, player, msg):
        if (self.config.permission_level == 'op') and not player.is_op():
            self.mclib.tell(player, 'permission denied')
            return
        if self.busy_restore:
            self.broadcast('restoration confirmed')
            self.sig_confirm_restore.emit()
    
    def cancel(self, player, msg):
        if self.busy_restore:
            self.sig_cancel_restore.emit()
            self.busy_restore = False
            self.broadcast('canceled')
    
    @QtCore.pyqtSlot()
    def on_restore_timeout(self):
        self.broadcast('Restoration canceled: confirmation timeout')
        self.busy_restore = False
    
    @QtCore.pyqtSlot(int)
    def on_restore_count(self, count):
        self.broadcast('Time before restoration: {}s'.format(count))
    
    @QtCore.pyqtSlot(dict)
    def on_restore_trigger(self, backup):
        target = utils.getfile(backup)
        self.broadcast('start restoration, stop server')
        def restore():
            self.log.info('start restoration, console freeze')
            try:
                self.core.sig_server_stop.disconnect(restore)
            except:
                pass
            utils.unpack(target)
            self.busy_restore = False
            self.core.start_server()

        if self.core.server_running:
            self.core.stop_server()
            self.core.sig_server_stop.connect(restore)
        else:
            restore()
    
    def remove(self, player, msg):
        if (self.config.permission_level == 'op') and not player.is_op():
            self.mclib.tell(player, 'permission denied')
            return
        try:
            target = int(msg)
        except:
            self.mclib.tell(player, '"{}" is not a valid integer'.format(msg))
            return
        if (target < 0) or (target >= len(self.info)):
            self.mclib.tell(player, '{} is out of range'.format(target))
        else:
            self.info.pop(target)
            self.mclib.tell(player, 'backup {} is removed successfully'.format(target))
