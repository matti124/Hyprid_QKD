import netsquid as ns
from netsquid.nodes import Node
from netsquid.components.qmemory import QuantumMemory
from netsquid.components.qchannel import QuantumChannel
from netsquid.components.models.qerrormodels import DepolarNoiseModel, FibreLossModel
from Charlie_Protocol import CharlieProtocolAttack
from Alice_Protocol import AliceProtocol
from Bob_Protocol import BobProtocol
from Eve_Protocol import EveProtocol
from utils import sifting, test_CHSH, sifting_powered, test_CHSH_powered

import oqs
import os
import numpy as np

from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from signature_wrapper import SignatureWrapper


# Costanti di configurazione
STEP_DURATION = 50000
DESIDERED_KEY_LENGTH = 128


def setup_network():
    # 1. definizione dei modelli di errore e dei canali per topologia di rete
    q_error_A = FibreLossModel(p_loss_init=0.4, p_loss_length=0.45)
    q_error_B = FibreLossModel(p_loss_init=0.4, p_loss_length=0.45)
    depolar_noise = DepolarNoiseModel(depolar_rate=0.4)

    # q_ch_A = QuantumChannel("C-->A", length=10, models={"quantum_loss_model": q_error_A, "quantum_noise_model": depolar_noise})
    q_ch_B = QuantumChannel("C-->B", length=10,
                            models={"quantum_loss_model": q_error_B, "quantum_noise_model": depolar_noise})

    # canale per simulazione di Eve come Man in the Middle
    #    CHARLIE-->EVE-->ALICE
    q_ch_E = QuantumChannel("C-->E", length=5, models={"quantum_loss_model": q_error_A})
    q_ch_E1 = QuantumChannel("E-->A", length=5, models={"quantum_loss_model": q_error_A})

    # 2. Nodo Alice
    mem_A = QuantumMemory("AliceMemory", num_positions=1)
    node_A = Node("Alice", port_names=['qin'], qmemory=mem_A)
    node_A.ports['qin'].forward_input(node_A.qmemory.ports['qin'])
    # node_A.ports['qin'].connect(q_ch_A.ports['recv']) # non la connettiamo in quanto simuliamo che riceve da Eve
    node_A.ports['qin'].connect(q_ch_E1.ports['recv'])

    # 3. Nodo Bob
    mem_B = QuantumMemory("BobMemory", num_positions=1)
    node_B = Node("Bob", port_names=['qin'], qmemory=mem_B)
    node_B.ports['qin'].forward_input(node_B.qmemory.ports['qin'])
    node_B.ports['qin'].connect(q_ch_B.ports['recv'])

    # 4. Nodo Charlie
    node_C = Node("Charlie", port_names=['qout_A', 'qout_B', 'qout_E'])
    # node_C.ports['qout_A'].connect(q_ch_A.ports['send']) # in quanto comunicazione è -->Eve-->Alice
    node_C.ports['qout_B'].connect(q_ch_B.ports['send'])
    node_C.ports['qout_E'].connect(q_ch_E.ports['send'])  # canele E per ricevere da Charlie ed E1 per mandare ad A

    # 5. Nodo Eve
    mem_E = QuantumMemory("EveMemory", num_positions=1)
    node_E = Node("Eve", port_names=['qin', 'qout_A'], qmemory=mem_E)  # FIX: aggiunto qmemory=mem_E
    node_E.ports['qout_A'].connect(q_ch_E1.ports['send'])
    node_E.ports['qin'].connect(q_ch_E.ports['recv'])
    node_E.ports['qin'].forward_input(node_E.qmemory.ports['qin'])

    return node_A, node_B, node_C, node_E


 # NUOVA LOGICA DI ESECUZIONE:
 # PRIMA:
 # Veniva dato un numero di qubits totale e i protocolli lavoravano in funzione di esso, ovvero:
 #  - Charlie: ogni tot tempo mandava coppia di qubit entanglati fin quando non mandava esattamente NUM_QUBITS
 #  - Alice e Bob: effettuavano le loro operazioni di misurazioni aspettando input da Charlie fin quando non misuravano NUM_QUBITS
 #  - Eve: stessa logica di Alice e Bob
 # Problema: se batch di qubits su cui iterare era piccolo e quindi per computare chiave di lunghezza desiderata vi era bisogno di
 #          più iterazioni, si creava una discrepanza tra indici, in quanto ogni qualvolta si terminava computazione su quel batch
 #          nel main vi era necessità di resettare simulazione affinché si potessero avviare nuovamente i protocolli
 #          Questo reset andava ovviamente ad azzerare timer di simulazione, che risulta essere fondamentale per computazione degli
 #          indici dei qubit ricevuti dai soggetti.
 #          Dunque si andava a riscrivere sopra gli indici già presenti ottenendo inconsistenza, ciò incideva particolarmente sul test
 #          CHSH dove si otteneva score bassissimo quando si sceglieva size del Batch bassa.
 #
 # DOPO:
 # Per risolvere problematica si è cambiato approccio, piuttosto che ragionare in funzione di batch, per computazione della chiave desiderata
 # facciamo scorrere tempo di simulazione a step predefiniti, per fare ciò sono stati modificati anche i protocoll in modo tale che
 # essi continuino ciclo di computazione finché non vengono stoppati dal main una volta raggiunta chiave di lunghezza desiderata, in
 # questo modo senza dover fare reset e senza dover computare un numero immenso di qubit rispetto a quanti effettivamente ce ne servono
 # riusciamo mantenere consistente valori delle liste e dunque un valore di CHSH accurato


