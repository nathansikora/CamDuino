from log_handler import Logger
from os.path import exists
from json import dump, load
from time import asctime
log = Logger.log

'''BASE_CONFIG_ATTRS = ['name', 'is_connected', 'is_capturing',
         'is_watchable', 'voltage', 'is_sleep_enabled', 'sleep_from', 'sleep_to',
         'sleep_sess', 'is_nap_enabled', 'nap_for', 'frames_per_capture', 'rot_deg']'''

BASE_CONFIG_ATTRS = ['name', 'is_watchable', 'is_sleep_enabled',
                     'sleep_from', 'sleep_to', 'sleep_sess', 'is_nap_enabled',
                     'nap_for', 'frames_per_capture', 'rot_deg']

class CameraHandler:
    def __init__(self, existing_cams=[]):
        self._ip_2_cam = {}
        self.cams_by_name = {}
        for cam_name in existing_cams:
            self.discover_cam(cam_name)

    def __iter__(self):
        return (list(self.cams_by_name.keys()) + list(self._ip_2_cam.keys())).__iter__()

    @property
    def cams(self):
        return self.cams_by_name

    def discover_cam(self, name, ip=None, sc=None):
        if name not in self.cams:
            self.cams[name] = Camera(name, ip, sc)
        if ip is not None:
            self._ip_2_cam[ip] = name
            self.cams[name].ip = ip
            log('discovered {0} at {1}'.format(name, ip))

    def exists(self, name_or_ip):
        if name_or_ip in self._ip_2_cam or name_or_ip in self.cams_by_name:
            return True
        return False

    def get_cam(self, name_or_ip):
        if name_or_ip in self._ip_2_cam:
            return self.cams_by_name[self._ip_2_cam[name_or_ip]]
        elif name_or_ip in self.cams_by_name:
            return self.cams_by_name[name_or_ip]
        else:
            return None

    def basic_configs(self):
        return {cam.name: cam.base_config() for cam in self.cams.values()}


class Camera:
    def __init__(self, name, ip=None, sc=None):
        self.name = name
        self.ip = ip
        self.sc = sc
        self.is_ahoy = False
        #self.is_connected = False
        #self.is_discovered
        self.is_capturing = False
        self.is_watchable = True
        self.voltage = 0
        self.is_sleep_enabled = True
        self.sleep_from = '18:00:00'
        self.sleep_to = '06:00:00'
        self.sleep_sess = '01:00:00'
        self.is_nap_enabled = True
        self.nap_for = '00:00:30'
        self.frames_per_capture = 60

        self.next_up = ''
        self.waiting_commands = []
        self.last_buff_time = -1
        self.first_buff_time = 0
        self.last_view_request = 0

        self.rot_deg = 0
        self.buff = []
        self.big_buff = b''
        self.match = None
        self.frame_list = []
        self.last_row = 0
        self.cur_frame = None

        config_name = 'configs/{}.json'.format(self.name)
        if exists(config_name):
            with open(config_name, 'r') as ff:
                new_config = load(ff)
                for key, val in new_config.items():
                    self.__setattr__(key, val)

    @property
    def is_connected(self):
        if self.sc is not None:
            try:
                self.sc.send(b'')
                return True
            except:
                return False
        return False

    @property
    def is_discovered(self):
        return self.ip is not None

    @property
    def nap_for_sec(self):
        if len(self.nap_for) > 0:
            return time_2_sec(self.nap_for)
        return 0

    @property
    def sleep_for_sec(self):
        if len(self.sleep_for) > 0:
            return time_2_sec(self.sleep_for)
        return 0

    @property
    def sleep_sess_sec(self):
        if len(self.sleep_sess) > 0:
            return time_2_sec(self.sleep_sess)
        return 0

    def base_config(self):
        return {att: self.__getattribute__(att) for att in BASE_CONFIG_ATTRS}

    def set_configs(self, cnfgs):
        self.is_watchable = True if cnfgs.get('is_watchable') == 'true' else False
        self.is_sleep_enabled = True if cnfgs.get('is_sleep_enabled') == 'true' else False
        self.is_nap_enabled = True if cnfgs.get('is_nap_enabled') == 'true' else False
        self.sleep_from = cnfgs.get('sleep_from')
        self.sleep_to = cnfgs.get('sleep_to')
        self.sleep_sess = cnfgs.get('sleep_sess')
        self.nap_for = cnfgs.get('nap_for')
        self.frames_per_capture = int(cnfgs.get('frames_per_capture')) if len(cnfgs.get('frames_per_capture')) > 0 else 60

    def save_config(self):
        with open('configs/{}.json'.format(self.name), 'w') as ff:
            dump(self.base_config(), ff)

def time_2_sec(t):
    t = t.split(':')
    return int(t[0]) * 3600 + int(t[1]) * 60 + int(t[2])

