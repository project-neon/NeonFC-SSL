from neonfc_ssl.core import Layer
from .comm import SimCliComm, SerialComm

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.control_layer.control_data import ControlData


class OutputLayer(Layer):
    def __init__(self, config, log_q):
        super().__init__("OutputLayer", config, log_q)
        self.sim_comm = SimCliComm(self.config, self.logger)
        self.serial_comm = SerialComm(self.config, self.logger)

        self.use_sim = self.config["use_gr_sim"]

    def _step(self, data: 'ControlData'):
        if self.use_sim:
            self.sim_comm.update(data)
        else:
            self.serial_comm.update(data)

    def _start(self):
        if self.use_sim:
            self.sim_comm.start()
        else:
            self.serial_comm.start()
