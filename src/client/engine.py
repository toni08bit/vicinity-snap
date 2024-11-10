import socket
import selectors
import sys
import urllib.request
import pickle
import subprocess
import os
import time

from config import config

if (__name__ != "__main__"):
    raise RuntimeError("This is not a module and should not be used manually.")

# Browser Setup
def check_200(url):
    try:
        response = urllib.request.urlopen(url)
        return (response.status == 200)
    except:
        return False

arg_data = pickle.loads(sys.stdin.buffer.read())
browser_url = f"http://{arg_data['host'][0]}:{arg_data['host'][1]}/"

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
        active_clients.remove(dead_client)

def register_client(address):
    address_list = list(address)
    for client_info in active_clients:
        if (client_info[1:] == address_list):
            client_info[0] = time.perf_counter()
            return
    active_clients.append([time.perf_counter()] + address_list)

if (arg_data["ipv6_mode"]):
    # IPv6 Mode
    private_socket = socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
    private_socket.bind(("::",0))
    private_socket.listen()

    multicast_address = (socket.inet_pton(socket.AF_INET6,config["group_addr"]) + (b"\x00" * 4))
    private_address = private_socket.getsockname()

    multicast = socket.socket(socket.AF_INET6,socket.SOCK_DGRAM)
    multicast.bind(("::",config["group_port"]))
    multicast.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_JOIN_GROUP,multicast_address)
    multicast.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_MULTICAST_HOPS,1)

    default_selector = selectors.DefaultSelector()
    default_selector.register(multicast,selectors.EVENT_READ,"multicast")
    default_selector.register(private_socket,selectors.EVENT_READ,"private")

    last_announcement = (-config["announce_interval"])
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
                    print(multicast.recvfrom(len(config["callsign"]) + 2))
                if (key.data == "private"):
                    print("accepting")
                    print(private_socket.accept())
        except TimeoutError:
            print("sent multicast")
            multicast.sendto((config["callsign"] + (private_address[1]).to_bytes(2,"big")),(config["group_addr"],config["group_port"]))
            last_announcement = time.perf_counter()
else:
    # IPv4 Mode
    pass