import netsquid as ns
from netsquid.protocols import NodeProtocol
import netsquid.qubits.operators as ops
import math
import random

#LOGICA DI EVE:
# Si tratta di un semplice MitM, per simularlo, nella topologia di rete dobbiamo creare un intermezzo nella comunicazione tra ad esempio Charlie ed Alice, ottenendo Charlie-->Eve-->Alice.
#Obiettivo di Eve è:
#   1. Riuscire ad intercettare i qubit entanglati con quelli che riceve Bob così poi da computare stessa chiave,
#      sceglie in maniera randomica stesse basi che utilizza Alice sperando di azzeccarne qualcuna 
#   2. simulare qubit entanglati verso Alice così che non si renda conto che comunicazione compromessa


class EveProtocol(NodeProtocol):
    def __init__(self, node):
        super().__init__(node=node)
        self.angles = [0, math.pi/2, math.pi/4]
        self.port_E2A=self.node.ports['qout_A']
        self.results_list=[]
        self.angles_list=[]
        self.index_list=[]

    def run(self):
        while True:
            yield self.await_port_input(self.node.qmemory.ports['qin'])

            qubit_stolen, = self.node.qmemory.pop(0)
 # in questo modo ha indice dei qubit che ha rubato per poi riuscire a sincronizzarsi con Bob in fase di sifting tra Alice ed egli.
            indice_qubit=round(ns.sim_time() / 100) 
            self.index_list.append(indice_qubit)
# fa esatta operazione che farebbe alice per cercare di ottenere stessa misurazione di Bob
            chosen_basis = random.randint(0,2)
            theta=self.angles[chosen_basis]
            ns.qubits.operate(qubit_stolen, ops.create_rotation_op(theta, (0,1,0)))
            
# effettua misurazione e salva risultato ed angoli usati
            result_stolen, prob = ns.qubits.measure(qubit_stolen)
            self.results_list.append(result_stolen)
            self.angles_list.append(theta)

# Ora che è stata effettuata misurazione il qubit rubato collassa, quindi simuliamolo anche in netsquid
            ns.qubits.discard(qubit_stolen)

# Infine genera un nuovo qubit casuale che manda ad Alice 
            fake_qubit=ns.qubits.create_qubits(1)
# Per tentare di nascondersi, Eve tenterà di mandare ad Alice un qubit che misurato nella stessa base che ha usato lui potrà permetterle di ottenere anche lei stesso risultato. Ciò è fondamentale per Eve, poichè in questo modo riesce diminuire le possibilità che Alice scegliendo qualsiasi base ottenga risultato differente e che quindiQBER si alzi troppo .
            if result_stolen == 1:
                ns.qubits.operate(fake_qubit, ns.X)

            ns.qubits.operate(fake_qubit, ops.create_rotation_op(theta, (0,1,0)))

            self.port_E2A.tx_output(fake_qubit)

    def get_and_clear_buffers(self):
        """Metodo per il master script per analizzare i dati rubati da Eve e svuotare i buffer"""
        data = (self.index_list.copy(), self.results_list.copy(), self.angles_list.copy())
        self.index_list.clear()
        self.results_list.clear()
        self.angles_list.clear()
        return data
