#!/usr/bin/env python3

import logging
from datetime import datetime, timezone
from pathlib import Path

from config import load_config, load_state, save_state, write_report
from collector.redis_collector import collect_redis_info
from reporting.report_generator import generate_report

#------------Base Paths----------------

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs" / "agent.log"

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

#------------logging-----------------

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

#-----------------agent loop---------------------

def run_agent():
    try:
        logging.info("Agent Started")
        config = load_config()
        state = load_state()
        REPORT_FILE = BASE_DIR / config["reporting"]["output"]

    # Ensure report directory exists
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).isoformat()
        snapshot = {
            "metadata":{
                "agent": config["agent"]["name"],
                "version": config["agent"]["version"],
                "schema_version": 1,
                "timestamp": timestamp
            },
            "environments": {}
        }

# -------------------Data Collection ---------------------

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
