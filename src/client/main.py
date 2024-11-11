import os
import multiprocessing
import signal
import json
import outside

import engine
from config import config,script_dir

if (__name__ != "__main__"):
    raise RuntimeError("This is not a module.")

host = ("127.0.0.1",config["http_port"])
ui_path = (f"{script_dir}/ui")

# HTTP Server
http_server = outside.OutsideHTTP(host)

def server_cleanup():
    engine_queue.put(b"")
http_server.config["server_cleanup"] = server_cleanup

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

engine_queue = multiprocessing.Queue()
websocket_occupied = multiprocessing.Value("b",False)
def websocket_handler(connection):
    if (websocket_occupied.value):
        print("[WARN] WebSocket double connection prevented.")
        connection.exit()
    
    def _on_connection_exit():
        websocket_occupied.value = False
    connection.on_exit = _on_connection_exit

    websocket_occupied.value = True
    while True:
        msg = connection.recv()
        if (len(msg) == 0):
            connection.exit()
            continue
        msg_json = json.loads(msg)
        connection.send(msg)
        

websocket_server = outside.protocol_websocket.WebSocket()
websocket_server.connection_handler = websocket_handler
http_server.set_route("/websocket",websocket_server)

# Engine Process
ipv6_enabled = True
engine_process = multiprocessing.Process(
    target = engine.engine_process,
    args = [
        host,
        ipv6_enabled,
        engine_queue
    ]
)
engine_process.start()

# Finish
http_server.run()
engine_process.wait()
