from flask import Flask, Response, request

from routes.realtime_generated import realtime_generated
from routes.resources import resources
from routes.landing import landing
from routes.setup import setup
from routes.configurator import configurator
from routes.auth import auth

# Proxy must be last
from routes.proxy import proxy

from libs.config import load_reloading_config, read_config
from multiprocessing import Process
from datetime import datetime
from ssl import SSLContext, PROTOCOL_TLSv1_2
from threading import Thread
import sys, logging

cfg = load_reloading_config('pyromanic.yaml')

if not read_config(cfg(), 'enabled', bool):
    exit(1)

app = Flask(__name__, static_folder=None)

log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

logger = logging.getLogger('pyromanic')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app.register_blueprint(realtime_generated)
app.register_blueprint(resources)
app.register_blueprint(landing)
app.register_blueprint(setup)
app.register_blueprint(configurator)
app.register_blueprint(auth)

# Proxy must be last
app.register_blueprint(proxy)

def log_error(s: str) -> int:
    if not "Traceback" in s:
        return 0
    print(s)
    if read_config(cfg(), "logging.file", str) != "off":
        with open(read_config(cfg(), "logging.file", str), 'a') as f:
            return f.write(
                "[" + datetime.now().strftime("%d/%b/%Y %H:%M:%S") + "]" + s + "\n"
                )
    return 0

sys.stderr.write = log_error

@app.after_request
def log_request(response: Response):
    if not read_config(cfg(), "logging.enabled", bool):
        return response

    logger_msg = ""
    if read_config(cfg(), 'logging.show_ips', bool):
        logger_msg += f'[{request.remote_addr}]'
    logger_msg += "[" + datetime.now().strftime("%d/%b/%Y %H:%M:%S") + "] "
    logger_msg += f'"{request.method} {request.path} {request.environ.get("SERVER_PROTOCOL")}" '
    logger_msg += f'{response.status_code}'

    if read_config(cfg(), "logging.console", bool):
        logger.info(logger_msg)

    if read_config(cfg(), "logging.file", str) != "off":
        with open(read_config(cfg(), "logging.file", str), 'a') as f:
            f.write(logger_msg + "\n")
    return response

def https_app():
    if read_config(cfg(), 'https.adhoc', bool):
        app.run(
            ssl_context='adhoc',
            host = read_config(cfg(), 'https.host', str),
            port = read_config(cfg(), 'https.port', int)
        )
    else:
        context = SSLContext(PROTOCOL_TLSv1_2)
        context.load_cert_chain(
            read_config(cfg(), 'https.certificate', str),
            read_config(cfg(), 'https.private_key', str)
        )
        app.run(
            ssl_context=context,
            host = read_config(cfg(), 'https.host', str),
            port = read_config(cfg(), 'https.port', int)
        )

def http_app():
    app.run(
        host = read_config(cfg(), 'http.host', str),
        port = read_config(cfg(), 'http.port', int)
    )

def https_thread():
    p = Process(target=https_app, daemon=False)
    p.start()
    p.join()
    if p.exitcode != 0:
        sys.exit(p.exitcode)

def http_thread():
    p = Process(target=http_app, daemon=False)
    p.start()
    p.join()
    if p.exitcode != 0:
        sys.exit(p.exitcode)

if __name__ == "__main__":
    if read_config(cfg(), "logging.file", str) != "off":
        with open(read_config(cfg(), "logging.file", str), 'a') as f:
            f.write("[" + datetime.now().strftime("%d/%b/%Y %H:%M:%S") + f"] Starting Pyromanic {read_config(cfg(), "version", str)}..." + "\n")

    if read_config(cfg(), 'https.enabled', bool):
        Thread(target=https_thread, daemon=True).start()
    if read_config(cfg(), 'http.enabled', bool):
        Thread(target=http_thread, daemon=True).start()
    input("Press Enter to Stop")