def E91_run_sim():
    ns.sim_reset()
    node_A, node_B, node_C, node_E = setup_network()

    final_keyA, final_keyB = [], []
    all_anglesA, all_anglesB = [], []
    all_measA, all_measB = [], []
    all_indicesA, all_indicesB = [], []
    all_eve_results = []
    all_eve_indices = []
    all_eve_angles = []
    iteration = 0

    print(f"Inizio trasmissione. Obiettivo: {DESIDERED_KEY_LENGTH} bit.\n")

    # Inizializzazione protocolli (Eseguita una sola volta prima del ciclo)
    alice_prot = AliceProtocol(node_A)
    bob_prot = BobProtocol(node_B)
    charlie_prot = CharlieProtocolAttack(node_C, interval=100)
    eve_prot = EveProtocol(node_E)

    # Avvio
    alice_prot.start()
    bob_prot.start()
    charlie_prot.start()
    eve_prot.start()

    while len(final_keyA) < DESIDERED_KEY_LENGTH:
        # Avanzamento della linea temporale (senza azzerare)
        ns.sim_run(duration=STEP_DURATION)

        # Estrazione e pulizia dei buffer in tempo reale dai nodi
        idxA, resA, angA = alice_prot.get_and_clear_buffers()
        idxB, resB, angB = bob_prot.get_and_clear_buffers()
        idxE, resE, angE = eve_prot.get_and_clear_buffers()

        print(f"Alice: {len(resA)} qubit (in questo blocco)")
        print(f"Bob: {len(resB)} qubit (in questo blocco)")

        # Elaborazione risultati
        keyA_batch, keyB_batch = sifting_powered(
            angA, angB,
            resA, resB,
            idxA, idxB
        )

        final_keyA.extend(keyA_batch)
        final_keyB.extend(keyB_batch)
        all_anglesA.extend(angA)
        all_anglesB.extend(angB)
        all_measA.extend(resA)
        all_measB.extend(resB)
        all_indicesA.extend(idxA)
        all_indicesB.extend(idxB)

        all_eve_indices.extend(idxE)
        all_eve_results.extend(resE)
        all_eve_angles.extend(angE)

        iteration += 1
        print(f"Giro {iteration}: Estratti {len(final_keyA)}/{DESIDERED_KEY_LENGTH} bit.")

    # Interruzione dei protocolli a obiettivo raggiunto
    alice_prot.stop()
    bob_prot.stop()
    charlie_prot.stop()
    eve_prot.stop()

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

    # Filtriamo i risultati di Eve solo per gli indici che Alice e Bob hanno effettivamente tenuto
    eve_key = []
    for idx, res in zip(all_eve_indices, all_eve_results):  # FIX: usa le liste accumulate, non eve_prot (fuori scope)
        if idx in all_indicesA:  # Se l'indice è tra quelli che Alice e Bob hanno scambiato
            eve_key.append(res)

    # Contiamo quanti bit Eve ha indovinato correttamente (QBER di Eve rispetto ad Alice)
    bit_corretti_eve = sum(1 for e, a in zip(eve_key, final_keyA) if e == a)
    percentuale_successo = (bit_corretti_eve / len(final_keyA)) * 100 if len(final_keyA) > 0 else 0

    print(f"\n--- ANALISI ATTACCO EVE ---")
    print(f"Bit totali rubati da Eve: {len(eve_key)}")
    print(f"Bit corretti (uguali ad Alice): {bit_corretti_eve}")
    print(f"Efficacia dell'attacco: {round(percentuale_successo, 2)}%")


