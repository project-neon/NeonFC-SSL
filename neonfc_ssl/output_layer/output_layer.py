from neonfc_ssl.core import Layer
from .comm import GrComm, SerialComm

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.control_layer.control_data import ControlData


class OutputLayer(Layer):
    def __init__(self, config, log_q, event_pipe):
        super().__init__("OutputLayer", config, log_q, event_pipe)
        self.gr_comm = GrComm(self.config, self.log)
        self.serial_comm = SerialComm(self.config, self.log)

        self.use_gr_sim = self.config["use_gr_sim"]

    def _step(self, data: 'ControlData'):
        if self.use_gr_sim:
            self.gr_comm.update(data)
        else:
            self.serial_comm.update(data)

    def _start(self):
        if self.use_gr_sim:
            self.gr_comm.start()
        else:
            self.serial_comm.start()
