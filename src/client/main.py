import os
import multiprocessing
import selectors
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
    engine_pipe.send(b"")
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

engine_inner_pipe,engine_pipe = multiprocessing.Pipe()
websocket_occupied = multiprocessing.Value("b",False)
def websocket_handler(connection):
    if (websocket_occupied.value):
        connection.exit()
    print("[INFO] Connected websocket.")
    websocket_occupied.value = True
    
    def _on_connection_exit():
        websocket_occupied.value = False
        print("[INFO] Disconnected websocket.")
    connection.on_exit = _on_connection_exit

    default_selector = selectors.DefaultSelector()
    default_selector.register(connection.pipe.fileno(),selectors.EVENT_READ,"http")
    default_selector.register(engine_pipe.fileno(),selectors.EVENT_READ,"engine")
    while (True):
        event_data = default_selector.select()

        for key,events in event_data:
            if (key.data == "http"):
                msg = connection.recv()
                if (len(msg) == 0):
                    continue
                request_json = json.loads(msg)
                if (request_json["type"] == "active_clients"):
                    engine_pipe.send(request_json)
                    connection.send(json.dumps(engine_pipe.recv()).encode("utf-8"))
                    continue
            elif (key.data == "engine"):
                connection.send(json.dumps(engine_pipe.recv()))
        

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
        engine_inner_pipe
    ]
)
engine_process.start()

# Finish
http_server.run()
engine_process.wait()
