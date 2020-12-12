from router_handler import RouterHandler
from frame_builder import FrameBuilder
from connection_handler import ConnectionHandler
from user_handler import UserHandler
from email_handler import EmailHandler
from video_handler import VideoHandler

from threading import Thread
from time import sleep
from json import load

with open('settings.json', 'r') as ff:
    dd = load(ff)['main_handler']
    USERS = dd['USERS']

IS_CHECK_ENABLE = True
ENABLE_CHECK_TIME_SEC = 20

class MainHandler:
    def __init__(self):
        self.enabled = [True]
        self.buff = []
        self.frame_list = {}
        self.active_cams = []
        self.cam_stats = {}
        self.out_site = ['http://localhost:8088/?token=']
        self.users = {}

        self.rut_hdl = RouterHandler()
        self.frm_bld = FrameBuilder(self.buff, self.frame_list)
        self.cnt_hdl = ConnectionHandler(self.enabled, self.buff, self.cam_stats, self.rut_hdl)
        self.usr_hdl = UserHandler(USERS, self.users, self.cnt_hdl.disconnect_cam)
        self.mil_hdl = EmailHandler(self.users, self.out_site)
        self.vid_hdl = VideoHandler(self.frame_list, self.enabled)


        enb_thr = Thread(target=self.is_enable)
        enb_thr.start()

    def is_enable(self):
        while IS_CHECK_ENABLE:
            if self.rut_hdl.is_client([x['name'] for x in USERS]):
                self.enabled[0] = False
            else:
                self.enabled[0] = True
            sleep(ENABLE_CHECK_TIME_SEC)
