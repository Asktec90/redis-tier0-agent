#!/usr/bin/env python3

import yaml
import json
import logging
import redis
from datetime import datetime, timezone
from pathlib import Path

#------------Base Paths----------------

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "state" / "snapshots.json"
LOG_FILE = BASE_DIR / "logs" / "agent.log"

# Ensure directory exists
for path in [STATE_FILE.parent, LOG_FILE.parent]:
    path.mkdir(parents=True, exist_ok=True)

#------------logging-----------------

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

#------------Utilities------------------
def load_config():
    with open(BASE_DIR / "config.yaml") as f:
        return yaml.safe_load(f)

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def write_report(path, text):
    path.write_text(text)

def collect_redis_info(host, port, timeout):
    try:
        r = redis.Redis(
            host=host,
            port=port,
            socket_timeout=timeout,
            decode_responses=True
        )

        r.ping()
        info = r.info()

        return {
            "status": "ok",
            "role": info.get("role"),
            "redis_version": info.get("redis_version"),
            "uptime_seconds": info.get("uptime_in_seconds"),
            "used_memory": info.get("used_memory"),
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "mem_fragmentation_ratio": info.get("mem_fragmentation_ratio")
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def generate_report(snapshot):
    lines = []

    meta = snapshot["metadata"]
    lines.append("# Redis Tier-0 Agent Report\n")
    lines.append(f"Run time: {meta['timestamp']}\n")

    for env, env_data in snapshot["environments"].items():
        lines.append(f"## Environment: {env}\n")
        
        for host, host_data in env_data["hosts"].items():
            lines.append(f"### Host: {host}\n")

            redis = host_data["redis"]
            lines.append(f"Redis mode: {redis['mode']}\n")
            lines.append("| Port | Status | Role | Version | Memory | Clients |")
            lines.append("|------|--------|------|---------|--------|---------|")

            for port, inst in redis["instances"].items():
                if inst["status"] == "ok":
                    lines.append(
                            f"| {port} | OK | {inst.get('role')} | "
                            f"{inst.get('redis_version')} | "
                            f"{inst.get('used_memory_human')} | "
                            f"{inst.get('connected_clients')} |"
                    )
                else:
                    lines.append(f"| {port} | ERROR | - | - | - | - |")

            lines.append("")

    return "\n".join(lines)

#-----------------agent loop---------------------

def run_agent():
    try:
        config = load_config()
        state = load_state()
        REPORT_FILE = BASE_DIR / config["reporting"]["output"]

    # Ensure report directory exists
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

        logging.info("Agent is Running")

        timestamp = datetime.now(timezone.utc).isoformat()
        snapshot = {
            "metadata":{
                "agent": "Redis-tier0-agent",
                "version": "0.1",
                "timestamp": timestamp
            },
            "environments": {}
        }

# placeholder data collection happens here

        for env_name, env_cfg in config["environments"].items():
            snapshot["environments"][env_name] = {
                "type": env_cfg.get("type"),
                "hosts": {}
            }

            for host_cfg in env_cfg["hosts"]:
                host_ip = host_cfg["ip"]
                redis_cfg = host_cfg["redis"]
                redis_mode = redis_cfg["mode"]
                ports = redis_cfg["ports"]

                snapshot["environments"][env_name]["hosts"][host_ip] = {
                        "system": {
                            "cpu": None,
                            "memory": None,
                            "io": None
                        },
                        "redis": {
                            "mode": redis_mode,
                            "instances": {}
                        }
                }

                for port in ports:
                    info = collect_redis_info(
                            host=host_ip,
                            port=port,
                            timeout=config["connection"]["timeout_seconds"]
                    )

                    snapshot["environments"][env_name]["hosts"][host_ip]["redis"]["instances"][str(port)] = info


# Store snapshot (history)

        state[timestamp] = snapshot
        save_state(state)

# Tier-0 report generation

        report = generate_report(snapshot)
        write_report(REPORT_FILE, report)
        
        logging.info("Agent run completed successfully")

    except Exception as e:
        logging.error("Agent run failed")
        logging.exception(e)

#-----------------entry-------------------

if __name__ == "__main__":
    run_agent()
