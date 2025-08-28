# Architecture Diagrams

## High-level System Architecture

```mermaid
graph TD
  subgraph Phone["Android Phone (Hub)"]
    A1["DrivingService\n(ANPR, OBD, Voice, DVR)"]
    A2["MQTT Client / Broker"]
  end

  subgraph ESP32["ESP32 Nodes"]
    E1["OBD/CAN Bridge\n(TWAI + Transceiver)"]
    E2["IO Node\n(Relays/LED/Buzzer)"]
    E3["S3-CAM (optional)\n(Snapshots)"]
  end

  subgraph Gateway["Pi Gateway (optional)"]
    G1["RTSP Camera Server / DVR"]
    G2["LPR Engine (offload)"]
    G3["MQTT Bridge"]
  end

  A1 -- BLE GATT / Wi‑Fi --> ESP32
  ESP32 -- MQTT / Wi‑Fi --> A2
  A2 <--> G3
  G1 --> G2
  A1 -. CameraX/USB OTG .- G1
```

## Data Flow (OBD → Alert)

```mermaid
sequenceDiagram
  participant ESP as ESP32 OBD Bridge
  participant AND as Android App
  participant RE as Rules Engine
  participant UI as Notifications/TTS

  ESP->>AND: BLE Notify Telemetry (fuel, rpm, temp)
  AND->>RE: Publish telemetry
  RE-->>AND: Evaluate predicates (fuel < 20%)
  AND->>UI: Show alert + TTS "Palivo dochází"
  AND->>MQTT: vehicle/alerts/{vin}
```

> Přidejte další diagramy (failover, discovery, pairing) dle potřeby.
