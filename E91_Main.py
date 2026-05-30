# PRIMA IMPLEMENTAZIONE DI E91 MANUALE (circa), usando netsquid.
#1. CREAZIONE TOPOLOGIA DI RETE+ DEFINIZIONE DEI COMPONENTI
#2. CREAZIONE DELLE SINGOLE ENTITÀ USANDO COMPONENTI DESCRITTI
#3. IMPLEMENTAZIONE DELLA LOGICA DI COMUNICAZIONE 
#4. IMPLEMENTAZIONE DELLA SIMULAZIONE

import netsquid as ns 
#Importazione componenti fondamentali
from netsquid.nodes import Node
from netsquid.components.qmemory import QuantumMemory
from netsquid.components.qchannel import QuantumChannel
from netsquid.components.cchannel import ClassicalChannel
from netsquid.components import QuantumChannel, Channel
from netsquid.components.models.delaymodels import FibreDelayModel

from Charlie_Protocol import CharlieProtocol
from Alice_Protocol import AliceProtocol
from Bob_Protocol import BobProtocol

from utils import sifting, test_CHSH

NUM_QUBITS=1000
def E91_run_sim():

#Definizione della connessione tra nodi:
    Qchannel_C2A=QuantumChannel("C-->A")
    Qchannel_C2B=QuantumChannel("C-->B")







# ------------------------------------------
# 1. ASSEGNAZIONE COMPONENTI AD ALICE      |
# ------------------------------------------

    memoria_alice = QuantumMemory("AliceMemory", num_positions=1)
    alice = Node("Alice", port_names=['qin_charlie'], qmemory=memoria_alice)

# Forward: tutto ciò che entra in 'qin_charlie' va dritto nella porta 'qin' della memoria
    alice.ports['qin_charlie'].forward_input(alice.qmemory.ports['qin'])
    alice.ports['qin_charlie'].connect(Qchannel_C2A.ports['recv'])
# ------------------------------------------
# 2. ASSEGNAZIONE COMPONENTI A BOB          |
# ------------------------------------------

    memoria_bob = QuantumMemory("BobMemory", num_positions=1)
    bob = Node("Bob", port_names=['qin_charlie'], qmemory=memoria_bob)

# Forward speculare a quello di Alice
    bob.ports['qin_charlie'].forward_input(bob.qmemory.ports['qin'])
    bob.ports['qin_charlie'].connect(Qchannel_C2B.ports['recv'])


#-------------------------------------------
# 3. ASSEGNAZIONE COMPONENTI A CHARLIE      |
#-------------------------------------------
    
    charlie= Node("Charlie", port_names=['qout_A', 'qout_B'])

    charlie.ports['qout_A'].connect(Qchannel_C2A.ports['send'])
    charlie.ports['qout_B'].connect(Qchannel_C2B.ports['send'])

# TEST
    charlie_prot=CharlieProtocol(charlie, NUM_QUBITS,100)
    alice_prot=AliceProtocol(alice, NUM_QUBITS)
    bob_prot=BobProtocol(bob,NUM_QUBITS)

    
    alice_prot.start()
    bob_prot.start()
    charlie_prot.start()

    
    print("Avvio simulazione...\n")
    ns.sim_run()
 
    keyA=[]
    keyB=[]

    keyA,keyB=sifting(alice_prot.angles_list, bob_prot.angles_list, alice_prot.results_list, bob_prot.results_list)

    print(f"\n\nChiavi finali ottenute: \n Chiave Alice-> [{keyA}] \n Chiave Bob-> [{keyB}]" )


    valore_S = test_CHSH(
    alice_prot.angles_list,
    bob_prot.angles_list,
    alice_prot.results_list,
    bob_prot.results_list
)
    print(f"\n\nValore CHSH (S) calcolato: {round(valore_S, 3)}")

if __name__=="__main__":
    E91_run_sim()
