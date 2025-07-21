# This controller will work with the twister_api and pyvisa
# to wrap control of the DSO into Qt, allowing for Qt-Style
# Event handling (Signals & Slots)
from PySide6 import QtCore, QtWidgets, QtGui, QtNetwork
from PySide6.QtWidgets import QSizePolicy

import pyvisa
from twister_api.oscilloscope_interface import Oscilloscope
from logger import logger

class ScopeController(QtWidgets.QWidget):
    failed_to_connect = QtCore.Signal()
    connected = QtCore.Signal()
    
    def __init__(self, parent=None, logger=None, retry_rate=None):
        super().__init__(parent=parent)
        self.logger = logger
        self.retry_rate = retry_rate
        self.connect_to_scope()

    def get_peak(self):
        if self.scope == None:
            if self.logger is not None:
                logger.warn('No scope connected. Acting in dummy mode. Returning 0 dBm @ 10 GHz')
                return 0, 10e9
        try:
            peakPWR_temp = self.scope.get_fft_peak(2)
            peak_freq_temp = self.scope.do_query(f":FUNCtion2:FFT:PEAK:FREQ?")
        except pyvisa.errors.VisaIOError:
            self.sweep_log.error(f"Trouble reaching scope!")
            self.scope_err.emit()
        peak_val = peakPWR_temp
        peak_freq = peak_freq_temp.strip('""')

        return peak_val, peak_freq
    
    def connect_to_scope(self):
        try:
            self.rm = pyvisa.ResourceManager()
            self.Infiniium = self.rm.open_resource("TCPIP0::192.168.27.10::inst0::INSTR")
            self.Infiniium.timeout = 20000
            self.Infiniium.clear()
            self.scope = Oscilloscope(
                visa_address="TCPIP0::192.168.27.10::inst0::INSTR", debug=True)
        except ValueError as ve:
            self.logger.warn(f"Couldn't connect to scope. Running as dummy...\n\tReason: {ve}")
            self.scope = None
        except pyvisa.errors.VisaIOError as ve:
            self.logger.warn(f"Couldn't connect to scope. Running as dummy...\n\tReason: {ve}")
            self.scope = None

    def isConnected(self):
        return False if self.scope is None else True
    