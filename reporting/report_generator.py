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
            lines.append("| Port | Status | Role | Version | Memory | Clustered |")
            lines.append("|------|--------|------|---------|--------|-----------|")

            for port, inst in redis["instances"].items():
                if inst["status"] == "ok":
                    lines.append(
                            f"| {port} | OK | {inst.get('role')} | "
                            f"{inst.get('redis_version')} | "
                            f"{inst['memory']['used_memory_human']} | "
                            f"{inst['cluster']['enabled']} |"
                    )
                else:
                    lines.append(f"| {port} | ERROR | - | - | - | - |")

            lines.append("")

    return "\n".join(lines)

