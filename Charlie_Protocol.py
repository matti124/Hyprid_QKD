# PROTOCOLLO DI CHARLIE
# FUNZIONE-> deve creare coppie di qubit entanglati in stato di Bell ed inoltrarli verso Alice e Bob
# IMPLEMENTAZIONE-> dovrebbe essere una subroutine del main, quindi main lo chiama e lui parte mandando il tutto


import netsquid as ns 
from netsquid.protocols import NodeProtocol


#  - SIMULAZIONE CON EVE->  DA COMMENTARE RIGA 18 E 31
#  - SIMULAZIONE CLASSICA-> DA COMMENTARE RIGA 20 E 32


class CharlieProtocolClassic(NodeProtocol):
    
    def __init__(self,node, interval):
        super().__init__(node=node)
        self.interval=interval
        self.port_C2A=self.node.ports['qout_A']
        self.port_C2B=self.node.ports['qout_B']

    def run(self):
        while True:
            qA,qB=ns.qubits.create_qubits(2)

            ns.qubits.operate(qA, ns.H)   
            ns.qubits.operate([qA,qB], ns.CX)
            ns.qubits.operate(qB, ns.X)
            ns.qubits.operate(qB, ns.Z)

            self.port_C2A.tx_output(qA)
            self.port_C2B.tx_output(qB)


            yield self.await_timer(self.interval)


class CharlieProtocolAttack(NodeProtocol):

        def __init__(self, node, interval):
            super().__init__(node=node)
            self.interval = interval
            self.port_C2B = self.node.ports['qout_B']
            self.port_C2E=self.node.ports['qout_E'] # per simulazione di MitM

        def run(self):
            while True:
                qA, qB = ns.qubits.create_qubits(2)

                ns.qubits.operate(qA, ns.H)
                ns.qubits.operate([qA, qB], ns.CX)
                ns.qubits.operate(qB, ns.X)
                ns.qubits.operate(qB, ns.Z)

                self.port_C2E.tx_output(qA) #quando si vuole simulare presenza di Eve
                self.port_C2B.tx_output(qB)

                yield self.await_timer(self.interval)
