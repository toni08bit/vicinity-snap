import hashlib

# Manual Configuration
config = {
    "callsign": "vicinity-snap-v1",
    "group_addr": ["e001","0ff6"],
    "group_port": 10656,
    "http_port": 8082,
    "announce_interval": 3,
    "client_death_timeout": 5
}

# Improve Configuration / Convert Values
## config["callsign"]
config["callsign"] = hashlib.sha256(bytes(config["callsign"],"utf-8")).digest()

## config["group_addr"]
config["group_addr"] = f"ff02::{config['group_addr'][0]}:{config['group_addr'][1]}"