from flask import Blueprint, request, redirect
from urllib.parse import unquote_plus, urlparse
from libs.auth import Auth
from libs.preprocessor import render_template_string
from libs.config import load_reloading_config, read_config
from libs.metrics import Metrics


cfg = load_reloading_config('pyromanic.yaml')
metrics = Metrics()
auth = Auth()

landing = Blueprint('landing', __name__, template_folder='../www/templates', url_prefix=read_config(cfg(), 'app.base_path', str))

@landing.route("/")
@metrics.measure
def index():
    if not auth.count_users():
        base = read_config(cfg(), 'app.base_path', str)
        base += "" if base.endswith("/") else "/"
        return redirect(base + "setup")

    if auth.is_valid_cookie(request.cookies.get("PYRO-AuthKey", type=str)):
        if "url" in request.args:
            url = unquote_plus(request.args["url"]).replace('\\', '')
            parsed = urlparse(url)
            # Only redirect to relative URLs (no netloc, no scheme)
            if not parsed.netloc and not parsed.scheme:
                return redirect(url)
            return redirect("/")

    if "c" in request.args:
        code = request.args["c"]
        match code:
            case "100":
                message = "The Username or Password you entered were Incorrect!"
            case "101":
                message = "Setup has already been Completed!"
            case "102":
                if "i" in request.args:
                    message = "You are Timed Out for %s Seconds" % request.args["i"]
                else:
                    message = "You are Timed Out"
            case _:
                message = ""
    else:
        message = ""

    with open("./www/templates/index.html", 'r') as f:
        return render_template_string(f.read(), info=message)