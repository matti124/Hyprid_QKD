import netsquid as ns
from netsquid.nodes import Node
from netsquid.components.qmemory import QuantumMemory
from netsquid.components.qchannel import QuantumChannel

from Charlie_Protocol import CharlieProtocol
from Alice_Protocol import AliceProtocol
from Bob_Protocol import BobProtocol
from utils import sifting, test_CHSH

# Costanti
NUM_QUBITS = 1
DESIDERED_KEY_LENGTH = 128


def setup_network():                    
    # 1. Definizione canali
    q_ch_A = QuantumChannel("C-->A")
    q_ch_B = QuantumChannel("C-->B")

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
    iteration = 0

    print(f"Inizio trasmissione. Obiettivo: {DESIDERED_KEY_LENGTH} bit.\n")
    
#Finchè non raggiungo chiave di lunghezza desiderata effettuo nuovi scambi di Alice e Bob con Charlie. Nel frattempo all'interno del ciclo comunque mi salvo le parti di chiave finale generate, gli angoli e misurazioni di Alice e Bob. Gli angoli e le misurazioni sono necessarie per calcolare la metrica CHSH.

    while len(final_keyA) < DESIDERED_KEY_LENGTH:
        # Reset della linea temporale
        ns.sim_reset()

        # Inizializzazione protocolli (vengono creati nuovi ogni giro)
        alice_prot = AliceProtocol(node_A, NUM_QUBITS)
        bob_prot = BobProtocol(node_B, NUM_QUBITS)
        charlie_prot = CharlieProtocol(node_C, NUM_QUBITS, 100)

        # Avvio
        alice_prot.start()
        bob_prot.start()
        charlie_prot.start()
        ns.sim_run()

        # Elaborazione risultati
        keyA_batch, keyB_batch = sifting(
            alice_prot.angles_list, bob_prot.angles_list,
            alice_prot.results_list, bob_prot.results_list
        )

        final_keyA.extend(keyA_batch)
        final_keyB.extend(keyB_batch)
        all_anglesA.extend(alice_prot.angles_list)
        all_anglesB.extend(bob_prot.angles_list)
        all_measA.extend(alice_prot.results_list)
        all_measB.extend(bob_prot.results_list)

        iteration += 1
        print(f"Giro {iteration}: Estratti {len(final_keyA)}/{DESIDERED_KEY_LENGTH} bit.")

    # Taglio finale alla lunghezza desiderata
    final_keyA = final_keyA[:DESIDERED_KEY_LENGTH]

    # Test CHSH finale su tutto il campione accumulato
    valore_S = test_CHSH(all_anglesA, all_anglesB, all_measA, all_measB)

    print("\n" + "=" * 40)
    print(f"CHIAVE GENERATA: {len(final_keyA)} bit")
    print(f"VALORE CHSH FINALE: {round(valore_S, 3)}")
    print("=" * 40)


if __name__ == "__main__":
    E91_run_sim()
