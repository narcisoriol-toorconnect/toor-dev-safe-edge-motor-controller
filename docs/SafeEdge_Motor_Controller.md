# SafeEdge Motor Controller  
## Project Request for Safety-Critical Embedded Product Development

### Client Project Brief

---

## 1. Project Overview

We are seeking an experienced embedded systems partner to design and deliver a **safety-critical motor controller product** intended for use across multiple regulated industries.

The product will act as a **standalone motor control and supervision unit** with an integrated human–machine interface and support for controlled software updates throughout its lifecycle.

This project is intended as both:
- A **real product foundation** suitable for industrialization
- A **reference implementation** demonstrating best practices in safety, maintainability, and long-term evolution

---

## 2. Product Description

The requested product is a **motor controller with integrated safety supervision**.

From a user perspective, the product:
- Controls a single electric motor
- Continuously monitors motor health and operating conditions
- Displays system state and faults on an integrated screen
- Enters a defined safe state under fault conditions
- Supports controlled updates after deployment
- Allows configurable running modes and algorithms

The product must behave deterministically, transparently, and predictably under all operating conditions.

---

## 3. Intended Application Domains

The product is intended to be applicable, with configuration changes only, to the following domains:

- Automotive auxiliary systems
- Industrial machinery and automation
- Medical device subsystems

Formal certification is not required within the scope of this project. However, the design and implementation must be **aligned with certification-ready practices** commonly required in these industries.

---

## 4. Safety Expectations

Safety is a core requirement of this project.

The product must:
- Perform startup self-checks before enabling motor operation
- Monitor critical runtime conditions during operation
- Detect and react to fault conditions in a deterministic manner
- Transition to a well-defined safe state when required
- Clearly indicate safety and fault status to the operator via the screen

Safety behavior must be:
- Clearly documented
- Testable
- Traceable to defined requirements

---

## 5. Software Update and Lifecycle Requirements

The product is expected to remain in service for a long period and to evolve over time.

As such:
- Software updates must be supported in a controlled manner
- Safety-critical behavior must remain protected from unintended changes
- Operators must be able to identify the software version running on the device
- Update and rollback behavior must be clearly defined and documented
- Client must be able to create configurable running modes easily without reflashing the safety-critical firmware

The update mechanism must be suitable for regulated environments and field deployment.

---

## 6. Human–Machine Interface (HMI)

The product must include a built-in human–machine interface.

Requirements:
- A physical display on the hardware device
- Clear visualization of system state, motor status, and fault conditions
- Operator actions limited to safe and clearly defined commands
- Consistent behavior between hardware operation and simulation

The HMI must prioritize clarity and safety over feature richness.

---

## 7. Simulation and Demonstration Environment

In addition to the physical device, a **simulation environment** representing the same product is required.

The simulated product must:
- Expose the same operational states and behaviors as the hardware device
- Present the same HMI through a browser-based interface
- Support fault injection and scenario demonstration
- Allow demonstration without physical hardware

Simulation is considered part of the product deliverable, not a development convenience.

---

## 8. Documentation and Deliverables

Professional-grade documentation suitable for internal review and external stakeholders is expected.

Deliverables must include:
- System overview and functional description
- Safety concept and assumptions
- Definition of operating states and fault handling
- Software and update lifecycle description
- Test strategy and evidence
- User-level operating documentation

Documentation must remain consistent with the implemented system.

---

## 9. Expectations from Toor Connect

We are looking for a partner who:
- Has proven experience in safety-critical embedded systems
- Can design firmware suitable for certification-oriented environments
- Understands long-term maintainability and lifecycle management
- Can propose a clean separation between safety-critical and evolvable software
- Is able to deliver both hardware-based and simulated demonstrations

We expect Toor Connect to:
- Propose the technical architecture
- Define safety boundaries
- Implement the embedded firmware
- Provide guidance on certification alignment
- Deliver a cohesive, demonstrable product

---

## 10. Project Outcome

At the end of the project, we expect to receive:
- A working hardware prototype
- A matching simulation environment
- Clear documentation of behavior, safety, and lifecycle
- A demonstrable product suitable for presentation to internal teams, customers, and auditors

This project will be used as a foundation for future product development and as a reference for our embedded systems strategy.

---

## 11. Next Steps

We are open to discussing scope, schedule, and technical approach in detail.

