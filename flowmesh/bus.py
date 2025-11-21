from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def _default_node(role: str) -> "NodeState":
    return NodeState(role=role)


@dataclass
class MetricSnapshot:
    latency_ms: Optional[float] = None
    packet_loss: Optional[float] = None
    cpu_percent: Optional[float] = None
    battery_percent: Optional[float] = None
    temperature_c: Optional[float] = None
    free_memory_mb: Optional[float] = None
    note: Optional[str] = None
    timestamp: str = field(default_factory=_utc_now)


@dataclass
class NodeState:
    role: str
    heartbeat: Optional[str] = None
    status: str = "unknown"
    metrics: Dict[str, float] = field(default_factory=dict)
    health_score: Optional[float] = None
    predicted_risk: Optional[float] = None
    history: List[MetricSnapshot] = field(default_factory=list)

    def add_snapshot(self, snapshot: MetricSnapshot) -> None:
        self.history.append(snapshot)
        self.heartbeat = snapshot.timestamp
        self.metrics = {
            k: v
            for k, v in snapshot.__dict__.items()
            if k != "timestamp" and v is not None
        }


@dataclass
class MeshSummary:
    online: int = 0
    degraded: int = 0
    offline: int = 0
    average_health: Optional[float] = None
    last_prediction: Optional[str] = None


@dataclass
class MeshBus:
    mesh_id: str
    updated_at: Optional[str] = None
    nodes: Dict[str, NodeState] = field(default_factory=dict)
    mesh_summary: MeshSummary = field(default_factory=MeshSummary)

    def touch(self) -> None:
        self.updated_at = _utc_now()


class BusCodec:
    @staticmethod
    def load(path: Path) -> MeshBus:
        if not path.exists():
            raise FileNotFoundError(f"Bus file not found: {path}")

        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)

        nodes = {
            name: NodeState(
                role=node.get("role", "unknown"),
                heartbeat=node.get("heartbeat"),
                status=node.get("status", "unknown"),
                metrics=node.get("metrics", {}),
                health_score=node.get("health_score"),
                predicted_risk=node.get("predicted_risk"),
                history=[MetricSnapshot(**snapshot) for snapshot in node.get("history", [])],
            )
            for name, node in raw.get("nodes", {}).items()
        }

        mesh_summary = MeshSummary(**raw.get("mesh_summary", {}))

        return MeshBus(
            mesh_id=raw.get("mesh_id", "flowmesh-v2"),
            updated_at=raw.get("updated_at"),
            nodes=nodes,
            mesh_summary=mesh_summary,
        )

    @staticmethod
    def save(bus: MeshBus, path: Path) -> None:
        serializable = {
            "mesh_id": bus.mesh_id,
            "updated_at": bus.updated_at,
            "nodes": {
                name: {
                    "role": node.role,
                    "heartbeat": node.heartbeat,
                    "status": node.status,
                    "metrics": node.metrics,
                    "health_score": node.health_score,
                    "predicted_risk": node.predicted_risk,
                    "history": [snapshot.__dict__ for snapshot in node.history[-50:]],
                }
                for name, node in bus.nodes.items()
            },
            "mesh_summary": bus.mesh_summary.__dict__,
        }

        with path.open("w", encoding="utf-8") as handle:
            json.dump(serializable, handle, indent=2)


def ensure_bus(path: Path) -> MeshBus:
    if path.exists():
        return BusCodec.load(path)

    bus = MeshBus(mesh_id="flowmesh-v2")
    bus.nodes = {
        "phone": _default_node("sensor"),
        "pi": _default_node("orchestrator"),
        "laptop": _default_node("witness"),
    }
    bus.touch()
    BusCodec.save(bus, path)
    return bus
