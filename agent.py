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

def collect_redis_info(host, port=6379, timeout=2):
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

#-----------------agent loop---------------------

def run_agent():
    try:
        config = load_config()
        state = load_state()
        REPORT_FILE = BASE_DIR / config["reporting"]["output"]

    # Ensure directory exists
        for path in [STATE_FILE.parent, LOG_FILE.parent, REPORT_FILE.parent]:
            path.mkdir(parents=True, exist_ok=True)

    #------------logging-----------------

        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )

    
        logging.info("Agent is Running")

        timestamp = datetime.now(timezone.utc).isoformat()
        snapshot = {
            "timestamp": timestamp,
            "environments": {}
        }   

# placeholder data collection happens here 

        for env, details in config["environments"].items():
            snapshot["environments"][env] = {
                "hosts": {}
            }

            for host in details["hosts"]:
                logging.info(f"Collecting Redis INFO from {host}")

                info = collect_redis_info(host)

                snapshot["environments"][env]["hosts"][host] = info

# Store snapshot (history)

        state[timestamp] = snapshot
        save_state(state)

# Tier-0 placeholder report

        report = f"""# Redis Tier-0 Agent Report

Run time: {timestamp}

## Environments observed 
"""
        for env, env_data in snapshot["environments"].items():
            report += f"## Environment {env}\n\n"

            for host, host_data in env_data["hosts"].items():
                report += f"## Host: {host}\n"

                for key, value in host_data.items():
                    report += f"- {key}: {value}\n"

        report += "\n"


        write_report(REPORT_FILE, report)
        logging.info("Agent run completed successfully")

    except Exception as e:
        logging.error("Agent run failed")
        logging.exception(e)

#-----------------entry-------------------

if __name__ == "__main__":
    run_agent()
