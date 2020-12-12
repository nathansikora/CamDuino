import socket
from threading import Thread
from time import sleep
from re import findall

CONNECTION_OK_STR = b'AHOY'
TARGET_PORT = 8888
MY_PORT = 8888


class ConnectionHandler:
    def __init__(self, enabled, buff, cam_stats, rut_hdl=None):
        self.enabled = enabled
        self.cam_ip = {}
        self.ip_cam = {}
        self.cam_stats = cam_stats
        self.active_cams = []
        self.rut_hdl = rut_hdl
        self.buff = buff
        self.sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sc.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sc.settimeout(1)
        self.sc.bind(("0.0.0.0", MY_PORT))

        self.invoke_thr = Thread(target=self.invoke_connection)
        self.buff_thr = Thread(target=self.wait_for_buffer)
        self.invoke_thr.start()
        self.buff_thr.start()
        if self.rut_hdl is not None:
            self.rut_client_thr = Thread(target=self.discover_router_clients)
            self.rut_client_thr.start()

    def discover_router_clients(self):
        while True:
            try:
                for ip, name in self.rut_hdl.clients.items():
                    if len(findall('CAM\d+$', name)) > 0:
                        if self.cam_ip[name] != ip:
                            self.discover_cam(name, ip)
            except:
                pass
            sleep(60)

    def discover_cam(self, cam, ip):
        self.cam_ip[cam] = ip
        self.ip_cam[ip] = cam
        self.cam_stats[cam] = None
        print('discovered {0} at {1}'.format(cam, ip))

    def connect_cam(self, cam):
        if cam not in self.active_cams:
            self.active_cams.append(cam)

    def disconnect_cam(self, cam):
        if cam in self.active_cams:
            self.active_cams.remove(cam)

    def invoke_connection(self):
        while True:
            while self.enabled[0]:
                for active_cam in self.active_cams:
                    if active_cam in self.cam_ip:
                        self.sc.sendto(b'CAPTURE\n', (self.cam_ip[active_cam], TARGET_PORT))
                    else:
                        self.sc.sendto(b'DISCOVER\n', ('255.255.255.255', TARGET_PORT))
                sleep(1)
            sleep(30)

    def wait_for_buffer(self):
        sc = self.sc
        while True:
            while self.enabled[0]:
                try:
                    tbuff, addr1 = sc.recvfrom(2048)
                    if tbuff[:9] == b'DISCOVER:':
                        self.discover_cam(tbuff[9:].decode(), addr1[0])
                        self.sc.sendto(CONNECTION_OK_STR + b'\n', (addr1[0], TARGET_PORT))
                    elif tbuff[:5] == b'TEST:':
                        print(tbuff)
                    elif addr1[0] not in self.cam_ip.values():
                        continue
                    elif tbuff[:6] == b'STATS:':
                        self.cam_stats[self.ip_cam[addr1[0]]] = 5 * int(tbuff[6:]) / 1023
                        print(self.cam_stats[self.ip_cam[addr1[0]]])
                    else:
                        ttbuff, addr2 = sc.recvfrom(2048)
                        if addr2[0] != addr1[0]:
                            continue
                        tbuff += ttbuff
                        if tbuff[0] == 88:
                            self.buff.append((self.ip_cam[addr1[0]], tbuff))
                except:
                    pass
            sleep(30)
