from PySide6 import QtCore, QtWidgets, QtNetwork
import json

class MotionPi(QtWidgets.QWidget):
    connected = QtCore.Signal()
    errorOccured = QtCore.Signal()
    data_received = QtCore.Signal(str, dict)
    readyRead = QtCore.Signal() # Passthrough signal
    awaiting_command = QtCore.Signal()
    ready_for_command = QtCore.Signal()

    def __init__(self, ip_addr: str, port: int, retry_ms: int=None, logger=None, nickname=None, parent=None):
        super().__init__(parent=parent)
        self.ip_addr = ip_addr
        self.port = port
        self.retry = retry_ms
        self.logger = logger
        self.readBuffer = QtCore.QByteArray()

        if nickname is None:
            self.nickname = ip_addr
        else:
            self.nickname = nickname

        if self.logger is not None:
            self.logger.debug(f"[MOTION PI] Logging Socket for {self.nickname}")

        self.socket = QtNetwork.QTcpSocket()
        self.socket.connectToHost(self.ip_addr, self.port)
        self.socket.errorOccurred.connect(self.failedToConnect)

        # self.socket.readyRead.connect(self.readyRead.emit)
        self.socket.readyRead.connect(self.onReadyRead)
        self.socket.connected.connect(self.connected.emit)

        if self.retry is not None:
            self.reconn_timer = QtCore.QTimer(self)
            self.reconn_timer.setSingleShot(True)
            self.reconn_timer.setInterval(self.retry)
            self.reconn_timer.timeout.connect(self.on_reconn_timeout)

        self.cmd_timer = QtCore.QTimer(self)
        self.cmd_timer.setSingleShot(True)
        self.cmd_timer.setInterval(30000)
        self.cmd_timer.timeout.connect(self.on_cmd_timeout)
        

         

    def try_connect(self):
        self.socket.connectToHost(self.ip_addr, self.port)

    def readAll(self):
        return self.socket.readAll()

    def bytesAvailable(self):
        return self.socket.bytesAvailable

    def send_cmd(self, cmd):
        if self.logger is not None:
            self.logger.debug(f"Sending Command {cmd}")
        toSend = json.dumps(cmd)
        self.socket.write(f"{toSend}/UTOL".encode())
        self.socket.flush()
        self.last_cmd = cmd
        self.awaiting_command.emit()

    @QtCore.Slot()
    def on_reconn_timeout(self):
        if self.logger is not None:
            self.logger.warn(f"[MOTION PI] Attempting to reconnect to {self.nickname}")
        self.socket.connectToHost(self.ip_addr, self.port)
    
    @QtCore.Slot()
    def on_cmd_timeout(self):
        if self.logger is not None:
            self.logger.warn(f"[MOTION PI] No response from {self.nickname}. Resending command, timestamp: {self.last_cmd['timestamp']}")
        self.send_cmd(self.last_cmd)

    @QtCore.Slot()
    def failedToConnect(self):
        if self.logger is not None:
            self.logger.error(f"[MOTION PI] Failed to connect to {self.nickname}.")

        if self.retry is not None:
            self.logger.warn(f"[MOTION PI] Starting reconnection timer")
            self.reconn_timer.start()
        
    @QtCore.Slot()
    def onReadyRead(self):
        res = QtCore.QByteArray()
        res.append(self.socket.readAll())
        check = res[-5:].data().decode()
        # if self.logger is not None:
        #     self.logger.debug(f"CHECK: {check}")
        self.readBuffer.append(res)
        if check != "/UTOL":
            return
        if res.isNull():
            if self.logger is not None:
                self.logger.error(f"NULL BYTES FROM TCP SOCKET")
            return
        res_str = self.readBuffer.data().decode().split("/UTOL")[0]
        # if self.logger is not None:
        #     self.logger.debug(f"Received: {res_str}")
        
        data = json.loads(res_str)

        # if self.logger is not None:
        #     self.logger.debug(f"JSON LOADS: {data}")

        self.data_received.emit(self.nickname, data)
        self.ready_for_command.emit()
        self.readBuffer = QtCore.QByteArray()
    
    