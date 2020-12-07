# coding=utf-8
import logging
from threading import Semaphore

import serial

'''
Works with SEG-021(H) Programmable Temperature Chamber from www.espec.com
'''


class SEG_021H:
    def __init__(self, serial_port: str, baudrate=9600, eof='\r\n', ack=True):
        logging.basicConfig(level=logging.INFO)
        self.port = serial.Serial(serial_port, baudrate=baudrate, parity=serial.PARITY_NONE,
                                  timeout=2)
        self.eof = eof
        self.ack = True
        self.sem = Semaphore()

    @staticmethod
    def _convert_string(s):
        return '' if s is None else str(s)

    @staticmethod
    def _my_decimal(num):
        return "{:.1f}".format(float(num))

    def serial_write_read(self, cmd: str, arg1=None, arg2=None, arg3=None, arg4=None):
        self.sem.acquire()
        build_cmd = cmd + self._convert_string(arg1) + self._convert_string(arg2) + self._convert_string(
            arg3) + self._convert_string(arg4) + self.eof
        self.port.write(build_cmd.encode())
        logging.debug('Sending Command:{}'.format(build_cmd))
        res = self.port.read_until(self.eof).decode().strip()
        logging.debug('Command:{},Read return:{}'.format(build_cmd, res))
        self.sem.release()
        return res

    def close(self):
        self.port.close()

    """ Get Command"""

    def get_rom_version(self):
        res = self.serial_write_read('!?V')
        return res

    def get_temp_pv(self):
        res = self.serial_write_read('!?T')
        return self._my_decimal(res)

    def get_temp_high_limit(self):
        res = self.serial_write_read('!?T1')
        return self._my_decimal(res)

    def get_temp_all(self):
        res = self.serial_write_read('!?T2')
        temp_list = [self._my_decimal(x) for x in res.split(',')]
        temp_result = {'temp_pv': temp_list[0], 'temp_sv': temp_list[1], 'temp_limit': temp_list[2]}
        return temp_result

    def get_running_mode(self):
        res = self.serial_write_read('!?M')
        if res.startswith('C'):
            return {'mode': 'CONST'}
        if res.startswith('P'):
            return {'mode': 'PROGRAM', 'pgm_id': res[1:]}
        if res.startswith('A'):
            return {'mode': 'ALARM', 'alarm_id': res[1:]}

    def get_heat_output_value(self):
        """加热输出值是什么鬼？"""
        res = self.serial_write_read('!?%')
        return self._my_decimal(res)

    def get_running_status(self):
        res = self.serial_write_read('!?R')
        if res.startswith('C'):
            return {'mode': 'CONST', 'temp_pv': self._my_decimal(res.split(' ')[1])}
        if res.startswith('P'):
            pgm, _temp = res.split(' ')
            pgm_id = pgm[1:]
            temp_pv, remain_time = _temp.split(',')
            remain_hours, remain_mins = remain_time.split('.')
            return {'mode': 'PGM', 'pgm_id': pgm_id, 'temp_pv': temp_pv, 'remain_hours': remain_hours,
                    'remain_mins': remain_mins}

    def get_pgm_step_setting(self, pgm_id: str, step: str):
        res = self.serial_write_read('!?P', arg1=pgm_id, arg2=step)
        if res.startswith('R'):
            step_setting = res.split(' ')[1]
            temp_sv, remain_time = step_setting.split(',')
            remain_hours, remain_mins = remain_time.split('.')
            return {'status': 'RUNNING', 'temp_sv': temp_sv, 'remain_hours': remain_hours, 'remain_mins': remain_mins}
        if res.startswith('S'):
            _, remain_time = res.split(' ')[1]
            remain_hours, remain_mins = remain_time.split('.')
            return {'status': 'STOPPED', 'remain_hours': remain_hours, 'remain_mins': remain_mins}

    def get_pgm_end_method(self, pgm_id: str):
        res = self.serial_write_read('!?P', arg1=pgm_id, arg2=3)
        if res.startswith('P'):
            next_pgm_id = res[1:]
            return {'method': 'SWITCH', 'next_pgm_id': next_pgm_id}
        if res.startswith('C'):
            return {'method': 'CONST'}
        if res.startswith('S'):
            return {'method': 'STOP'}

    def get_const_sv(self):
        res = self.serial_write_read('!?C')
        return self._my_decimal(res)

    """Set Command"""

    @staticmethod
    def _part_set_command_response(res):
        if res.startswith('OK'):
            cmd = res.split(':')[1]
            return {'result': 'SUCCESS', 'cmd': cmd}
        if res.startswith('NA'):
            error = res.split(':')[1]
            return {'result': "FAILED", 'error': error}

    def set_const_value(self, temp):
        res = self.serial_write_read('!SC', arg1=self._my_decimal(temp))
        return self._part_set_command_response(res)

    def set_pgm_step_value(self, pgm_id: int, step: int, run: bool, hours: int, mins: int, temp_sv: float = 25.0):
        temp_sv = self._my_decimal(temp_sv)
        if run:
            res = self.serial_write_read(cmd='!SP', arg1=pgm_id, arg2=step, arg3=' R{}'.format(temp_sv),
                                         arg4=',{}.{}'.format(hours, mins))
        else:
            res = self.serial_write_read(cmd='!SP', arg1=pgm_id, arg2=step, arg3=' S{}.{}'.format(hours, mins))
        return self._part_set_command_response(res)

    def set_pgm_end_method(self, pgm_id: int, method: str, next_pgm_id: int = None):
        if method == "STOP":
            res = self.serial_write_read(cmd='!SP', arg1=pgm_id, arg2='3S')
        elif method == 'CONST':
            res = self.serial_write_read(cmd='!SP', arg1=pgm_id, arg2='3C')
        elif method == 'SWITCH':
            res = self.serial_write_read(cmd='!SP', arg1=pgm_id, arg2='3P{}'.format(next_pgm_id))
        return self._part_set_command_response(res)

    """Running Command"""

    def run_const(self):
        res = self.serial_write_read('!RC')
        return self._part_set_command_response(res)

    def stop(self):
        res = self.serial_write_read('!RS')
        return self._part_set_command_response(res)

    def run_pgm(self, pgm_id: int):
        res = self.serial_write_read('!RP', arg1=str(pgm_id))
        return self._part_set_command_response(res)
