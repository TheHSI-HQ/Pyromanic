from flask import Blueprint, Response, request, send_file
from rcssmin import cssmin # pyright: ignore[reportUnknownVariableType, reportMissingTypeStubs]
from rjsmin import jsmin # pyright: ignore[reportUnknownVariableType, reportMissingTypeStubs]
from libs.metrics import Metrics
from libs.config import load_reloading_config, read_config
from yaml import safe_load
from os.path import exists

cfg = load_reloading_config('pyromanic.yaml')
metrics = Metrics()

resources = Blueprint('resources', __name__, template_folder='../www/templates', url_prefix=read_config(cfg(), 'app.base_path', str))

@resources.route("/res/css/<string:path>.css")
@metrics.measure
def css_provider(path: str):
    if not exists("./www/css/" + path + ".css"):
        return "<h1>404 Not Found</h1>", 404
    with open("./www/css/" + path + ".css", 'r') as f:
        read = f.read()

        base = read_config(cfg(), 'app.base_path', str).removesuffix("/")
        version = read_config(cfg(), 'version', str)
        read = read.replace("<<base>>", base)
        read = read.replace("<<version>>", version)

        if "dev" in request.args:
            return Response(read, 200, mimetype="text/css")
        minified: bytearray | bytes | str = cssmin(read) # pyright: ignore[reportUnknownVariableType]
        if isinstance(minified, str):
            return Response(minified, 200, mimetype="text/css")
    return Response("Failed to Compile CSS", 500, mimetype="text/text")

@resources.route("/res/js/<string:path>.js")
@metrics.measure
def js_provider(path: str):
    if not exists("./www/js/" + path + ".js"):
        return "<h1>404 Not Found</h1>", 404
    with open("./www/js/" + path + ".js", 'r') as f:
        read = f.read()

        base = read_config(cfg(), 'app.base_path', str).removesuffix("/")
        version = read_config(cfg(), 'version', str)
        read = read.replace("<<base>>", base)
        read = read.replace("<<version>>", version)

        if "dev" in request.args:
            return Response(read, 200, mimetype="text/javascript")
        minified: bytearray | bytes | str = jsmin(read) # pyright: ignore[reportUnknownVariableType]
        if isinstance(minified, str):
            return Response(minified, 200, mimetype="text/js")
    return Response("Failed to Compile JS", 500, mimetype="text/text")

@resources.route("/res/img/<string:path>.img")
@metrics.measure
def img_provider(path: str):
    t_path = path.split("-")[0]
    format = path.split("-")[1]
    if not exists("./www/img/" + t_path + ".yaml"):
        return "<h1>404 Not Found</h1>", 404
    with open("./www/img/" + t_path + ".yaml", 'r') as f:
        metadata = safe_load(f.read())
        if "formats" not in metadata or "default" not in metadata:
            return Response("Failed to Read Metadata", 500, mimetype="text/text")
        formats = metadata["formats"]
        default = metadata["default"]
        if format in formats:
            return send_file("./www/img/" + t_path + "/" + formats[format])
        else:
            return send_file("./www/img/" + t_path + "/" + formats[default])
    return Response("Failed to Compile CSS", 500, mimetype="text/text")