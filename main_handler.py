from router_handler import RouterHandler
from frame_builder import FrameBuilder
from connection_handler import ConnectionHandler
from user_handler import UserHandler
from email_handler import EmailHandler
from video_handler import VideoHandler
from camera_handler import CameraHandler
from pyngrok import ngrok

from threading import Thread
from time import sleep
from json import load

with open('configs/settings.json', 'r') as ff:
    dd = load(ff)['main_handler']
    USERS = dd['USERS']

IS_CHECK_ENABLE = True
ENABLE_CHECK_TIME_SEC = 20
EXISTING_CAMS = ['CAM1']
PRESETS = [{'name': 'lines', 'val': {'SCALING_XSC': int('10000000', 2), 'SCALING_YSC': int('10000000', 2)}},
           {'name': 'nightmode', 'val': {'COM11': int('10000000', 2)}}]
OFFLINE_IMAGE_PATH = r'Q.png'

class MainHandler:
    def __init__(self):
        self.enabled = [True]
        self.buff = {}
        self.frame_list = {}
        self.cam_hdl = CameraHandler(EXISTING_CAMS)
        self.active_cams = []
        self.ng_site = ngrok.connect(8088)
        #self.out_site = ['http://localhost:8088/?token=']
        self.out_site = [self.ng_site.public_url + '/?token=']
        self.users = {}

        #self.rut_hdl = RouterHandler()
        self.rut_hdl = None
        self.frm_bld = FrameBuilder(self.cam_hdl)
        self.cnt_hdl = ConnectionHandler(self.enabled, self.rut_hdl, self.cam_hdl, PRESETS)
        self.usr_hdl = UserHandler(USERS, self.users)
        self.mil_hdl = EmailHandler(self.users, self.out_site, self.usr_hdl.tokenize_all_users)
        self.vid_hdl = VideoHandler(self.cam_hdl, self.cnt_hdl, self.enabled, OFFLINE_IMAGE_PATH)

        for token, user in self.users.items():
            print('{}:   {}{}'.format(user['name'], self.out_site[0], token))

        enb_thr = Thread(target=self.is_enable)
        enb_thr.start()

    def is_enable(self):
        while IS_CHECK_ENABLE:
            if self.rut_hdl is not None and self.rut_hdl.is_client([x['name'] for x in USERS]):
                self.enabled[0] = False
            else:
                self.enabled[0] = True
            sleep(ENABLE_CHECK_TIME_SEC)
