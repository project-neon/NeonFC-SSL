import serial
import threading
import time
import logging

class RobotFeedback(threading.Thread):
    def __init__(self, port_name): # port_name (COM4, COM3)
        super(RobotFeedback, self).__init__()

        self.port_id = port_name
        self.baud_rate = 9600
        self.serial_port = serial.Serial(self.port_id, self.baud_rate, dsrdtr=None)
        self.serial_port.setRTS(False)
        self.serial_port.setDTR(False)

        self.running = False
      #  self.daemon = True

        #self.logger = logging.getLogger()

        time.sleep(0.5)

    def run(self):
        self.running = True

        self.clear_buffers()

        try:
            while self.running:
                if not self.serial_port.is_open:
                    self.serial_port.open()
                
                try:
                    line = self.serial_port.readline() 
                    if line != None:
                        data_in_line = str(line).replace("\\r", "").replace("\\n", "").replace("'", "").replace("b", "")
                        if not self.error_check(data_in_line): 
                            data = self.parse_feedback_data(data_in_line) 
                            #data = [{id:, rssi:, battery: },{id:, rssi:, battery: },{id:, rssi:, battery: }]
                except serial.SerialException as e:
                   # self.logger.info(f"Error on serial port: {e}")
                    break
        finally:
            self.close_port()
            #self.logger.info("Closed feedback serial port")

    def stop(self):
        self.running = False
        self.close_port()

    def close_port(self):
        self.clear_buffers()
        if self.serial_port.is_open:
            self.serial_port.close()

    def clear_buffers(self):
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()

    def error_check(self, serial_line):
        return serial_line.count('>') < 3

    def parse_feedback_data(self, serial_line):
        data_per_id = self.split_serial_per_id(serial_line)
        if len(data_per_id) > 1:
            data_list = self.convert_data_to_dict(data_per_id)
            print(data_list)
            return data_list

    def split_serial_per_id(self, serial_line):
        data_per_id = [i[1:] for i in serial_line.split('>')[0:6]]
        return data_per_id

    def convert_data_to_dict(self, data_as_list):
        dict_list = []
        for data in data_as_list:
            data_split = data.split(',')

            if len(data_split) != 3: 
                return 'error'
            
            robot_dict = {'id': data_split[0], 
                          'rssi': data_split[1],
                            'battery': data_split[2]}
            dict_list.append(robot_dict)
        return dict_list