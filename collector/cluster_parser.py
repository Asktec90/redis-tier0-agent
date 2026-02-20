#!/usr/bin/env python3

def parse_cluster_nodes(cluster_nodes):

    topology = {
        "masters": [],
        "replicas": [],
        "resharding_detected": False
    }

    lines = cluster_nodes.splitlines()

    for line in lines:
        if not line.strip():
            continue
        parts = line.split()

        if len(parts) < 8:
            continue

        node_id = parts[0]
        address = parts[1]
        flags = parts[2]
        state = parts[7]

        ip_port = address.split("@")[0]
        ip, port = ip_port.split(":")
        port = int(port)
        flag_list = flags.split(",")

        if "master" in flag_list:

            slots = []

            for item in parts[8:]:
                if item.startswith("["):
                    topology["resharding_detected"] = True
                    continue

                if "-" in item:
                    try:
                        start, end = item.split("-")
                        slots.append((int(start), int(end)))
                    except ValueError:
                        continue

            master_obj = {
                "node_id": node_id,
                "ip": ip,
                "port": port,
                "state": state,
                "flags" : flag_list,
                "slots": slots
            }

            topology["masters"].append(master_obj)

        elif "slave" in flag_list:

            replica_obj = {
                "node_id": node_id,
                "ip": ip,
                "port": port,
                "flags": flag_list,
                "state": state
            }

            topology["replicas"].append(replica_obj)

    return topology

