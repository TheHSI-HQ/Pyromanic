from flask import Blueprint, request, Response, stream_with_context, redirect
from typing import Iterator, Any, Callable
from libs.config import load_reloading_config, read_config, nullable_read_config
from libs.metrics import Metrics, flagExternal, flagInternal
from requests import request as rrequest
from re import compile, sub
from logging import warning
import zlib

cfg = load_reloading_config('pyromanic.yaml')
metrics = Metrics()

proxy = Blueprint('proxy', __name__, template_folder='../www/templates')

def add_additional_data(target_url: str, headers: dict[str, str]) -> tuple[str, dict[str, str]]:
    if nullable_read_config(cfg(), 'proxy.additional_data', list) is not None:
        for additional_data in read_config(cfg(), 'proxy.additional_data', list): # pyright: ignore[reportUnknownVariableType]
            if not isinstance(additional_data, dict):
                continue
            match additional_data["type"]:
                case "header":
                    headers[additional_data["key"]] = additional_data["value"]
                case "parameter":
                    if "?" in target_url:
                        target_url += "&" + additional_data["key"] + "=" + additional_data["value"] # pyright: ignore[reportUnknownVariableType]
                    else:
                        target_url += "?" + additional_data["key"] + "=" + additional_data["value"] # pyright: ignore[reportUnknownVariableType]
                case _: # pyright: ignore[reportUnknownVariableType]
                    raise ValueError("Cannot compute Additional Data")
    return (target_url, headers) # pyright: ignore[reportUnknownVariableType]

def fetch_client_ip(target_url: str) -> tuple[str, str]:
    fallback: str = str(request.remote_addr)

    method = read_config(cfg(), 'proxy.remote_ip_method', str)
    if method.startswith("header[") and method.endswith("]"):
        header = method.removeprefix("header[").removesuffix("]")
        if header in request.headers:
            return str(request.headers.get(header)), target_url
        warning(f"remote_ip_method is set to header but the supplied header ({header}) wasn't found")
        return (fallback, target_url)
    if method.startswith("parameter[") and method.endswith("]"):
        parameter = method.removeprefix("parameter[").removesuffix("]")
        if parameter in request.args:
            parameter_regex = compile(f"[&?]{parameter}=[^&]+")
            target_url = parameter_regex.sub('', target_url)
            return str(request.args.get(parameter)), target_url
        warning(f"remote_ip_method is set to parameter but the supplied parameter ({parameter}) wasn't found")
        return (fallback, target_url)
    if method == "url":
        ip = request.path.removesuffix("/").split("/")[-1]
        target_url = sub(r'/[^/?]+/?(?=\?|$)', '', target_url)

        return (ip, target_url)
    if method == "source":
        return (fallback, target_url)
    raise ValueError("remote_ip_method is not a valid value")

def append_info_header(headers: dict[str, str], client_ip: str) -> dict[str, str]:
    for header in read_config(cfg(), 'proxy.remote_ip_header', list): # pyright: ignore[reportUnknownVariableType]
        if not isinstance(header, str):
            continue
        headers[header] = client_ip # pyright: ignore[reportArgumentType]

    if not read_config(cfg(), "proxy.skip_x-pyromanic", bool):
        headers["X-Pyromanic"] = "Pyromanic " + read_config(cfg(), "version", str)
    return headers

def decompress_stream(stream: Iterator[Any], encoding: str):
    if encoding.startswith("gzip"):
        dec = zlib.decompressobj(16+zlib.MAX_WBITS)
    elif encoding.startswith("deflate"):
        # deflate auto
        dec = zlib.decompressobj()
    else:
        dec = None

    for chunk in stream:
        if dec:
            data = dec.decompress(chunk)
            if data:
                yield data
        else:
            yield chunk
    if dec:
        tail = dec.flush()
        if tail:
            yield tail

