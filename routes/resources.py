from flask import Blueprint, Response, request, send_file
from rcssmin import cssmin # pyright: ignore[reportUnknownVariableType, reportMissingTypeStubs]
from rjsmin import jsmin # pyright: ignore[reportUnknownVariableType, reportMissingTypeStubs]
from libs.metrics import Metrics
from libs.config import load_reloading_config, read_config
from yaml import safe_load
from os.path import exists
import os
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
    js_root = os.path.abspath("./www/js/")
    candidate_path = os.path.normpath(os.path.join("./www/js/", path + ".js"))
    candidate_fullpath = os.path.abspath(candidate_path)
    if not candidate_fullpath.startswith(js_root + os.sep):
        return Response("Forbidden", 403)
    if not exists(candidate_fullpath):
        return "<h1>404 Not Found</h1>", 404
    with open(candidate_fullpath, 'r') as f:
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
    img_root = os.path.abspath("./www/img/")
    metadata_candidate_path = os.path.normpath(os.path.join("./www/img/", t_path + ".yaml"))
    metadata_candidate_fullpath = os.path.abspath(metadata_candidate_path)
    if not metadata_candidate_fullpath.startswith(img_root + os.sep):
        return Response("Forbidden", 403)
    if not exists(metadata_candidate_fullpath):
        return "<h1>404 Not Found</h1>", 404
    with open(metadata_candidate_fullpath, 'r') as f:
        metadata = safe_load(f.read())
        if "formats" not in metadata or "default" not in metadata:
            return Response("Failed to Read Metadata", 500, mimetype="text/text")
        formats = metadata["formats"]
        default = metadata["default"]
        img_root = os.path.abspath("./www/img/")
        if format in formats:
            candidate_path = os.path.normpath(os.path.join("./www/img/", t_path, formats[format]))
            candidate_fullpath = os.path.abspath(candidate_path)
            if not candidate_fullpath.startswith(img_root + os.sep):
                return Response("Forbidden", 403)
            return send_file(candidate_fullpath)
        else:
            candidate_path = os.path.normpath(os.path.join("./www/img/", t_path, formats[default]))
            candidate_fullpath = os.path.abspath(candidate_path)
            if not candidate_fullpath.startswith(img_root + os.sep):
                return Response("Forbidden", 403)
            return send_file(candidate_fullpath)
    return Response("Failed to Compile CSS", 500, mimetype="text/text")