As a next step, we expect Toor Connect to provide an initial proposal outlining:
- Technical direction
- Key assumptions
- Project phases
- Estimated effort


---

## 12. Functional Specification (Toor Connect Proposal)

This section describes the concrete functionality proposed for the SafeEdge Motor Controller demo scope. It consolidates client intent with Toor Connect’s safety‑aligned practices to enable clear planning, development, and acceptance.

### 12.1 Device Functional Summary
- Controls a single electric motor with integrated safety supervision.
- Core controls: Start/Stop and selecting the desired profile
- Deterministic behavior under all conditions; transitions to a defined safe state on faults.
- Built‑in HMI shows state, faults, and running version.
- Browser‑based simulation mirrors device behavior for demos and testing.

### 12.2 Operating Modes and State Machine
- States: BOOT (self‑tests), IDLE (enabled, stopped), RUN (closed‑loop), WARN (advisory), FAULT (latched until ACK+clear), EMERGENCY (latched until power‑cycle/privileged reset), SAFE (outputs disabled), UPDATE (A/B update), DIAGNOSTICS (read‑only).
- Key transitions: BOOT→IDLE on self‑tests pass; IDLE↔RUN via Start/Stop (subject to interlocks); RUN→FAULT/EMERGENCY on monitored violations; FAULT→IDLE after operator ACK and condition cleared.
- Timing budgets: EMERGENCY disable ≤ 1 ms; FAULT ramp‑down to 0 A ≤ 10 ms then disable ≤ 20 ms.

### 12.3 Interfaces & I/O (Demo Platform)
- Power stage: 3‑phase bridge, DC bus input (monitored), phase current sensing.
- Sensors: DC bus voltage, phase current, heatsink temperature.
- Feedback: Encoder and/or Hall inputs (presence + plausibility checked).
- Actuators: Brake output, motor contactor/relay control (logic retained for HMI/logs).
- HMI: Integrated display + input controls.
- USB mass‑storage: Updates package drop and diagnostics export.

### 12.4 Control Performance (Demo Defaults)
- Speed setpoint range: 0–100% with rate limit ≤ 20%/s.
- Step ≤ 20% achieves ±5% steady‑state within 1 s.
- Start (RUN) to motion latency ≤ 150 ms; Stop to zero‑torque ≤ 50 ms (non‑EMERGENCY).
- Interlocks and monitoring enforced at all times.

### 12.5 Safety Self‑Tests at Boot
- Time budget: device becomes operative within ≤ 1 s on pass.
- Retries: up to 3 attempts; on persistent failure, enter safe state.
- Tests: firmware image CRC; RAM quick test (<10 ms); storage read/write + CRC; power‑rails in‑range; gate‑driver diagnostics; sensor plausibility at idle; encoder/Hall presence + plausibility.
- Safe state (boot failure): disable PWM/drive, engage brake, open motor relay (logic stays powered), HMI shows “Self‑test failed”.

### 12.6 Runtime Monitoring & Safe State
- Parameters and indicative policies (tunable):
	- DC bus V: WARN < 40/>60 V >100 ms; FAULT < 36/>65 V >20 ms.
	- Phase/arm current: WARN > 0.8·Imax >100 ms; FAULT > 1.0·Imax >10 ms; EMERGENCY > 1.5·Imax immediate (Imax default 30 A).
	- Heatsink temp: WARN > 85 °C >1 s; FAULT > 95 °C >200 ms; EMERGENCY > 105 °C immediate.
	- Speed/RPM: WARN > 110% >200 ms; FAULT > 120% >100 ms; EMERGENCY > 130% immediate.
	- 3V3/5V rails: WARN ±5% >50 ms; FAULT ±10% >10 ms.
	- Encoder/Hall loss: > 50 ms → FAULT (latched) until clear.
	- Watchdog expiry: EMERGENCY.
- Classes: WARN (non‑latching), FAULT (latched until ACK+clear), EMERGENCY (latched until power‑cycle/privileged reset).
- Actions: EMERGENCY disables PWM ≤ 1 ms, engages brake, opens motor relay; FAULT ramps to 0 A ≤ 10 ms then disables ≤ 20 ms.

