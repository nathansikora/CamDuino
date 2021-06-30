from threading import Thread
import numpy as np
from time import sleep
from re import split, search, DOTALL

IM_WIDTH = 300
MINI_IM_WIDTH = int(IM_WIDTH/2)
IM_HEIGHT = 240
MAX_FRAMES_PER_CAM_BUFFER = 1


class FrameBuilder:
    def __init__(self, cam_hdl):
        self.cam_hdl = cam_hdl
        self.cur_frame = {}
        self.last_row = {}
        self.hue_dict = self.create_hue_dict()
        self.frame_temp = np.zeros([IM_HEIGHT, IM_WIDTH], dtype=np.uint8)
        self.parse_thr = Thread(target=self.parse_buff)
        self.parse_thr.start()
        self.r1 = 0
        self.r2 = 0

    @staticmethod
    def create_hue_dict():
        dd = {}
        for k in range(16):
            x = [x for x in '{0:04b}'.format(k)]
            y = ''.join([x[3], x[2], x[0], x[1]])
            dd[k] = int(y, 2)
        return dd

    def parse_buff(self):
        hue_dict = self.hue_dict
        while True:
            any_active = False
            try:
                for cam in self.cam_hdl.cams.values():

                    if len(cam.buff) < 1:
                        continue
                    any_active = True
                    if cam.match is None:
                        cam.big_buff += cam.buff.pop(0)    # TODO: remove this and see how fast it runs
                    cam.match = search(b'XXXXXXX.+?XXXXXXX', cam.big_buff, DOTALL)
                    if cam.match is None:
                        continue
                    cam.big_buff = cam.big_buff[cam.match.end()-7:]
                    buff = cam.match.group()[:-7]
                    if cam.cur_frame is None:
                        cam.cur_frame = self.frame_temp.copy()
                    try:
                        frame = cam.cur_frame
                        _, line_num, buff_def = split(b'^XXX+(\d{3})', buff)
                        line_num = int(line_num)
                        prev_k = 0
                        if line_num < cam.last_row:
                            new_frame = frame.copy()

                            new_frame = np.roll(new_frame, -14, axis=0)
                            new_frame = np.roll(new_frame, -4, axis=1)
                            cam.frame_list.append(np.rot90(new_frame, int(cam.rot_deg/90)))
                            if len(cam.frame_list) > MAX_FRAMES_PER_CAM_BUFFER:
                                cam.frame_list.pop(0)
                        for cur_k in range(MINI_IM_WIDTH, len(buff_def) + 1, MINI_IM_WIDTH):
                            tbuff = np.array(list(buff_def[prev_k:cur_k]), dtype=np.uint8)
                            tbuff = np.repeat(tbuff, 2)
                            tbuff = tbuff.reshape(MINI_IM_WIDTH, 2).transpose()

                            tbuff[0] >>= 4
                            tbuff[0] = [hue_dict[x] for x in tbuff[0]]
                            tbuff[0] <<= 4
                            tbuff[1] >>= 4
                            tbuff[1] = [hue_dict[x] for x in tbuff[1]]
                            tbuff[1] <<= 4

                            tbuff = tbuff.transpose().reshape(1, IM_WIDTH)
                            frame[line_num % IM_HEIGHT, :] = tbuff
                            line_num += 1
                            prev_k = cur_k
                        cam.last_row = line_num - 1
                    except:
                        pass
                    if not any_active:
                        sleep(0.05)
            except:
                pass