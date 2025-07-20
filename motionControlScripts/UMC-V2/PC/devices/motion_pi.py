from PySide6 import QtCore, QtWidgets, QtNetwork

class MotionPi(QtWidgets.QWidget):
    connected = QtCore.Signal()
    errorOccured = QtCore.Signal()
    data_received = QtCore.Signal(str)
    readyRead = QtCore.Signal() # Passthrough signal

    def __init__(self, ip_addr: str, port: int, retry_ms: int=None, logger=None, nickname=None, parent=None):
        super().__init__(parent=parent)
        self.ip_addr = ip_addr
        self.port = port
        self.retry = retry_ms
        self.logger = logger

        if nickname is None:
            self.nickname = ip_addr
        else:
            self.nickname = nickname

        if self.logger is not None:
            self.logger.debug(f"[MOTION PI] Logging Socket for {self.nickname}")

        self.socket = QtNetwork.QTcpSocket()
        self.socket.connectToHost(self.ip_addr, self.port)
        self.socket.errorOccurred.connect(self.failedToConnect)

        self.socket.readyRead.connect(self.readyRead.emit)
        self.socket.connected.connect(self.connected.emit)

        if self.retry is not None:
            self.reconn_timer = QtCore.QTimer(self)
            self.reconn_timer.setSingleShot(True)
            self.reconn_timer.setInterval(self.retry)
            self.reconn_timer.timeout.connect(self.on_reconn_timeout)

    def try_connect(self):
        self.socket.connectToHost(self.ip_addr, self.port)

    def readAll(self):
        return self.socket.readAll()

    @QtCore.Slot()
    def on_send_cmd(self, cmd):
        pass

    @QtCore.Slot()
    def on_reconn_timeout(self):
        if self.logger is not None:
            self.logger.warn(f"[MOTION PI] Attempting to reconnect to {self.nickname}")
        self.socket.connectToHost(self.ip_addr, self.port)

    @QtCore.Slot()
    def failedToConnect(self):
        if self.logger is not None:
            self.logger.error(f"[MOTION PI] Failed to connect to {self.nickname}.")

        if self.retry is not None:
            self.logger.warn(f"[MOTION PI] Starting reconnection timer")
            self.reconn_timer.start()
        

    
    