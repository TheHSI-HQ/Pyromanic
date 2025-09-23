from flask import Blueprint
from libs.preprocessor import render_template_string
from libs.config import load_reloading_config, read_config
from libs.metrics import Metrics
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

cfg = load_reloading_config('pyromanic.yaml')
metrics = Metrics()

landing = Blueprint('landing', __name__, template_folder='../www/templates', url_prefix=read_config(cfg(), 'app.base_path', str))

@landing.route("/")
@metrics.measure
def index():
    # Generate our private key
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    public_key = private_key.public_key()

    # Export our public key to send to the browser as SPKI (PEM)
    public_pem = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open("./www/templates/index.html", 'r') as f:
        return render_template_string(f.read(), info="The Username or Password you entered were Incorrect!", pem=public_pem.decode())