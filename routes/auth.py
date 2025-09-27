from flask import Blueprint, make_response, redirect, request, jsonify
from libs.auth import Auth
from libs.config import load_reloading_config, read_config
from libs.metrics import Metrics

from urllib.parse import unquote_plus, quote_plus

cfg = load_reloading_config('pyromanic.yaml')
metrics = Metrics()
authentication = Auth()

auth = Blueprint('auth', __name__, template_folder='../www/templates', url_prefix=read_config(cfg(), 'app.base_path', str))

@auth.route("/letmein", methods=["POST"])
@metrics.measure
def letmein():
    if "username" not in request.form or "password" not in request.form:
        return jsonify({"error": "bad request"}), 400
    if authentication.verify_user(request.form["username"], request.form["password"]):
        if "url" in request.args:
            resp =  make_response(redirect(unquote_plus(request.args["url"])))
        else:
            resp = make_response(redirect("/"))

        resp.set_cookie('PYRO-AuthKey', authentication.register_cookie(request.form["username"]))

        return resp
    base = read_config(cfg(), 'app.base_path', str)
    base += "" if base.endswith("/") else "/"
    if "url" in request.args:
        return redirect(base + "?url=" + quote_plus(request.args["url"]) + "&c=100")
    return redirect(base + "?c=100")