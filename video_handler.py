from cv2 import imencode
from time import sleep

SLEEP_BETWEEN_FRAMES_TIME = 0.3


class VideoHandler:
    def __init__(self, frame_list, enabled):
        self.enabled = enabled
        self.frame_list = frame_list

    def gen_frames(self, cam):
        frame_list = self.frame_list
        while self.enabled[0]:
            if cam in frame_list and len(frame_list[cam]) > 0:
                ret, buffer = imencode('.jpg', frame_list[cam].pop())
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            sleep(SLEEP_BETWEEN_FRAMES_TIME)
        return
