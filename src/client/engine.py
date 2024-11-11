def engine_process(host,ipv6_enabled,engine_queue):
    import socket
    import selectors
    import urllib.request
    import subprocess
    import signal
    import math
    import random
    import time

    import names
    from config import config,script_dir

    # Signals
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    signal.signal(signal.SIGINT,signal.SIG_IGN)

    # Browser Setup
    def check_200(url):
        try:
            response = urllib.request.urlopen(url)
            return (response.status == 200)
        except:
            return False

    browser_url = f"http://{host[0]}:{host[1]}/"

    while (True):
        if (check_200(browser_url)):
            break
        time.sleep(0.5)

    # subprocess.Popen(
    #     args = ["xdg-open",browser_url],
    #     stdout = subprocess.DEVNULL,
    #     stdin = subprocess.DEVNULL,
    #     preexec_fn = os.setpgrp
    # )
    print("\033[1m" + f"###\n\n[INFO] Open {browser_url}, if no browser has been opened automatically.\n\n###" + "\033[0m")

    # LAN Communication
    active_clients = []

    def check_dead():
        dead_clients = []
        for client_info in active_clients:
            if ((client_info[0] + config["client_death_timeout"]) < time.perf_counter()):
                dead_clients.append(client_info)
        for dead_client in dead_clients:
            print(f"[INFO] Client at {dead_client[1]} on {str(dead_client[2])} died.")
            active_clients.remove(dead_client)

    def register_client(address):
        for client_info in active_clients:
            if (client_info[1:] == address):
                client_info[0] = time.perf_counter()
                return
        print(f"[INFO] Registered new client at {address[0]} on {str(address[1])}.")
        active_clients.append([time.perf_counter()] + address)

    if (ipv6_enabled):
        # IPv6 Mode
        private_socket = socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
        private_socket.bind(("::",0))
        private_socket.listen()

        multicast_address = (socket.inet_pton(socket.AF_INET6,config["group_addr"]) + (b"\x00" * 4))
        private_address = private_socket.getsockname()
        print(f"[OK] Private socket on port {str(private_address[1])}.")

        multicast = socket.socket(socket.AF_INET6,socket.SOCK_DGRAM)
        multicast.bind(("::",config["group_port"]))
        multicast.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_JOIN_GROUP,multicast_address)
        multicast.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_MULTICAST_HOPS,1)
        multicast.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_MULTICAST_LOOP,0)
        print(f"[OK] Multicast on port {str(config['group_port'])}.")

        default_selector = selectors.DefaultSelector()
        default_selector.register(multicast,selectors.EVENT_READ,"multicast")
        default_selector.register(private_socket,selectors.EVENT_READ,"private")
        default_selector.register(engine_queue._reader,selectors.EVENT_READ,"main")
        
        device_name = (random.choice(names.adjectives) + random.choice(names.nouns) + str(math.floor(random.random() * 100)))

        last_announcement = (-config["announce_interval"])
        print(f"[OK] Initialized as {device_name}.")
        while (True):
            announcement_wait = (config["announce_interval"] - (time.perf_counter() - last_announcement))
            try:
                if (announcement_wait <= 0):
                    raise TimeoutError
                event_data = default_selector.select(config["announce_interval"])
                if (len(event_data) == 0):
                    raise TimeoutError
                
                for key,events in event_data:
                    if (key.data == "multicast"):
                        try:
                            pkg_len = (len(config["app_callsign"]) + 2)
                            recv_data,recv_addr = multicast.recvfrom(pkg_len)
                            if (recv_data[:len(config["app_callsign"])] != config["app_callsign"]):
                                print("[WARN] Callsign mismatch in message on channel. (Possible version mismatch!)")
                                continue
                            client_port = recv_data[(pkg_len - 2):]
                            if (len(client_port) != 2):
                                print("[WARN] Short message on channel.")
                                continue
                            client_port = int.from_bytes(client_port,"big")
                            register_client([recv_addr[0],client_port])
                        except Exception:
                            print("[ERROR] Exception while processing message on channel.")
                    elif (key.data == "main"):
                        queue_msg = engine_queue.get()
                        if (queue_msg == b""):
                            print("[OK] Stopping loop.")
                            return
                        pass # TODO termination processing
                    elif (key.data == "private"):
                        # TODO
                        print("accepting")
                        print(private_socket.accept())
            except TimeoutError:
                multicast.sendto((config["app_callsign"] + (private_address[1]).to_bytes(2,"big")),(config["group_addr"],config["group_port"]))
                last_announcement = time.perf_counter()
                check_dead()
    else:
        # IPv4 Mode
        pass