### 12.7 HMI Requirements
- Views: Status (state, RPM, bus V, current, temperature, version), Faults (active + history), Version/Info, Diagnostics (read‑only).
- Refresh ≥ 10 Hz; state‑to‑screen latency ≤ 200 ms.
- Color semantics: Normal=green, Warning=amber, Fault=red; contrast ≥ 4.5:1.
- Parity with simulation: same labels, flows, and messages (timing tolerance ≤ 10%).

#### 12.7.1 Maintenance Panel (M2)
- View: Maintenance — shows on‑device health score (0–100), advisory category (OK / Check soon / Service required), and top contributing signals (e.g., temp trend, current peaks, fault rate).
- Update rate: ≥ 1 Hz (target 2 Hz) with ≤ 200 ms HMI latency.
- Behavior when ML disabled/unavailable: show “Maintenance advisory not available” and remain functional for other views.
- Simulation parity: same panel and values for a given reference dataset/model.

### 12.8 Updates & Rollback (A/B)
- Channel: USB mass‑storage file drop to /updates.
- Package: signed archive (.pkg) with manifest (version, slot, hash) and payload; ECDSA‑P256 over SHA‑256.
- Dual slots: install to inactive, verify, atomic switch; auto‑rollback on boot failure; power‑loss safe.
- Target: 1 MiB payload installs in ≤ 60 s on reference HW.

### 12.9 Simulation Parity & Fault Injection
- Browser HMI: Chrome/Edge (last 2 versions); layouts 1280×720 and 1920×1080; ≥ 10 Hz updates.
- Parity matrix covers views, commands, messages, and fault/ACK flows.
- Fault injection: overcurrent, undervoltage, overtemp, encoder loss, comms loss, watchdog; via UI toggles and YAML scripts; metrics export CSV/JSON.

### 12.10 Logging & Diagnostics
- Persistent ASCII logs on filesystem; capacity ≥ 1000 entries; ring‑buffer rollover.
- Entry schema: timestamp, severity, category, code, message.
- Taxonomy: ST_BOOT_xx (self‑tests), RT_MON_xx (monitoring), RT_SAFE_xx (safe‑state), CMD_xx (commands), UPD_xx (updates), HMI_xx (UI), SIM_xx (simulation).
- Export bundle over USB (logs + version/slot + checksum); filter by date/category.

### 12.11 Assumptions & Non‑Goals (Demo Scope)
- Assumes BLDC/PMSM‑like control with encoder/Hall feedback available.
- Certification is out‑of‑scope; design aligns with certification‑ready practices.
- No machine learning features in this scope; analytics may be considered later in non‑safety partition.

> Last updated: 2025‑12‑12

### 12.12 Machine Learning & Predictive Maintenance (Planned for M2)

Goal: provide on-device predictive maintenance insights without affecting safety‑critical behavior. ML features run in the non‑safety Application partition and do not gate motion or safe‑state decisions.

Scope (M2):
- Data collection: extend logging/export with telemetry (e.g., RPM, current RMS/peaks, temperature trends, fault rates) at configurable rates suitable for offline analysis and on-device features.
- Dataset export: generate de‑identified CSV/JSON bundles for training; include version and device context.
- Model lifecycle: train models off‑device; package models with semantic versioning and integrity metadata; distribute as part of Application updates (separate from Safety Core).
- On‑device scoring (mandatory): lightweight health score (0–100) and advisory category (OK / Check soon / Service required) computed on device at ≥ 1 Hz (target 2 Hz); advisory only (no impact on Safety Core decisions).
- HMI: present health score/advisories in a dedicated view with top contributing signals; clearly marked as non‑safety information.
- Simulation: reproduce health score behavior using sample models and recorded datasets for parity.

Non‑interference and constraints:
- Safety Core remains authoritative for self‑tests, monitoring, and safe‑state actions.
- ML components cannot disable interlocks or modify thresholds; failure of ML features must not degrade safety behavior.
- Resource limits (reference HW): average CPU ≤ 5%, RAM ≤ 64 KiB, model size ≤ 200 KiB; per‑inference compute ≤ 10 ms.

Acceptance (M2):
- Dataset export covers required signals with documentation; toolchain provided to convert to training format.
- Model package schema defined (version, input features, normalization, checksum); update path validated via A/B Application slot.
- Advisory HMI shows health score and top contributing signals; no control path to Safety Core.
- Simulation parity demonstrates the same advisory outputs for a reference dataset.