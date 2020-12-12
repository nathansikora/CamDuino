from threading import Thread
import numpy as np
from time import sleep
from re import split

IM_WIDTH = 200
MINI_IM_WIDTH = int(IM_WIDTH/2)
IM_HEIGHT = 240
MAX_FRAMES_PER_CAM_BUFFER = 5


class FrameBuilder:
    def __init__(self, buff, frame_list):
        self.buff = buff
        self.frame_list = frame_list
        self.cur_frame = {}
        self.last_row = 0
        self.frame_temp = np.zeros([IM_HEIGHT, IM_WIDTH], dtype=np.uint8)
        self.parse_thr = Thread(target=self.parse_buff)
        self.parse_thr.start()

    def add_frame(self, frame, cam):
        if cam not in self.frame_list:
            self.frame_list[cam] = []
        self.frame_list[cam].append(frame)
        if len(self.frame_list[cam]) > MAX_FRAMES_PER_CAM_BUFFER:
            self.frame_list[cam].pop(0)

    def parse_buff(self):
        while True:
            while len(self.buff) == 0:
                sleep(0.05)
            cam, buff = self.buff.pop(0)
            if cam not in self.cur_frame:
                self.cur_frame[cam] = self.frame_temp.copy()
            try:
                frame = self.cur_frame[cam]
                _, line_num, buff_def = split(b'^XXX+(\d{3})', buff)
                line_num = int(line_num)
                prev_k = 0
                if line_num < self.last_row:
                    self.add_frame(frame, cam)
                for cur_k in range(MINI_IM_WIDTH, len(buff_def) + 1, MINI_IM_WIDTH):
                    tbuff = np.array(list(buff_def[prev_k:cur_k]), dtype=np.uint8)
                    tbuff = np.repeat(tbuff, 2)
                    tbuff = tbuff.reshape(MINI_IM_WIDTH, 2).transpose()

                    tbuff[0] >>= 4
                    tbuff[0] <<= 4
                    tbuff[1] <<= 4
                    tbuff = tbuff.transpose().reshape(1, IM_WIDTH)
                    frame[line_num % IM_HEIGHT, :] = tbuff
                    line_num += 1
                    prev_k = cur_k
                self.last_row = line_num - 1
            except:
                pass