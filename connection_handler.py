import socket
from threading import Thread
from time import sleep, clock, localtime
from re import findall
from log_handler import Logger
log = Logger.log

CONNECTION_OK_STR = b'AHOY'
TCP_CHECK_STR = b'ARRR'
REG_FILE_PATH = 'regs.txt'
TARGET_UDP_PORT = 8888
MY_UDP_PORT = 8888
MY_TCP_PORT = 8889
CAM_MAX_FRAME_DELAY_SEC = 2
CAM_MAX_WAIT_FOR_REQUEST_SEC = 5
CAMERA_SLEEP_TIME = '01:00:00'

class ConnectionHandler:
    def __init__(self, enabled, rut_hdl=None, cam_hdl=None, presets=None):
        self.cam_hdl = cam_hdl
        self.rut_hdl = rut_hdl

        self.is_ahoy = False
        self.debug_capture = False
        self.enabled = enabled
        self.presets = presets

        self.regs, self.op_regs = self._read_reg_file()

        self.tcp_sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sc.settimeout(5)
        self.tcp_sc.bind(("0.0.0.0", MY_TCP_PORT))
        self.tcp_sc.listen()
        self.udp_sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sc.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_sc.settimeout(1)
        self.udp_sc.bind(("0.0.0.0", MY_UDP_PORT))

        self.invoke_thr = Thread(target=self.invoke_connection)
        self.buff_thr = Thread(target=self.wait_for_udp_buffer)
        self.invoke_thr.start()
        self.buff_thr.start()
        if self.rut_hdl is not None:
            self.rut_client_thr = Thread(target=self.discover_router_clients)
            self.rut_client_thr.start()


    def debug_set_regs(self, adr_val, cam_name='CAM1'):
        if adr_val is None or not self.cam_hdl.exists(cam_name):
            return
        command = b'ADD_REG:'
        for adr, val in adr_val:
            adr = self.regs[adr]
            reg = chr(adr).encode()
            val = chr(val).encode()
            command += reg + val + b'&'
        command = command[:-1]
        return self.send_command(cam_name, command)

    def debug_set_vars(self, var_val, cam_name='CAM1'):
        if var_val is None or not self.cam_hdl.exists(cam_name):
            return
        command = b'SET_VAR:'
        for var, val in var_val:
            command += var.encode() + b'=' + val.encode() + b'&'
        command = command[:-1]
        return self.send_command(cam_name, command)

    def send_command(self, cam_name, command):
        try:
            cam = self.cam_hdl.get_cam(cam_name)

            cam.is_ahoy = False
            if cam.is_connected:
                cam.sc.send(command + CONNECTION_OK_STR)
            else:
                log('debug request {0} for {1} cam offline'.format(command, cam_name))
                return False, True
            sleep(5)
            if cam.is_ahoy:
                log('debug request {0} for {1} success'.format(command, cam_name))
                return True, False
            else:
                log('debug request {0} for {1} failed'.format(command, cam_name))
                return False, False
        except:
            log('debug request {0} for {1} except'.format(command, cam_name))
            return False, False


    @staticmethod
    def _read_reg_file(reg_path=REG_FILE_PATH):
        dd, bb = {}, {}
        with open(reg_path, 'r') as ff:
            ss = ff.read()
            for cur in ss.split('\n'):
                val, key = cur.split(' ')
                dd[key] = int(val, 16)
                bb[str(int(val, 16))] = key
        return dd, bb

    def discover_router_clients(self):
        while True:
            try:
                for ip, cam_name in self.rut_hdl.clients.items():
                    if len(findall('CAM\d+$', cam_name)) > 0:
                        if not self.cam_hdl.exists(cam_name):
                            self.cam_hdl.discover_cam(cam_name, ip=ip)
                        elif self.cam_hdl.get_cam(cam_name).ip != ip:
                            self.cam_hdl.discover_cam(cam_name, ip=ip)
            except:
                pass
            sleep(60)

    def capture_cam(self, cam_name):
        if self.cam_hdl.exists(cam_name) and not self.cam_hdl.get_cam(cam_name).is_capturing:
            self.cam_hdl.get_cam(cam_name).is_capturing = True
            log('camera {} set to capture'.format(cam_name))

    def uncapture_cam(self, cam_name):
        if self.cam_hdl.exists(cam_name) and self.cam_hdl.get_cam(cam_name).is_capturing:
            self.cam_hdl.get_cam(cam_name).is_capturing = False
            log('camera {} set to uncapture'.format(cam_name))

    def listen_for_active_cam(self):
        try:
            conn, ip = self.tcp_sc.accept()
            ip = ip[0]
            cur_cam = self.cam_hdl.get_cam(ip)

            if cur_cam is not None:
                if cur_cam.sc is not None:
                    cur_cam.sc.close()
                    cur_cam.sc = None
                cur_cam.sc = conn
                Thread(target=self.wait_for_tcp_buffer, args=(cur_cam,)).start()
                log('connect request : {}'.format(ip))

        except:
            pass

    def tcp_connect_to_cam(self, cam):
        try:
            if cam.ip is None:
                return
            self.udp_sc.sendto(b'CONNECTREQUEST' + CONNECTION_OK_STR, (cam.ip, TARGET_UDP_PORT))
            self.listen_for_active_cam()
        except:
            pass

    def invoke_connection(self):
        while True:
            while self.enabled[0]:
                for cam in self.cam_hdl.cams.values():
                    if clock() - cam.last_view_request > CAM_MAX_WAIT_FOR_REQUEST_SEC:
                        self.uncapture_cam(cam.name)
                    if not self.debug_capture and clock() - cam.last_buff_time > CAM_MAX_FRAME_DELAY_SEC:
                        if cam.is_sleep_enabled:
                            cur_time = localtime()
                            cur_time = '{0:02}:{1:02}:{2:02}'.format(cur_time.tm_hour, cur_time.tm_min, cur_time.tm_sec)
                            if is_between_times(cam.sleep_from, cam.sleep_to, cur_time):
                                if not cam.is_connected:
                                    self.tcp_connect_to_cam(cam)
                                    continue
                                if self.send_command(cam.name, ('SLEEP:{}'.format(cam.sleep_sess_sec)).encode()):

                                    cam.next_up = add_time(cur_time, cam.sleep_sess)
                                    cam.sc.close()

                        if len(cam.waiting_commands) > 0:
                            if not cam.is_connected:
                                self.tcp_connect_to_cam(cam)
                                continue
                            cur_command = cam.waiting_commands[0]
                            is_success, is_disconnected = cur_command[0](*cur_command[1])
                            if is_success:
                                cam.waiting_commands.pop(0)
                            elif is_disconnected:
                                cam.waiting_commands.pop(0)

                        elif cam.is_capturing:
                            if not cam.is_connected:
                                self.tcp_connect_to_cam(cam)
                                continue
                            self.send_command(cam.name, b'CAPTURE')
                        elif cam.is_nap_enabled:
                            if not cam.is_connected:
                                self.tcp_connect_to_cam(cam)
                                continue
                            if self.send_command(cam.name, ('SLEEP:{}'.format(cam.nap_for_sec)).encode()):
                                cam.next_up = add_time(cur_time, cam.nap_for)
                                cam.sc.close()
                sleep(0.5)
            sleep(30)

    def wait_for_tcp_buffer(self, cam):
        cam_sc = cam.sc
        while cam_sc is not None and self.enabled[0]:
            try:
                buff, temp = cam_sc.recvfrom(2048)
                #if len(buff) > 0:
                #    print(buff)
                if buff.startswith(b'ECHO:'):   # for testing
                    log(buff)
                if buff.startswith(b'DEBUG:'):  # for debug mode
                    log(buff)
                if buff.startswith(b'STATS:'):
                    cam.voltage = 5 * int(buff[6:]) / 1023

                    log('power from {0} : {1}'.format(cam.name, cam.voltage))
                if buff.startswith(TCP_CHECK_STR):
                    cam_sc.send(TCP_CHECK_STR)

                if CONNECTION_OK_STR in buff:
                    cam.is_ahoy = True
            except:
                pass

    def wait_for_udp_buffer(self):
        udp_sc = self.udp_sc
        while True:
            while self.enabled[0]:
                try:    # for some reason, when esp8266 sends buffer it sends it in 2 seperate packets, and some time they mix up
                    rec_buff, rec_addr = udp_sc.recvfrom(2048)
                    #print('UDP: {0}'.format(rec_buff))
                    if rec_buff.startswith(b'DISCOVER:'):
                        self.cam_hdl.discover_cam(rec_buff[9:].decode(), rec_addr[0])
                        sleep(0.1)
                        self.udp_sc.sendto(CONNECTION_OK_STR + b'\n', (rec_addr[0], TARGET_UDP_PORT))
                        log('discovery request : {}'.format(rec_addr))
                    #elif rec_buff.startswith(b'CONNECT'):
                    #    self.listen_for_active_cam()
                    #    log('connect request : {}'.format(rec_addr))
                    elif rec_buff.startswith(b'ECHO:'):
                        log('echo from {0} : {1}'.format(rec_addr, rec_buff))
                    elif self.cam_hdl.exists(rec_addr[0]):
                        cur_cam = self.cam_hdl.get_cam(rec_addr[0])
                        cur_time = clock()
                        if cur_time - cur_cam.last_buff_time > 30 or cur_cam.last_buff_time == -1:
                            cur_cam.first_buff_time = cur_time
                        cur_cam.last_buff_time = cur_time
                        cur_cam.buff.append(rec_buff)
                except:
                    pass
            sleep(30)


def is_between_times(low, high, cur):
    low = [int(x) for x in low.split(':')]
    high = [int(x) for x in high.split(':')]
    cur = [int(x) for x in cur.split(':')]

    if high > low:
        return cur > low and cur < high
    else:
        return cur > low or cur < high


def add_time(t, a):
    t = [int(x) for x in t.split(':')]
    a = [int(x) for x in a.split(':')]
    t[2] = t[2] + a[2]
    if t[2] > 59:
        t[2] -= 60
        t[1] += 1
    t[1] = t[1] + a[1]
    if t[1] > 59:
        t[2] -= 60
        t[0] += 1
    t[0] = t[0] + a[0]
    if t[0] > 23:
        t[0] -= 24
    return '{0:02}:{1:02}:{2:02}'.format(*t)