from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Optional

from .bus import BusCodec, MeshBus, MetricSnapshot, ensure_bus


def calculate_status(snapshot: MetricSnapshot) -> str:
    if snapshot.packet_loss is not None and snapshot.packet_loss > 0.2:
        return "offline"
    if snapshot.latency_ms is not None and snapshot.latency_ms > 300:
        return "degraded"
    if snapshot.cpu_percent is not None and snapshot.cpu_percent > 95:
        return "degraded"
    return "online"


def update_mesh_summary(bus: MeshBus) -> None:
    online = 0
    degraded = 0
    offline = 0
    health_values = []

    for node in bus.nodes.values():
        if node.status == "online":
            online += 1
        elif node.status == "degraded":
            degraded += 1
        else:
            offline += 1

        if node.health_score is not None:
            health_values.append(node.health_score)

    bus.mesh_summary.online = online
    bus.mesh_summary.degraded = degraded
    bus.mesh_summary.offline = offline
    bus.mesh_summary.average_health = (
        sum(health_values) / len(health_values) if health_values else None
    )


def health_score(snapshot: MetricSnapshot) -> float:
    score = 1.0
    if snapshot.latency_ms:
        score -= min(snapshot.latency_ms / 1000, 0.5)
    if snapshot.packet_loss:
        score -= min(snapshot.packet_loss, 0.5)
    if snapshot.cpu_percent and snapshot.cpu_percent > 80:
        score -= min((snapshot.cpu_percent - 80) / 100, 0.2)
    if snapshot.battery_percent is not None and snapshot.battery_percent < 20:
        score -= 0.2
    if snapshot.temperature_c and snapshot.temperature_c > 70:
        score -= 0.1
    return max(0.0, round(score, 3))


def apply_heartbeat(bus_path: Path, node_name: str, metrics: Dict[str, float], note: Optional[str]) -> MeshBus:
    bus = ensure_bus(bus_path)
    node = bus.nodes.get(node_name)
    if node is None:
        from .bus import _default_node  # local import to avoid circular import in type checking

        node = _default_node(role="unknown")
        bus.nodes[node_name] = node

    snapshot = MetricSnapshot(**metrics, note=note)
    node.add_snapshot(snapshot)
    node.status = calculate_status(snapshot)
    node.health_score = health_score(snapshot)
    bus.touch()
    update_mesh_summary(bus)
    BusCodec.save(bus, bus_path)
    return bus


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FlowMesh heartbeat emitter")
    parser.add_argument("node", help="Node name (e.g. phone, pi, laptop)")
    parser.add_argument("--bus", default="flowmesh/flowmesh_bus.json", help="Path to the bus JSON")
    parser.add_argument("--latency-ms", type=float, dest="latency_ms")
    parser.add_argument("--packet-loss", type=float, dest="packet_loss")
    parser.add_argument("--cpu-percent", type=float, dest="cpu_percent")
    parser.add_argument("--battery-percent", type=float, dest="battery_percent")
    parser.add_argument("--temperature-c", type=float, dest="temperature_c")
    parser.add_argument("--free-memory-mb", type=float, dest="free_memory_mb")
    parser.add_argument("--note")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bus_path = Path(args.bus)

    metrics = {
        "latency_ms": args.latency_ms,
        "packet_loss": args.packet_loss,
        "cpu_percent": args.cpu_percent,
        "battery_percent": args.battery_percent,
        "temperature_c": args.temperature_c,
        "free_memory_mb": args.free_memory_mb,
    }

    apply_heartbeat(bus_path=bus_path, node_name=args.node, metrics=metrics, note=args.note)


if __name__ == "__main__":
    main()
