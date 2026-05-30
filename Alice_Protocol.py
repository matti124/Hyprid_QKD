import netsquid as ns
from netsquid.protocols import NodeProtocol
import netsquid.qubits.operators as ops
import random
import math

#LOGICA DI ALICE (bob identica)
#Ogniqualvolta riceve un qubit, mantiene aggiornate due liste:
#   1. Angolo scelto per misurare i-esimo qubit
#   2. Risultato ottenuto da i-esimo qubit misurato
#
#Una volta finita questa parte, Alice e Bob si contattano tramite un canale classico per fare sifting e quindi scegliere bit della chiave 
class AliceProtocol(NodeProtocol):
    def __init__(self, node, num_qubits):
        super().__init__(node=node)
        self.num_qubits = num_qubits
        self.angles=[0, math.pi/4, math.pi/2]
        self.results_list=[]
        self.angles_list=[]
   
    def run(self):
        for i in range(self.num_qubits):
            # 1. ATTESA EVENTO: Alice si mette in pausa finché non entra 
            #    qualcosa nella porta 'qin' della sua memoria
            yield self.await_port_input(self.node.qmemory.ports['qin'])
            
            # 2. ESTRAZIONE: Prendiamo il qubit dalla posizione 0 della memoria
            # Usiamo pop(0) invece di peek(0) così la memoria si svuota!
            qubit, = self.node.qmemory.pop(0)
            
            # STAMPA: Controlliamo il qubit e a che istante di tempo è arrivato
            # print(f"[T={ns.sim_time()} ns] ALICE ha ricevuto: {qubit[0]}")

            chosen_basis=random.randint(0,2)
            theta=self.angles[chosen_basis]
            ns.qubits.operate(qubit, ops.create_rotation_op(theta, (0,1,0)))

            result,prob =ns.qubits.measure(qubit)
            self.results_list.append(result)
            self.angles_list.append(theta)
        
        print(f"\n\n[ALICE] Qubit {i} | Base: {self.angles_list}\n | Risultato: {self.results_list}")