#==========================================================
# FASE DI ANALISI PER COMPRENDERE SE COMUNICAZIONE ALTERATA
#==========================================================
    verified_attack= False
    if qber_percentuale>=30 and  valore_S<=2:
        print("\n" + "=" * 50)
        print("RILEVATO MAN IN THE MIDDLE!")
        print("=" * 50)
        verified_attack= True


#=========
# PQC
#=========
    ML_DSA = "ML-DSA-87"
    ML_KEM = "ML-KEM-1024"

    generatorMLKEMBOB = oqs.KeyEncapsulation("ML-KEM-1024")
    generatorMLDSABOB = oqs.Signature("ML-DSA-87")
    ml_kem_bob_pk = generatorMLKEMBOB.generate_keypair()
    ml_kem_bob_sk = generatorMLKEMBOB.export_secret_key()

    ml_dsa_bob_pk = generatorMLDSABOB.generate_keypair()
    ml_dsa_bob_sk = generatorMLDSABOB.export_secret_key()

    print("\n" + "=" * 40)
    print(f"CHIAVE PUBBLICA ML-KEM DI BOB :{len(ml_kem_bob_pk)} Byte")
    print(f"CHIAVE PUBBLICA ML-DSA DI BOB :{len(ml_dsa_bob_pk)} Byte")
    print("=" * 40)

    generatorMLDSAALICE = oqs.Signature("ML-DSA-87")
    generatorMLKEMALICE = oqs.KeyEncapsulation(ML_KEM)
    ml_dsa_alice_pk = generatorMLDSAALICE.generate_keypair()
    ml_dsa_alice_sk = generatorMLDSAALICE.export_secret_key()

    print("\n" + "=" * 40)
    print(f"CHIAVA PUBBLICA ML-DSA DI ALICE :{len(ml_dsa_alice_pk)} Byte")
    print(f"INIZIO PRTOCOLLO DI SCAMBIO CHIAVI PQC")
    print("=" * 40)

    print(f"BOB FIRMA LA SUA CHIAVE PUBBLICA ML-KEM con ML-DSA")
    err, signature = SignatureWrapper.sign(ML_DSA, ml_dsa_bob_sk, ml_kem_bob_pk)
    if err is not None:
        print(err)
        return

    print("ALICE RICEVE LA CHIAVE PUBBLICA DI BOB E NE VERIFICA LA FIRMA")
    verified_result = SignatureWrapper.verify(ML_DSA, ml_dsa_bob_pk, signature, ml_kem_bob_pk)

    if not verified_result:
        print("MITM DURANTE LA FASE DI SCAMBIO CHIAVI PQC! COMUNICAZIONE INTERROTTA\n")
        return

    cipher_text, shared_secret_alice = generatorMLKEMALICE.encap_secret(ml_kem_bob_pk)

    print("ALICE FIRMA DIGITALMENTE IL CIPHERTEXT PRIMA DI INVIARLO")

    err, signature_ciphertext = SignatureWrapper.sign(ML_DSA, ml_dsa_alice_sk, cipher_text)
    if err is not None:
        print(err)
        return

    print("BOB RICEVE IL CIPHERTEX E NE VERIFICA LA FIRMA")
    verified_result = SignatureWrapper.verify(ML_DSA, ml_dsa_alice_pk, signature_ciphertext, cipher_text)

    if not verified_result:
        print("MITM DURANTE LA FASE DI SCAMBIO CHIAVI PQC! COMUNICAZIONE INTERROTTA\n")
        return

    shared_secret_bob = generatorMLKEMBOB.decap_secret(cipher_text)

    print("\n" + "=" * 40)
    print(f"SCAMBIO CHIAVI PQC FRA ALICE E BOB ULTIMATO CON SUCCESSO")
    print(f"SEGRETO CONDIVISO PQC BOB: {shared_secret_bob.hex()}")
    print(f"SEGRETO CONDIVISO PQC ALICE: {shared_secret_alice.hex()}")
    print("=" * 40)

    if not verified_attack:
        print(f"ALICE DERIVA LA CHIAVE IBRIDA")
        salt = os.urandom(32)
        hkdf = HKDF(
        algorithm=hashes.SHA384(),
        length=32,
        salt=salt,
        info=b"QKD-PQC-KEM-v1"
        )
        final_keyA_byte = np.packbits(final_keyA).tobytes()
        session_key_alice = hkdf.derive(shared_secret_alice + final_keyA_byte)

        print(f"BOB DERIVA LA CHIAVE IBRIDA")

        hkdf = HKDF(
            algorithm=hashes.SHA384(),
            length=32,
            salt=salt,
            info=b"QKD-PQC-KEM-v1"
        )

        final_keyB_byte = np.packbits(final_keyB).tobytes()
        session_key_bob = hkdf.derive(shared_secret_bob + final_keyB_byte)
        print("\n" + "=" * 40)
        print(f"CHIAVE IBRIDA DI SESSIONE DERIVATA CON SUCCESSO")
        print(f"CHIAVE IBRIDA DI BOB: {session_key_bob.hex()}")
        print(f"CHIAVE IBRIDA DI ALICE: {session_key_alice.hex()}")
        print("=" * 40)

        print("INIZIALIZZO AES_GCM")
        aesgcmBOB = AESGCM(session_key_bob)
        nonce = os.urandom(12)
        ciphertext = aesgcmBOB.encrypt(nonce,
                                "Buonasera Prof. Esposito! Saluti da Jacopo e Mattia, studenti del corso di TQS".encode(
                                    "utf-8"), None)

        aesgcmALICE = AESGCM(session_key_alice)
        plaintext = aesgcmALICE.decrypt(nonce, ciphertext, None)

        print("\n" + "=" * 40)
        print(f"MESSAGGIO CIFRATO: {ciphertext.hex()}")
        print(f"MESSAGGIO DECIFRATO: {plaintext.decode('utf-8')}")  # FIX: virgolette singole dentro f-string
        print("=" * 40)
    else:
        print("\n" + "=" * 40)
        print("Comunicazione su canale quantistico intercettata!\n")
        print("Chiave di sessione derivata unicamente da PQC")
        print("\n" + "=" * 40)

        print("INIZIALIZZO AES_GCM")
        session_key_bob=shared_secret_bob
        session_key_alice=shared_secret_alice
        aesgcmBOB = AESGCM(session_key_bob)
        nonce = os.urandom(12)
        ciphertext = aesgcmBOB.encrypt(nonce,
                                "Buonasera Prof. Esposito! Saluti da Jacopo e Mattia, studenti del corso di TQS".encode(
                                    "utf-8"), None)

        aesgcmALICE = AESGCM(session_key_alice)
        plaintext = aesgcmALICE.decrypt(nonce, ciphertext, None)

        print("\n" + "=" * 40)
        print(f"MESSAGGIO CIFRATO: {ciphertext.hex()}")
        print(f"MESSAGGIO DECIFRATO: {plaintext.decode('utf-8')}")  # FIX: virgolette singole dentro f-string
        print("=" * 40)

if __name__ == "__main__":
    E91_run_sim()