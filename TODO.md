# AI-SERVIS – Implementation TODO

This TODO captures the remaining implementation work to deliver Phone / Hybrid / Pro editions. Tasks are grouped by phase and domain.

## Phase 1 – Analysis & Design
- [ ] Run 2× stakeholder workshops (service ops, legal/privacy, installers)
- [ ] Finalize LPR stack choice: CameraX+OCR (Phone) vs offload (Hybrid/Pro)
- [ ] Define OBD PID profiles by brand/segment (baseline EU post‑2008)
- [ ] UX flows: onboarding, privacy sliders, alerts, ANPR feed, dashboard gauges
- [ ] ADRs: background execution policy, local storage policy, OTA strategy
- [ ] DPIA/Privacy baseline (edge‑only defaults, retention, audit)

## Phase 2 – Android MVP
- [x] App skeleton: navigation, DI (Hilt), permissions (BLE/Camera/Location/Notifications)
- [x] Foreground DrivingService lifecycle (start/pause/resume/stop)
- [x] BLE Manager: scan/pair (QR bootstrap), GATT read/notify/write — stubs
- [x] MQTT Manager: local broker or WS client, reconnect and backpressure — working telemetry/alerts/events
- [x] OBD Manager: ELM327 BLE MVP (fuel, RPM, speed, coolant, DTC) — stub interface
- [x] ANPR light: pipeline placeholders and notifications channel — stub interface + events Flow
- [x] Rules Engine v1: YAML/JSON → predicates (fuel<20, temp>105, new DTC) → actions (alert/TTS/MQTT)
- [x] Alerts/Notifications: channels, rate‑limit, deep links (basic notifications wired)
- [x] Storage: encrypted preferences and clip/event store with retention sweeper
- [x] Voice: TTS/STT adapter (ElevenLabs/cloud pluggable) with barge‑in — stub TTS only
- [x] UI: dashboard (gauges), ANPR feed, alerts list, settings/privacy — basic VIN settings done
- [x] Telemetry publishing: `vehicle/telemetry/{vin}/obd` and `vehicle/events/{vin}/anpr`
- [x] Unit tests: rules, hashing, topic mapping; instrumentation: permissions, service lifecycle (skeleton)

## Phase 2 – ESP32 OBD Bridge (Read‑only)
- [ ] TWAI init + transceiver (GPIO map, bitrate 500k, 11‑bit)
- [ ] PID scheduler with rate limiting; listen‑only option
- [ ] BLE GATT services: telemetry notify, commands/config, OTA progress
- [ ] Config persist (NVS): VIN, intervals, thresholds, pairing keys
- [ ] OTA v1: signed manifest fetch + rollback safe
- [ ] Local alarms (fuel/temp) with buzzer/LED patterns (optional IO node)
- [ ] Power management: watchdog, graceful shutdown, brown‑out resilience
- [ ] Manufacturing/test mode: self‑test, loopback, BLE advert payload

## Phase 3 – Core Stabilization
- [x] Android connectivity hardening (BLE/Wi‑Fi Direct retries, mDNS discovery)
- [x] DVR light: rolling clip buffer; event‑triggered save; offload on home Wi‑Fi
- [x] ANPR precision: region rules (CZ/EU), O↔0/B↔8 heuristics, confidence tuning
- [x] Privacy enforcement: retention sweeper, export log, incognito mode
- [x] Crash/metrics: Sentry/Crashlytics, health pings, anonymized opt‑in metrics
- [ ] Battery/thermal guidelines: in‑app advisory, sampling policy

## Edge‑Compat (Hybrid/Pro, optional)
- [ ] Mosquitto bridge: phone ↔ gateway (leader election presence)
- [ ] Camera‑server: RTSP ingest, bookmark events, timeline API
- [ ] LPR engine container: same contracts; disable phone ANPR when gateway leads
- [ ] Health watchdog: restart policy, disk space guard, secure volumes

## Web & Sales Enablement
- [ ] Solutions page: Phone vs Hybrid vs Pro (compatibility badges)
- [ ] Configurator wizard: budget slider, features, reliability → bill of materials
- [ ] Pricing cards with rental toggle; JSON‑LD (LocalBusiness, Product)
- [ ] CTA strip, FAQ, privacy box, live calculator; analytics (GTM/GA4 events)
- [ ] Lead forms with server‑side email + DKIM/DMARC

## CI/CD & Release
- [ ] Android: signing setup, internal track, versioning, fastlane optional
- [ ] ESP32: matrix builds (esp32, s3), signing with key in secrets, artifact manifests
- [ ] Edge images: container build, compose templates, healthchecks
- [ ] Linting/format/QA gates; SBOM generation (optional)

## Security & Privacy
- [ ] Pairing flow: QR (nodeId, pubkey), Ed25519, Android Keystore
- [ ] TLS pinning (Wi‑Fi sessions), cert rotation plan
- [ ] Audit events: pairing, policy changes, exports, OTA
- [ ] DPIA template + privacy README (CZ/EU) checked by counsel
- [ ] Role‑based UI (owner vs installer), data access scoping

## Pilot (10 vehicles)
- [ ] Installer checklist (OBD split, power, cable routing, fuse ratings)
- [ ] Device‑tester tool (BLE scan, RSSI, GATT diagnostics, CAN bitrate check)
- [ ] Success criteria: session reliability, ANPR precision, alert latency, UX NPS
- [ ] Feedback loop → backlog grooming and fixes

## Documentation
- [ ] Wiring diagrams (OBD/CAN, power topology, UVC hub when present)
- [ ] Contracts v1.x changelog and migration notes
- [ ] Install guides (Phone/Hybrid/Pro variants)
- [ ] Troubleshooting runbook (L1/L2/L3)

## QA & Validation
- [ ] Test matrix: Android devices/OS versions, BLE chipsets, camera models
- [ ] Drive scenarios: day/night, rain, tunnels, city/highway
- [ ] OBD profiles by makes (sanity PIDs, tolerance ranges)
- [ ] Load tests: MQTT throughput, event bursts, storage cleanup

## GA Readiness
- [ ] Final security review; pen test light
- [ ] SLA and support process; spares inventory
- [ ] Release notes v1.0; partner enablement (training assets)
- [ ] Rollout plan (region → national)
