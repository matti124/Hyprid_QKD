import netsquid as ns
from netsquid.nodes import Node
from netsquid.components.qmemory import QuantumMemory
from netsquid.components.qchannel import QuantumChannel
from netsquid.components.models.qerrormodels import DepolarNoiseModel, FibreLossModel
from Charlie_Protocol import CharlieProtocol
from Alice_Protocol import AliceProtocol
from Bob_Protocol import BobProtocol
from utils import sifting, test_CHSH, sifting_powered, test_CHSH_powered

# Costanti di configurazione
NUM_QUBITS = 5000
DESIDERED_KEY_LENGTH = 128


def setup_network():
    q_error_A = FibreLossModel(p_loss_init=0.05, p_loss_length=0.45)
    q_error_B = FibreLossModel(p_loss_init=0.05, p_loss_length=0.45)
    depolar_noise = DepolarNoiseModel(depolar_rate=0.9)

    q_ch_A = QuantumChannel("C-->A", length=10, models={"quantum_loss_model": q_error_A, "quantum_noise_model": depolar_noise})
    q_ch_B = QuantumChannel("C-->B", length=10, models={"quantum_loss_model": q_error_B, "quantum_noise_model": depolar_noise})
    # 2. Nodo Alice

    mem_A = QuantumMemory("AliceMemory", num_positions=1)
    node_A = Node("Alice", port_names=['qin'], qmemory=mem_A)
    node_A.ports['qin'].forward_input(node_A.qmemory.ports['qin'])
    node_A.ports['qin'].connect(q_ch_A.ports['recv'])

    # 3. Nodo Bob
    mem_B = QuantumMemory("BobMemory", num_positions=1)
    node_B = Node("Bob", port_names=['qin'], qmemory=mem_B)
    node_B.ports['qin'].forward_input(node_B.qmemory.ports['qin'])
    node_B.ports['qin'].connect(q_ch_B.ports['recv'])

    # 4. Nodo Charlie
    node_C = Node("Charlie", port_names=['qout_A', 'qout_B'])
    node_C.ports['qout_A'].connect(q_ch_A.ports['send'])
    node_C.ports['qout_B'].connect(q_ch_B.ports['send'])

    return node_A, node_B, node_C

def E91_run_sim():
    node_A, node_B, node_C = setup_network()

    final_keyA, final_keyB = [], []
    all_anglesA, all_anglesB = [], []
    all_measA, all_measB = [], []
    all_indicesA, all_indicesB = [], []
    iteration = 0

    print(f"Inizio trasmissione. Obiettivo: {DESIDERED_KEY_LENGTH} bit.\n")

    while len(final_keyA) < DESIDERED_KEY_LENGTH:
        # Reset della linea temporale
        ns.sim_reset()

        # Inizializzazione protocolli
        alice_prot = AliceProtocol(node_A, NUM_QUBITS)
        bob_prot = BobProtocol(node_B, NUM_QUBITS)
        charlie_prot = CharlieProtocol(node_C, NUM_QUBITS, 100)

        # Avvio
        alice_prot  .start()
        bob_prot.start()
        charlie_prot.start()
        ns.sim_run()
        print(f"Alice: {len(alice_prot.results_list)} qubit")
        print(f"Bob: {len(bob_prot.results_list)} qubit")

        # Elaborazione risultati
        keyA_batch, keyB_batch = sifting_powered(
            alice_prot.angles_list, bob_prot.angles_list,
            alice_prot.results_list, bob_prot.results_list,
            alice_prot.index_list, bob_prot.index_list
        )

        final_keyA.extend(keyA_batch)
        final_keyB.extend(keyB_batch)
        all_anglesA.extend(alice_prot.angles_list)
        all_anglesB.extend(bob_prot.angles_list)
        all_measA.extend(alice_prot.results_list)
        all_measB.extend(bob_prot.results_list)
        all_indicesA.extend(alice_prot.index_list)
        all_indicesB.extend(bob_prot.index_list)

        iteration += 1
        print(f"Giro {iteration}: Estratti {len(final_keyA)}/{DESIDERED_KEY_LENGTH} bit.")

    # Taglio finale alla lunghezza desiderata
    final_keyA = final_keyA[:DESIDERED_KEY_LENGTH]
    final_keyB = final_keyB[:DESIDERED_KEY_LENGTH]

    # Test CHSH finale su tutto il campione accumulato
    valore_S = test_CHSH_powered(all_anglesA, all_anglesB, all_measA, all_measB, all_indicesA, all_indicesB)

    # ==========================================
    # Calcolo del QBER (Quantum Bit Error Rate)
    # ==========================================
    errori = sum(1 for a, b in zip(final_keyA, final_keyB) if a != b)
    qber_percentuale = (errori / DESIDERED_KEY_LENGTH) * 100

    print("\n" + "=" * 50)
    print("REPORT FINALE TRASMISSIONE")
    print("=" * 50)
    print(f"VALORE CHSH: {round(valore_S, 3)} (Sicurezza superata se >= 2.0)")
    print(f"QBER:        {round(qber_percentuale, 2)}% (Errori nella chiave)")
    print("-" * 50)
    print(f"CHIAVE ALICE: {final_keyA}")
    print(f"CHIAVE BOB:   {final_keyB}")
    print("=" * 50)


if __name__ == "__main__":
    E91_run_sim()