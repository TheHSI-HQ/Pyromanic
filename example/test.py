from flask import Flask, request, send_file

app = Flask(__name__)

@app.route("/favicon.ico")
def favicon():
    return send_file("favicon.ico")

@app.route("/<path:_>", methods=["GET", "HEAD", "OPTIONS", "TRACE", "PUT", "DELETE", "POST", "PATCH", "CONNECT"])
def test(_):
    a='<br>'.join([k + ": " + v for k, v in request.headers])
    a+="<br><p></p>" + request.method
    a+="<br><p></p>" + request.url
    return a

app.run(debug=True)