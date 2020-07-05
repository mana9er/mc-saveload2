from PyQt5 import QtCore
from .main import SaveLoad
from . import utils

class BackupWorker(QtCore.QObject):
    complete = QtCore.pyqtSignal()
    
    
    def __init__(self):
        super().__init__()
        self.info = None
    
    @QtCore.pyqtSlot(dict)
    def prepare(self, info):
        self.info = info
    
    def start(self):
        if not self.info:
            return
        utils.pack(utils.getfile(self.info))
        self.complete.emit(self.info)
        self.info = None
    
    @QtCore.pyqtSlot(tuple)
    def wait_flush(self, msg):
        if not self.info:
            return
        player, text = msg
        match_obj = re.match(r'[^<>]*?\[Server thread/INFO\] \[minecraft/DedicatedServer\]: (.*)$', text)
        if match_obj:
            if match_obj.group(1).find('Saved the game') >= 0:
                self.start()


class CountdownWorker(QtCore.QObject):
    timeout = QtCore.pyqtSignal()
    count = QtCore.pyqtSignal(int)
    trigger = QtCore.pyqtSignal(dict)
    
    def __init__(self):
        self.info = None
        self.state = 0
        # 0: waiting
        # 1: waiting for confirmation
        # 2: counting down
        self.cur_count = 0

        self.confirm_timer = QTimer()
        self.confirm_timer.setInterval(SaveLoad.config.restore_waiting * 1000)
        self.confirm_timer.setSingleShot(True)
        self.confirm_timer.timeout.connect(self.on_confirm_timeout)
        self.countdown_timer = QTimer()
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self.on_countdown)

    @QtCore.pyqtSlot(dict)
    def start(self, info):
        self.info = info
        self.state = 1
        self.confirm_timer.start()

    @QtCore.pyqtSlot()
    def on_confirm_timeout(self):
        self.state = 0
        self.info = None
        self.timeout.emit()

    @QtCore.pyqtSlot()
    def confirm(self):
        if self.state == 1:
            self.state = 2
            self.confirm_timer.stop()
            self.cur_count = SaveLoad.config.restore_countdown
            self.countdown_timer.start()

    @QtCore.pyqtSlot()
    def on_countdown(self):
        self.cur_count -= 1
        if self.cur_count == 0:
            self.countdown_timer.stop()
            self.state = 0
            self.trigger.emit(self.info)
            self.info = None
        else:
            self.count.emit(self.cur_count)

    @QtCore.pyqtSlot()
    def cancel(self):
        if self.state != 0:
            self.confirm_timer.stop()
            self.countdown_timer.stop()
            self.state = 0
            self.info = None
        
        