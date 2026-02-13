#!/usr/bin/env python3
from .cluster_parser import parse_cluster_nodes
import redis

def collect_redis_info(host, port, timeout):
    try:
        r = redis.Redis(
            host=host,
            port=port,
            socket_timeout=timeout,
            decode_responses=True
        )

        r.ping()
        base_info = r.info()
        cluster_enabled = base_info.get("cluster_enabled", 0)

        #Handle keyspace safely
        db0 = base_info.get("db0", {})
        keys = db0.get("keys", 0)
        expires = db0.get("expires", 0)

        result = {
            "status": "ok",
            "role": base_info.get("role"),
            "redis_version": base_info.get("redis_version"),
            "uptime_seconds": base_info.get("uptime_in_seconds"),

            "memory": {
                "used_memory": base_info.get("used_memory"),
                "used_memory_human": base_info.get("used_memory_human"),
                "used_memory_rss": base_info.get("used_memory_rss"),
                "used_memory_rss_human": base_info.get("used_memory_rss_human"),
                "mem_fragmentation_ratio": base_info.get("mem_fragmentation_ratio"),
                "maxmemory": base_info.get("maxmemory")
            },

            "stats": {
                "evicted_keys": base_info.get("evicted_keys"),
                "expired_keys": base_info.get("expired_keys"),
                "instantaneous_ops_per_sec": base_info.get("instantaneous_ops_per_sec")
            },

            "keyspace": {
                "keys": keys,
                "expires": expires
            },

            "cluster": {
                "enabled": bool(cluster_enabled)
            }
        }

        if result["cluster"]["enabled"]:
            cluster_nodes = r.execute_command("CLUSTER NODES")
            result["cluster"]["nodes"] = parse_cluster_nodes(cluster_nodes)


        return result

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

