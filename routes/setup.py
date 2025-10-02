from flask import Blueprint, redirect, request, make_response, jsonify
from libs.preprocessor import render_template_string
from libs.config import load_reloading_config, read_config
from libs.metrics import Metrics

from libs.auth import Auth

cfg = load_reloading_config('pyromanic.yaml')
metrics = Metrics()
auth = Auth()

setup = Blueprint('setup', __name__, template_folder='../www/templates', url_prefix=read_config(cfg(), 'app.base_path', str))

@setup.route("/setup", methods=["GET"])
@metrics.measure
def setup_page():
    if auth.count_users():
        base = read_config(cfg(), 'app.base_path', str)
        base += "" if base.endswith("/") else "/"
        return redirect(base + "?c=101")
    with open("./www/templates/setup.html", 'r') as f:
        return render_template_string(f.read())

@setup.route("/setup", methods=["POST"])
@metrics.measure
def setup_account():
    if auth.count_users():
        base = read_config(cfg(), 'app.base_path', str)
        base += "" if base.endswith("/") else "/"
        return redirect(base + "?c=101")
    if "username" not in request.form or "password" not in request.form:
        return jsonify({"error": "bad request"}), 400

    auth.create_user(request.form["username"], request.form["password"], "operator")
    resp = make_response(redirect("/"))
    resp.set_cookie(
        'PYRO-AuthKey',
        auth.register_cookie(request.form["username"]),
        secure=True,
        httponly=True,
        samesite='Strict'
    )
    return resp