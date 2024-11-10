import sys
import os
import subprocess
import pickle

import outside

from config import config

host = ("127.0.0.1",config["http_port"])

if (__name__ != "__main__"):
    raise RuntimeError("This is not a module.")

http_server = outside.OutsideHTTP(host)

def main_route(request):
    return 200,"Hello."
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
