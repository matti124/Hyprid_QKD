import netsquid as ns
from netsquid.protocols import NodeProtocol
from netsquid.qubits.operators import create_rotation_op
import math
import random

def RY(theta):
    return create_rotation_op(theta, (0, 1, 0))

class BobProtocol(NodeProtocol):
    
    def __init__(self, node, num_qubits):
        super().__init__(node=node)
        self.num_qubits = num_qubits
        
        # Gli angoli di Bob per l'E91 (diversi da quelli di Alice!)
        self.angles = [math.pi/4, -math.pi/4, 0]
        
        self.results_list = []
        self.angles_list = []

    def run(self):
        for i in range(self.num_qubits):
            # 1. ATTESA EVENTO
            yield self.await_port_input(self.node.qmemory.ports['qin'])

            # 2. ESTRAZIONE: Prendiamo il qubit dalla memoria
            qubit, = self.node.qmemory.pop(0)

            # 3. SCELTA DELLA BASE E ROTAZIONE
            chosen_basis = random.randint(0, 2)
            theta = self.angles[chosen_basis]
            
            # Ruotiamo il qubit solo se l'angolo non è 0
            if theta != 0:
                ns.qubits.operate(qubit, RY(theta))

            # 4. MISURAZIONE
            meas_result, prob = ns.qubits.measure(qubit)
            
            # 5. SALVATAGGIO NEI TACCUINI
            self.results_list.append(meas_result)
            self.angles_list.append(theta)

            # 6. STAMPA A SCHERMO
        print(f"\n\n[BOB] Qubit {i} | Base: {self.angles_list}\n | Risultato: {self.results_list}")

