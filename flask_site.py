from main_handler import MainHandler

from flask import Flask, render_template, make_response, Response, request
from json import dumps


NETWORK_MODE = True
app = Flask(__name__)


def parse_reg_set(ss):
    try:
        var_val = []
        for cur in ss.split(','):
            cur_var_val = cur.split('=')
            if len(cur_var_val) == 2 and (not any(x is None for x in cur_var_val)):
                if cur_var_val[1][0].lower() == 'b':
                    cur_var_val[1] = int(cur_var_val[1][1:], 2)
                else:
                    cur_var_val[1] = int(cur_var_val[1])
                cur_var_val[0] = cur_var_val[0].upper()
                var_val.append(cur_var_val)
        return var_val
    except:
        return None


@app.route('/video_feed')
def video_feed():
    cookie = request.cookies.get('token')
    cam_name = request.args['cam']
    if cookie in M.usr_hdl.users and cam_name in M.cam_hdl.cams:
        return Response(M.vid_hdl.gen_frames(cam_name), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return '404'


@app.route('/debug', methods=['GET', 'POST'])
def debug_page():
    new_token = validate_connection(request)
    if new_token is not None:
        cam_name = request.form.get('cam_name')

        if cam_name is not None and M.cam_hdl.exists(cam_name):
            cam = M.cam_hdl.get_cam(cam_name)
            if 'save_but' in request.form:
                cam.save_config()

            if 'rot_left' in request.form:
                cam.rot_deg = (cam.rot_deg - 90) % 360
            elif 'rot_right' in request.form:
                cam.rot_deg = (cam.rot_deg + 90) % 360

            if 'regset_form' in request.form:
                regset = request.form.get('regset')
                if regset == 'default':
                    cam.waiting_commands.append((M.cnt_hdl.send_command, (cam_name, b'DEF_REG')))
                else:
                    regset = parse_reg_set(regset)
                    if len(regset) > 0 and regset is not None:
                        cam.waiting_commands.append((M.cnt_hdl.debug_set_regs, (regset, cam_name)))
            elif 'camconfig_form' in request.form:
                fpc = request.form.get('frames_per_capture')
                if fpc is not None and len(fpc) > 0:
                    if cam.frames_per_capture != int(fpc):
                        cam.waiting_commands.append((M.cnt_hdl.debug_set_vars, (('check_connection_frames', fpc), cam_name)))
                cam.set_configs(request.form)

        resp = make_response(render_template(r"debug.html",
                                             presets=dumps(M.cnt_hdl.presets),
                                             cam_configs=dumps(M.cam_hdl.basic_configs())))
        resp.set_cookie('token', new_token)
        return resp
    else:
        return "404"

@app.route('/<string:cam_name>')
def reroute_cam(cam_name):
    if cam_name in M.cam_hdl.cams:
        return index(cam_name)
    else:
        return '404'

@app.route('/')
def index(cam_name='CAM1'):
    """Video streaming home page."""

    new_token = validate_connection(request)
    if new_token is not None:
        existing_cams = list(M.cam_hdl.cams.keys())
        cam = M.cam_hdl.get_cam(cam_name)
        resp = make_response(render_template(r"template.html", existing_cams=dumps(existing_cams),
                                             current_cam=dumps(cam_name),
                                             video_feed_url='/video_feed?cam={}'.format(cam_name),
                                             voltage=cam.voltage,
                                             ontime=cam.last_buff_time - cam.first_buff_time))

        M.cnt_hdl.capture_cam(cam_name)

        resp.set_cookie('token', new_token)
        return resp
    else:
        return "404"

def validate_connection(request):
    token = None
    get_arg = request.args.get('token')
    cookie = request.cookies.get('token')
    if get_arg in M.usr_hdl.users:
        token = get_arg
    elif cookie in M.usr_hdl.users:
        token = cookie

    if token is not None:
        new_token = M.usr_hdl.retokenize(token)
        return new_token
    return None

if __name__ == '__main__':
    M = MainHandler()
    if NETWORK_MODE:
        app.run(debug=False, host='0.0.0.0', port=8088, threaded=True)
    else:
        app.run(debug=False, port=8088, threaded=True)
