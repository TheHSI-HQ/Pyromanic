from flask import Blueprint, make_response, redirect, request, jsonify
from libs.auth import Auth
from libs.config import load_reloading_config, read_config
from libs.metrics import Metrics
from datetime import datetime, timezone, timedelta

from urllib.parse import unquote_plus, quote_plus

cfg = load_reloading_config('pyromanic.yaml')
metrics = Metrics()
authentication = Auth()


auth = Blueprint('auth', __name__, template_folder='../www/templates', url_prefix=read_config(cfg(), 'app.base_path', str))

class RateLimit:
    def __init__(self):
        self.rate_limits: dict[str, tuple[datetime, int]] = {}
    def get(self):
        return self.rate_limits
    def set(self, rate_limits: dict[str, tuple[datetime, int]]):
        self.rate_limits = rate_limits

rate_limit = RateLimit()

@auth.route("/letmein", methods=["POST"])
@metrics.measure
def letmein():
    _rate_limits = rate_limit.get()
    now = datetime.now(timezone.utc)

    base = read_config(cfg(), 'app.base_path', str)
    base += "" if base.endswith("/") else "/"

    # Clean up expired rate limits
    for k, v in _rate_limits.items():
        print(f"{k} => expires: {v[0]}, now: {now}, keep: {v[0] >= now}")

    _rate_limits = {k: v for k, v in _rate_limits.items() if v[0] >= now}

    ip = request.remote_addr
    max_attempts = read_config(cfg(), "auth.rate_limit.attempts", int)
    remember_secs = read_config(cfg(), "auth.rate_limit.remember", int)

    def redirect_with_code(code: int, extra:str=""):
        url = base + f"?c={code}"
        if "url" in request.args:
            url += f"&url={quote_plus(request.args['url'])}"
        if extra:
            url += f"&{extra}"
        return redirect(url)

    if ip in _rate_limits:
        expires, attempts = _rate_limits[ip]
        if expires >= now and attempts > max_attempts:
            wait_time = (expires - now).seconds
            return redirect_with_code(102, f"i={wait_time}")

    if "username" not in request.form or "password" not in request.form:
        return jsonify({"error": "bad request"}), 400

    if authentication.verify_user(request.form["username"], request.form["password"]):
        resp = make_response(redirect(unquote_plus(request.args["url"])) if "url" in request.args else redirect("/"))
        resp.set_cookie('PYRO-AuthKey', authentication.register_cookie(request.form["username"]))
        return resp

    if ip:
        if ip in _rate_limits:
            expires, attempts = _rate_limits[ip]
            _rate_limits[ip] = (expires, attempts + 1)
        else:
            _rate_limits[ip] = (
                now + timedelta(seconds=remember_secs),
                1
            )

    rate_limit.set(_rate_limits)

    return redirect_with_code(100)