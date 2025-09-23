from io import BytesIO
from flask import Blueprint, send_file
from PIL import Image
from pathlib import Path
import requests
from libs.config import load_reloading_config, read_config
from libs.cache import Cache
from libs.metrics import Metrics, flagCached
from logging import error, warning

cfg = load_reloading_config('pyromanic.yaml')
cache = Cache()
metrics = Metrics()

def merge_icons(icon_url: str) -> Image.Image:
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    try:
        base_img = Image.open(BytesIO(pull_icon(icon_url))).convert("RGBA")
        base_img = base_img.resize((128, 128), Image.Resampling.LANCZOS)
        canvas.paste(base_img, (0, 0), base_img)
        overlay_img = Image.open(Path() / 'www' / 'favicon.ico').convert("RGBA")
        overlay_img = overlay_img.resize((64, 64), Image.Resampling.LANCZOS)
        canvas.paste(overlay_img, (64, 64), overlay_img)
    except Exception:
        overlay_img = Image.open(Path() / 'www' / 'favicon.ico').convert("RGBA")
        overlay_img = overlay_img.resize((64, 64), Image.Resampling.LANCZOS)
        canvas.paste(overlay_img, (64, 64), overlay_img)
    return canvas

def pull_icon(url: str):
    buffer = BytesIO()
    try:
        buffer = BytesIO(requests.get(url, timeout=2).content)
        return buffer.getvalue()
    except Exception:
        error("Could not Read Custom Icon")
        with open(Path() / 'www' / 'error_favicon.ico', 'rb') as f:
            buffer.write(f.read())
        return buffer.getvalue()
    finally:
        buffer.close()

realtime_generated = Blueprint('realtime_generated', __name__, template_folder='../www/templates') # url_prefix=read_config(cfg(), 'app.base_path', str)

@realtime_generated.route('/favicon.ico')
@metrics.measure
def favicon():
    icon = read_config(cfg(), 'app.branding.icon', str)
    if cache.has_with_input('/favicon.ico', [icon]):
        data = cache.get_with_input('/favicon.ico', [icon])
        if isinstance(data, bytes):
            flagCached()
            return send_file(BytesIO(data), mimetype="image/png")
        else:
            warning("Cache for /favicon.ico in an Invalid Format (not bytes)")
    if icon == "default":
        buffer = BytesIO()
        with open(Path() / 'www' / 'favicon.ico', 'rb') as f:
            buffer.write(f.read())
        data = buffer.getvalue()
        buffer.close()
        cache.set('/favicon.ico', [icon], data)
        return send_file(BytesIO(data), mimetype="image/png")
    elif icon == "passthrough":
        url = read_config(cfg(), 'proxy.web_root', str)
        if not url.endswith("/"):
            url += "/"
        url += "favicon.ico"
        img = merge_icons(url)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        data = buffer.getvalue()
        buffer.close()
        cache.set('/favicon.ico', [icon], data)
        return send_file(BytesIO(data), mimetype="image/png")

    img = merge_icons(icon)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    data = buffer.getvalue()
    buffer.close()

    cache.set('/favicon.ico', [icon], data)

    return send_file(BytesIO(data), mimetype="image/png")