# Hybrid QKD and PQC Network Simulation

## Overview

This repository provides a comprehensive simulation of a hybrid quantum-safe communication network. It integrates the **E91 Quantum Key Distribution (QKD)** protocol with **Post-Quantum Cryptography (PQC)** mechanisms to establish a secure symmetric session key.

The quantum network operations and entanglement distributions are simulated using [NetSquid](https://netsquid.org/), while the post-quantum key encapsulation and digital signatures are handled by the [liboqs-python](https://github.com/open-quantum-safe/liboqs-python) library.

The ultimate goal is to demonstrate a highly secure communication channel capable of detecting eavesdropping (Man-in-the-Middle) and resisting quantum computer attacks.

---

## Architecture and Cryptographic Suite

The project implements a multi-layered security approach:

1. **Quantum Layer (E91 Protocol)**
   - Entanglement-based key distribution utilizing a central node (Charlie) to generate and distribute Bell states to Alice and Bob.
   - Realistic network modeling using `FibreLossModel` and `DepolarNoiseModel`.

2. **Post-Quantum Layer (PQC)**
   - **Authentication:** `ML-DSA-87` (Module-Lattice-Based Digital Signature Standard) is used to sign and verify public keys and ciphertexts.
   - **Key Encapsulation:** `ML-KEM-1024` (Module-Lattice-Based Key Encapsulation Mechanism) is used to securely exchange a classical shared secret.

3. **Hybrid Key Derivation & Encryption**
   - The quantum key and the PQC shared secret are combined using **HKDF** (with `SHA-384`) to derive the final robust session key.
   - The final payload is encrypted and authenticated using **AES-GCM**.

---

## Repository Structure

| File | Description |
|------|-------------|
| `E91_Main_classic.py` | Main script for the secure environment simulation. Runs the QKD session, executes the PQC exchange, derives the hybrid key, and encrypts a test message. |
| `E91_Main_attacked.py` | Main script demonstrating a network compromised by an active eavesdropper (Eve). Highlights detection via QBER anomalies and CHSH inequality violations. |
| `Alice_Protocol.py & Bob_Protocol.py` | NetSquid node protocol for Alice and Bob. Handles qubit reception, basis selection, and measurement logging. |
| `Charlie_Protocol.py` | The entanglement source. Generates entangled qubit pairs and distributes them. Contains configurations for both secure and MitM-compromised routing. |
| `Eve_Protocol.py` | Implements a Man-in-the-Middle (MitM) attack. Eve intercepts qubits, performs random measurements, and forwards newly generated fake states to Alice. |
| `utils.py` | Core mathematical utility functions, including key sifting (`sifting_powered`) and CHSH value computation (`test_CHSH_powered`). |
| `signature_wrapper.py` | Utility wrapper for `liboqs` to streamline signing and verification using ML-DSA. |
| `requirements.txt` | Python package dependencies required to run the simulation. |

---

## Prerequisites and Installation

Python 3.12 at most is required along with the specified dependencies.

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

> **Note:** The [NetSquid](https://netsquid.org/) package may require a registered account and an accepted academic/commercial license to be installed via their official package index.

---

## Usage

### 1. Secure Environment Simulation

Run the standard protocol without eavesdropping interference:

```bash
python E91_Main_classic.py
```

**Expected output:**
- Continuous generation and extraction of qubits until the target key length (128 bits) is reached.
- A high CHSH score (≥ 2.0) and a low Quantum Bit Error Rate (QBER).
- Successful ML-DSA signature verification and ML-KEM shared secret encapsulation.
- Successful decryption of the final AES-GCM encrypted message.

### 2. Eavesdropper (MitM) Simulation

Simulate a network actively attacked by Eve:

```bash
python E91_Main_attacked.py
```

**Expected output:**
- Detection of a critical drop in the CHSH value (< 2.0) alongside a high QBER (≥ 30%).
- A `MAN IN THE MIDDLE DETECTED` alert is triggered.
- The system discards the quantum key and automatically falls back to deriving the AES session key solely from the PQC shared secret, ensuring the final message remains secure.

---

## Simulation Design Notes

- **Time-Stepped Execution:** To prevent index inconsistencies during key sifting across multiple qubit batches, the simulation advances the NetSquid clock in predefined durations (`STEP_DURATION`). This ensures accurate qubit indexing for robust CHSH calculations.
- **Educational Context:** This implementation is designed for academic demonstration of Quantum Networking and Security concepts, highlighting the synergy between quantum physics and post-quantum cryptography.

---

## Contributors

<a href="https://github.com/matti124/Hyprid_QKD/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=matti124/Hyprid_QKD" />
</a>
