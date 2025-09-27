from flask import Blueprint
from libs.preprocessor import render_template_string
from libs.config import load_reloading_config, read_config
from libs.metrics import Metrics

cfg = load_reloading_config('pyromanic.yaml')
metrics = Metrics()

setup = Blueprint('setup', __name__, template_folder='../www/templates', url_prefix=read_config(cfg(), 'app.base_path', str))

@setup.route("/setup")
@metrics.measure
def setup_page():
    with open("./www/templates/setup.html", 'r') as f:
        return render_template_string(f.read())