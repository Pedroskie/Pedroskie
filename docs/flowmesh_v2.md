# FlowMesh v2 (Technical Mode)

FlowMesh v2 is a lightweight mesh health plane that links the phone (sensor),
the Raspberry Pi (orchestrator), and the laptop (witness) into a shared
observability loop. It focuses on heartbeat propagation, shared state on disk,
predictive health scoring, and mesh-wide situational awareness.

## Components

- **flowmesh/flowmesh_bus.json** — Shared state file (heartbeat, metrics,
  node scores, and mesh summary). If it is missing, the heartbeat daemon
  auto-creates a default bus with `phone`, `pi`, and `laptop` nodes.
- **flowmesh/heartbeat.py** — Emits heartbeats and metrics. Updates node
  status, health score, and the mesh summary.
- **flowmesh/predictor.py** — Runs a small risk model that surfaces forward
  failure probability signals for each node.

## Using the heartbeat emitter

```bash
python -m flowmesh.heartbeat phone \
  --latency-ms 28 --packet-loss 0.02 --cpu-percent 23 --battery-percent 82
```

The command will update `flowmesh/flowmesh_bus.json` with the latest snapshot,
re-score the node, and recompute the mesh summary.

## Running the prediction pass

```bash
python -m flowmesh.predictor
```

This consumes the shared bus, runs a trend-based risk model across recent
snapshots, and writes the predicted risk to each node entry.

## Bus schema (compact)

```json
{
  "mesh_id": "flowmesh-v2",
  "updated_at": "2024-05-22T10:03:08.254Z",
  "nodes": {
    "phone": {
      "role": "sensor",
      "heartbeat": "2024-05-22T10:03:08.254Z",
      "status": "online",
      "metrics": {"latency_ms": 28.0, "packet_loss": 0.02},
      "health_score": 0.93,
      "predicted_risk": 0.14,
      "history": [ {"latency_ms": 28.0, "packet_loss": 0.02, ...} ]
    }
  },
  "mesh_summary": {
    "online": 2,
    "degraded": 1,
    "offline": 0,
    "average_health": 0.82,
    "last_prediction": "2024-05-22T10:03:08.254Z"
  }
}
```

## Design notes

- **Shared heartbeat files** live under `flowmesh/flowmesh_bus.json`.
- **Node-to-node health scoring** runs inside `heartbeat.py` with a weighted
  heuristic that combines latency, packet loss, CPU, thermal, and battery.
- **Distributed prediction** is provided by `predictor.py` using a moving
  window of recent snapshots.
- **Mesh-wide telemetry** is encoded in `mesh_summary` to power dashboards or
  other collectors.
- **Cross-node awareness** comes from the shared bus and the average-health
  rollup.
- **Failure forecasting** uses latency slope, packet loss, low battery, and
  thermal risk signals.
- **Distributed logs** can consume the `history` list per node for audit and
  replay.
- **Mesh consensus** can layer on top of the shared bus by having guardians
  vote on the `mesh_summary` or future `mesh_decisions` fields.
