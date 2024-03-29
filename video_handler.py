from cv2 import imencode, imread
from time import sleep
import numpy as np
from time import perf_counter

SLEEP_BETWEEN_FRAMES_TIME = 0.3


class VideoHandler:
    def __init__(self, cam_hdl, cnt_hdl, enabled, offline_image_path=None):
        self.offline_image = self.load_offline_image(offline_image_path)
        self.enabled = enabled
        self.cam_hdl = cam_hdl
        self.cnt_hdl = cnt_hdl

    def load_offline_image(self, offline_image_path=None):
        if offline_image_path is None:
            im = np.zeros([1, 1], dtype=np.uint8)
        else:
            im = imread(offline_image_path).mean(2)
        _, buffer = imencode('.jpg', im)
        return buffer.tobytes()

    def is_available(self, cam_name):
        if self.cam_hdl.exists(cam_name) and len(self.cam_hdl.get_cam(cam_name).frame_list) > 0:
            return True
        return False

    def gen_frames(self, cam_name):
        #while True:
        if not self.cam_hdl.exists(cam_name):
            return (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + self.offline_image + b'\r\n')
        else:
            cam = self.cam_hdl.get_cam(cam_name)
            if not cam.is_requested_capturing:
                self.cnt_hdl.capture_cam(cam_name)
            cam.last_view_request = perf_counter()
            #print('ba {}'.format(cam.last_view_request))
            if perf_counter() - cam.last_buff_time > 30:
                return (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + self.offline_image + b'\r\n')
                #continue


            frame_list = self.cam_hdl.get_cam(cam_name).frame_list
            if len(frame_list) > 0 and self.enabled[0]:
                ret, buffer = imencode('.jpg', frame_list[0])
                frame = buffer.tobytes()
                return (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                return (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + self.offline_image + b'\r\n')
            #sleep(SLEEP_BETWEEN_FRAMES_TIME)
