from main_handler import MainHandler

from time import localtime
from flask import Flask, render_template, make_response, Response, request


NETWORK_MODE = True
app = Flask(__name__)

@app.route('/video_feed')
def video_feed():
    cookie = request.cookies.get('token')
    if cookie in M.usr_hdl.users:
        cur_usr = M.usr_hdl.users[cookie]
        cur_usr['last_seen'] = localtime()
        return Response(M.vid_hdl.gen_frames(cur_usr['cam']), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return '404'


@app.route('/')
def index():
    """Video streaming home page."""
    token = None
    resp = make_response(render_template(r"template.html"))
    get_arg = request.args.get('token')
    cookie = request.cookies.get('token')
    if get_arg in M.usr_hdl.users:
        token = get_arg
    elif cookie in M.usr_hdl.users:
        token = cookie

    if token is not None:
        user = M.usr_hdl.users[token]
        new_token = M.usr_hdl.tokenize_user(user)
        M.cnt_hdl.connect_cam(user['cam'])
        resp.set_cookie('token', new_token)
        return resp
    else:
        return "404"


if __name__ == '__main__':
    M = MainHandler()
    if NETWORK_MODE:
        app.run(debug=False, host='0.0.0.0', port=8088, threaded=True)
    else:
        app.run(debug=False, port=8088, threaded=True)
