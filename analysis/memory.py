def get_connected_master_memory(snapshot):

    result = {}

    for env_name, env_data in snapshot["environments"].items():
        env_masters = {}

        for host_ip, host_data in env_data["hosts"].items():

            for port, inst in host_data["redis"]["instances"].items():
                if inst["status"] != "ok":
                    continue

                if not inst["cluster"]["enabled"]:
                    continue

                topology = inst["cluster"]["nodes"]
                self_node_id = inst["cluster"].get("self_node_id")

                #skip if somehow the self node id is missing

                if not self_node_id:
                    continue

                #check if this instance is a connected master

                for master in topology["masters"]:
                    if (
                        master["node_id"] == self_node_id and 
                        master["state"] == "connected"
                    ):
                        env_masters[self_node_id] = inst["memory"]["used_memory"]

        if env_masters:
            result[env_name] = env_masters
    return result

def calculate_average_memory(master_memory_dict):
    if not master_memory_dict:
        return {}
    
    result = {}

    for env_name, masters in master_memory_dict.items():
        values = list(masters.values())

        if not values:
            continue

        avg = sum(values) / len(values)

        result[env_name] = {
            "average": avg,
            "count": len(values)
        }
    
    return result
                