def proxy_path(_flagExternal: Callable[[], None], _flagInternal: Callable[[], None]):
    if request.cookies.get("PYRO-AuthKey", type=str) is None:
        base = read_config(cfg(), 'app.base_path', str)
        base += "" if base.endswith("/") else "/"
        return redirect(base)

    if request.method not in read_config(cfg(), 'proxy.allowed_methods', list):
        return "<h1>405 Method Not Allowed</h1>", 405

    requested_route = request.url.removeprefix(request.url_root)

    target_url = read_config(cfg(), 'proxy.web_root', str)
    if not target_url.endswith("/"):
        target_url += "/"
    target_url += requested_route

    if read_config(cfg(), 'proxy.no_modify', bool) and read_config(cfg(), 'proxy.strict_no_modify', bool):
        headers = {key: value for key, value in request.headers}
        cookies = {key: value for key, value in request.headers}
    else:
        cookies = {key: value for key, value in request.headers if key.lower() != 'pyro-authkey'}
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}
        headers["Accept-Encoding"] = "identity"


    if not read_config(cfg(), 'proxy.no_modify', bool):
        client_ip, target_url = fetch_client_ip(target_url)
        target_url, headers = add_additional_data(target_url, headers)
        headers = append_info_header(headers, client_ip)

    if read_config(cfg(), 'proxy.proxy.http', str).lower() == "none" or read_config(cfg(), 'proxy.proxy.https', str).lower() == "none":
        proxies = None
    else:
        proxies=dict(http=read_config(cfg(), 'proxy.proxy.http', str),
                    https=read_config(cfg(), 'proxy.proxy.https', str))
    _flagExternal()
    resp = rrequest(
        method=request.method,
        url=target_url,
        headers=headers,
        data=request.get_data(),
        cookies=cookies,
        stream=True,
        allow_redirects=False,
        timeout=read_config(cfg(), 'proxy.timeout', int),
        proxies=proxies
    )
    _flagInternal()

    encoding = resp.headers.get("Content-Encoding", "").lower().strip()

    @stream_with_context  # ensure Flask context stays alive
    def generate_response():
        # upstream is your rrequest(...) with stream=True
        for data in decompress_stream(resp.iter_content(1024), encoding):
            yield data

    # Build response headers:
    excluded = ["content-length", "content-encoding", "transfer-encoding", "connection"]

    stripped_headers: list[str] | None = nullable_read_config(cfg(), "proxy.strip_headers", list) # pyright: ignore[reportUnknownVariableType]
    if stripped_headers is not None:
        for header in stripped_headers:
            excluded.append(header.lower())

    response_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded]

    return Response(
        generate_response(), # type: ignore (Buggy behavior)
        status=resp.status_code,
        headers=response_headers
    )

@proxy.route("/", defaults={'_': ''}, methods=["GET"])
@proxy.route("/<path:_>", methods=["GET"])
@metrics.measure
def proxy_path_get(_: str):
    return proxy_path(flagExternal, flagInternal)

@proxy.route("/", defaults={'_': ''}, methods=["HEAD"])
@proxy.route("/<path:_>", methods=["HEAD"])
@metrics.measure
def proxy_path_head(_: str):
    return proxy_path(flagExternal, flagInternal)

@proxy.route("/", defaults={'_': ''}, methods=["OPTIONS"])
@proxy.route("/<path:_>", methods=["OPTIONS"])
@metrics.measure
def proxy_path_options(_: str):
    return proxy_path(flagExternal, flagInternal)

@proxy.route("/", defaults={'_': ''}, methods=["TRACE"])
@proxy.route("/<path:_>", methods=["TRACE"])
@metrics.measure
def proxy_path_trace(_: str):
    return proxy_path(flagExternal, flagInternal)

@proxy.route("/", defaults={'_': ''}, methods=["PUT"])
@proxy.route("/<path:_>", methods=["PUT"])
@metrics.measure
def proxy_path_put(_: str):
    return proxy_path(flagExternal, flagInternal)

@proxy.route("/", defaults={'_': ''}, methods=["DELETE"])
@proxy.route("/<path:_>", methods=["DELETE"])
@metrics.measure
def proxy_path_delete(_: str):
    return proxy_path(flagExternal, flagInternal)

@proxy.route("/", defaults={'_': ''}, methods=["POST"])
@proxy.route("/<path:_>", methods=["POST"])
@metrics.measure
def proxy_path_post(_: str):
    return proxy_path(flagExternal, flagInternal)

@proxy.route("/", defaults={'_': ''}, methods=["PATCH"])
@proxy.route("/<path:_>", methods=["PATCH"])
@metrics.measure
def proxy_path_patch(_: str):
    return proxy_path(flagExternal, flagInternal)

@proxy.route("/", defaults={'_': ''}, methods=["CONNECT"])
@proxy.route("/<path:_>", methods=["CONNECT"])
@metrics.measure
def proxy_path_connect(_: str):
    return proxy_path(flagExternal, flagInternal)