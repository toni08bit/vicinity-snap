import sys
import os
import subprocess
import pickle
import outside

from config import config,script_dir

if (__name__ != "__main__"):
    raise RuntimeError("This is not a module.")

host = ("127.0.0.1",config["http_port"])
ui_path = (f"{script_dir}/ui")

http_server = outside.OutsideHTTP(host)

def main_route(request):
    requested_path = os.path.abspath(ui_path + request.url)
    if (not requested_path.startswith(ui_path)):
        return 403,"Invalid parent folder."
    if (os.path.isdir(requested_path)):
        if (os.path.exists(requested_path + "/index.html")):
            return outside.protocol_http.Response(
                status_code = 200,
                headers = {},
                content = outside.protocol_http.FilePath(requested_path + "/index.html")
            )
        else:
            return 404,"No index.html file."
    elif (os.path.isfile(requested_path)):
        return outside.protocol_http.Response(
            status_code = 200,
            headers = {},
            content = outside.protocol_http.FilePath(requested_path)
        )
    else:
        return 404,"URL not found or unavailable."
http_server.set_route("/",main_route)

engine_process = subprocess.Popen(
    args = [
        sys.executable,
        (f"{os.path.dirname(os.path.realpath(__file__))}/engine.py"),
    ],
    stdin = subprocess.PIPE,
    stdout = sys.stdout,
    stderr = sys.stdout
)
engine_process.stdin.write(pickle.dumps({
    "host": host,
    "ipv6_mode": True
}))
engine_process.stdin.close()

http_server.run()
engine_process.wait()
