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
