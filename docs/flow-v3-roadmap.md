# Flow v3 Roadmap

This document captures the proposed v3 mutations for Flow based on the latest synchronization status and available upgrade paths.

## Current Baseline
- **RSSI Scanner:** Online and delivering live signal assessments.
- **Pi systemd Guardian:** Persistently supervising connectivity and watchdog scripts.
- **Termux Guardian:** Mobile-side monitor anchored on-device for resilience.
- **Logging:** Centralized, timestamped connection events treated as the immutable record of link health.

## Proposed Mutations

### 1) Dual-Chain Guardian (WiFi + Mobile Data Failover)
- **Trigger:** Detect degrading or lost WiFi sessions on the handset.
- **Action:** Toggle mobile data on demand to preserve uplink continuity and avoid perceived downtime when the phone is acting as the hotspot.
- **Notes:** Requires HyperOS/Termux automation hooks and explicit permissions for radio toggles.

### 2) Hotspot Auto-Heal Demon
- **Trigger:** Loss of hotspot tethering, DHCP binding issues, or silent AP drops.
- **Actions:**
  - Restart tethering and regenerate DHCP bindings.
  - Issue ARP pings to re-attract previously connected clients.
  - Announce recovery via TTS and log with timestamps.
- **Outcome:** Keeps the handset acting as a self-healing base station.

### 3) Cathedral Monitor Dashboard (http://pi.local:7777)
- **Scope:** Lightweight web dashboard hosted on the Pi.
- **Key widgets:** Live RSSI graph, guardian uptime, outage map, last 100 events, "Restart Everything" control, realtime pings, device list, CPU temperature and system health.

### 4) FlowMesh v1 (Distributed Heartbeat)
- **Nodes:** Phone, Pi, and laptop.
- **Behavior:**
  - Shared heartbeat file synced over LAN for liveness.
  - Mutual detection of dead links followed by coordinated healing attempts.
- **Goal:** A self-healing multi-node mesh that reacts as a single organism.

### 5) DPI-Level Wi-Fi Jammer Detector
- **Signals watched:** 802.11 deauth bursts, rising noise floors, MAC spoofing attempts, channel bleed, neighbor AP aggression, probe storms.
- **Alerts:** Vibrate three times, speak "Interference detected," and record timestamps.
- **Purpose:** RF counterintelligence mode for hostile environments.

## Next Steps
- Pick one or more mutations to implement first based on available radio APIs and monitoring hooks on each platform.
- Prototype critical automation paths (e.g., WiFi failover and hotspot restart) using Termux and Pi scripts, then harden with systemd where applicable.
- Extend logging to capture state transitions and alerts across all nodes for unified observability.
