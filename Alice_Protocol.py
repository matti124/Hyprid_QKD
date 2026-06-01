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
    def __init__(self, node):
        super().__init__(node=node)
        self.angles=[0, math.pi/2, math.pi/4]
        self.index_list=[] # Lista fondamentale per mantenimento degli indici dei qubit ricevuti
        self.results_list=[]
        self.angles_list=[]
   
    def run(self):
        while True:
            # 1. ATTESA EVENTO: Alice si mette in pausa finché non entra qubit
            yield self.await_port_input(self.node.qmemory.ports['qin'])
            
            # 2. ESTRAZIONE: Prendiamo il qubit dalla posizione 0 della memoria
            qubit, = self.node.qmemory.pop(0)

            # SALVATAGGIO DELL'INDICE, sfruttiamo il tempo di simulazione per effettivamente ottenere indice, ad esempio
            # ns.sim_time=900ns --> indice: 900/100=9 sarebbe nono qubit, questo perchè Charlie settato con intervallo di
            # inoltro a 100ns
            indice = round(ns.sim_time() / 100)
            self.index_list.append(indice)

            # STAMPA: Controlliamo il qubit e a che istante di tempo è arrivato
            # print(f"[T={ns.sim_time()} ns] ALICE ha ricevuto: {qubit[0]}")

            chosen_basis=random.randint(0,2)
            theta=self.angles[chosen_basis]
            ns.qubits.operate(qubit, ops.create_rotation_op(theta, (0,1,0)))

            result,prob =ns.qubits.measure(qubit)
            self.results_list.append(result)
            self.angles_list.append(theta)
            print(f"\n\n[ALICE] Qubit {indice} | Base: {self.angles_list}\n | Risultato: {self.results_list}")

    
    def get_and_clear_buffers(self):
        """Metodo per estrarre i dati raccolti finora e svuotare i buffer"""
        data = (self.index_list.copy(), self.results_list.copy(), self.angles_list.copy())
        self.index_list.clear()
        self.results_list.clear()
        self.angles_list.clear()
        return data
