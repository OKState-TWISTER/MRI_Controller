from PySide6 import QtCore, QtWidgets
import time

class JitterController(QtWidgets.QWidget):
    send_command = QtCore.Signal(dict) # cmd
    send_command_to_target = QtCore.Signal(dict, str) #cmd, target

    def __init__(self, parent=None, scope=None, logger=None):
        super().__init__(parent=parent)
        self.scope = scope
        self.logger = logger

    def startMeasurement(self, duration=10.0, side=None):
        if self.logger is not None:
            self.logger.debug("[JITTER] Running Jitter Measurment")
        cmd = {}
        cmd['timestamp'] = time.time()
        cmd['cmd'] = "meas"
        cmd['args'] = {}
        cmd['args']['type'] = 'jitter'
        cmd['args']['duration'] = duration

        self.send_command_to_target.emit(cmd, "tx")
        self.send_command_to_target.emit(cmd, "rx")

            

        
