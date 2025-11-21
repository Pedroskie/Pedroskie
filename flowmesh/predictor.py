from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Dict, List

from .bus import BusCodec, MeshBus, MetricSnapshot, NodeState, ensure_bus


@dataclass
class Prediction:
    node: str
    risk: float
    signal: str


class RiskModel:
    def __init__(self, history_window: int = 5) -> None:
        self.history_window = history_window

    def predict(self, node: NodeState) -> Prediction:
        recent = node.history[-self.history_window :]
        if not recent:
            return Prediction(node=node.role, risk=0.1, signal="insufficient data")

        latency_score = self._latency_score(recent)
        loss_score = self._loss_score(recent)
        battery_score = self._battery_score(recent)
        thermal_score = self._thermal_score(recent)

        risk = min(1.0, latency_score + loss_score + battery_score + thermal_score)
        signal = ", ".join(
            part
            for part in [
                self._signal("latency", latency_score),
                self._signal("loss", loss_score),
                self._signal("battery", battery_score),
                self._signal("thermal", thermal_score),
            ]
            if part
        )
        return Prediction(node=node.role, risk=round(risk, 3), signal=signal or "stable")

    def _latency_score(self, recent: List[MetricSnapshot]) -> float:
        values = [snap.latency_ms for snap in recent if snap.latency_ms is not None]
        if not values:
            return 0.05
        slope = self._slope(values)
        base = mean(values) / 1000
        return min(0.5, base + max(0.0, slope * 0.1))

    def _loss_score(self, recent: List[MetricSnapshot]) -> float:
        values = [snap.packet_loss for snap in recent if snap.packet_loss is not None]
        if not values:
            return 0.05
        return min(0.5, mean(values))

    def _battery_score(self, recent: List[MetricSnapshot]) -> float:
        values = [snap.battery_percent for snap in recent if snap.battery_percent is not None]
        if not values:
            return 0.0
        low_battery = 1 - min(values) / 100
        return max(0.0, low_battery * 0.3)

    def _thermal_score(self, recent: List[MetricSnapshot]) -> float:
        values = [snap.temperature_c for snap in recent if snap.temperature_c is not None]
        if not values:
            return 0.0
        overheat = [max(0.0, (v - 60) / 100) for v in values]
        return min(0.2, mean(overheat))

    def _slope(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        x = list(range(len(values)))
        x_mean = mean(x)
        y_mean = mean(values)
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
        denominator = sum((xi - x_mean) ** 2 for xi in x) or 1
        return numerator / denominator

    def _signal(self, name: str, score: float) -> str:
        if score > 0.4:
            return f"{name}:high"
        if score > 0.2:
            return f"{name}:medium"
        return ""


def update_predictions(bus_path: Path, model: RiskModel | None = None) -> Dict[str, Prediction]:
    bus = ensure_bus(bus_path)
    model = model or RiskModel()
    predictions: Dict[str, Prediction] = {}

    for node_name, state in bus.nodes.items():
        prediction = model.predict(state)
        state.predicted_risk = prediction.risk
        predictions[node_name] = prediction

    bus.mesh_summary.last_prediction = bus.updated_at
    BusCodec.save(bus, bus_path)
    return predictions


def main() -> None:
    bus_path = Path("flowmesh/flowmesh_bus.json")
    update_predictions(bus_path)


if __name__ == "__main__":
    main()
