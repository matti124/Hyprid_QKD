import math

def sifting(Angles_A, Angles_B, Results_A, Results_B):
    # liste per salvare le chiavi da assegnare ad Alice e Bob
    key_A = []
    key_B = []

    num_meas = min(len(Angles_A), len(Angles_B))
    # Controllo per ogni elemento della lista che abbiano usato stesso angolo...
    for i in range(num_meas):
        ang_A = round(Angles_A[i], 5)
        ang_B = round(Angles_B[i], 5)

        if ang_A == ang_B:
            bit_A = Results_A[i]
            key_A.append(bit_A)

            bit_B = Results_B[i]
            key_B.append(1 - bit_B)

    return key_A, key_B


def test_CHSH(Angles_A, Angles_B, Results_A, Results_B):
    #Coppie di angoli fondamentali per calcolare metrica
    coppie_chsh = [
        (0.0, math.pi / 4),
        (0.0, 3 * math.pi / 4),
        (math.pi / 2, math.pi / 4),
        (math.pi / 2, 3 * math.pi / 4)
    ]
    # 1. Convertiamo i bit classici in spin fisici (+1 e -1), dunque se bit era 0 -> 1 mentre 1 -> -1
    spins_A = [1 if r == 0 else -1 for r in Results_A]
    spins_B = [1 if r == 0 else -1 for r in Results_B]

    somma_prodotti = {}
    conteggi = {}
    num_meas = min(len(Angles_A), len(Angles_B))

    # 2. Raggruppiamo i risultati per ogni coppia di angoli usata
    for i in range(num_meas):
        ang_A = Angles_A[i]
        ang_B = Angles_B[i]
        coppia = (ang_A, ang_B)
        if coppia in coppie_chsh:
            prodotto = spins_A[i] * spins_B[i]

            if coppia not in somma_prodotti: #se coppia di angoli non presente l'aggiungo
                somma_prodotti[coppia] = 0
                conteggi[coppia] = 0

            somma_prodotti[coppia] += prodotto #somma di +1 e -1
            conteggi[coppia] += 1 #numero di occorrenze di quella coppia

    # 3. Calcoliamo il Valore di Aspettazione (E) per ogni coppia
    E = {}
    for coppia in somma_prodotti:
        E[coppia] = somma_prodotti[coppia] / conteggi[coppia] #classica media

    # 4. Estraiamo le 4 medie usando la libreria math pura
    try:
        E_1 = E.get((0, math.pi / 4), 0)
        E_2 = E.get((0, 3 * math.pi / 4), 0)
        E_3 = E.get((math.pi / 2, math.pi / 4), 0)
        E_4 = E.get((math.pi / 2, 3 * math.pi / 4), 0)

        # 5. La Formula di CHSH
        S = E_1 - E_2 + E_3 + E_4
        print(f"E1={E_1:.3f}, E2={E_2:.3f}, E3={E_3:.3f}, E4={E_4:.3f}")
        print(f"Coppie trovate: {list(somma_prodotti.keys())}")
        return abs(S)

    except Exception as e:
        print(f"Errore nel calcolo CHSH: {e}")
        return 0.0

# Fortemente aiutato da AI per creazione del dizionario indicizzato
def sifting_powered(Angles_A, Angles_B, Results_A, Results_B, Indices_A, Indices_B):
    key_A = []
    key_B = []

    # Costruiamo un dizionario per Alice: indice -> (angolo, risultato)
    # Così possiamo accedere rapidamente ai dati di un qubit specifico tramite il suo indice
    dict_A = {idx: (ang, res) for idx, ang, res in zip(Indices_A, Angles_A, Results_A)}

    # Stessa cosa per Bob
    dict_B = {idx: (ang, res) for idx, ang, res in zip(Indices_B, Angles_B, Results_B)}

    # Troviamo gli indici dei qubit ricevuti da ENTRAMBI Alice e Bob
    # set() crea un insieme di indici, & trova l'intersezione tra i due insiemi
    # Se Alice ha perso il qubit 2 e Bob ha perso il qubit 5,
    # common conterrà solo gli indici dove nessuno dei due ha avuto perdite
    common = set(dict_A.keys()) & set(dict_B.keys())

    # Per ogni qubit ricevuto da entrambi, in ordine crescente di indice
    for idx in sorted(common):
        ang_A, res_A = dict_A[idx]
        ang_B, res_B = dict_B[idx]

        # Sifting: teniamo solo i risultati dove Alice e Bob hanno usato la stessa base
        if round(ang_A, 5) == round(ang_B, 5):
            key_A.append(res_A)
            key_B.append(1 - res_B)

    return key_A, key_B



def test_CHSH_powered(Angles_A, Angles_B, Results_A, Results_B, Indices_A, Indices_B):
    coppie_chsh = [
        (0.0, math.pi / 4),
        (0.0, 3 * math.pi / 4),
        (math.pi / 2, math.pi / 4),
        (math.pi / 2, 3 * math.pi / 4)
    ]

    # Costruiamo dizionari indicizzati per sincronizzare le misure
    dict_A = {idx: (ang, res) for idx, ang, res in zip(Indices_A, Angles_A, Results_A)}
    dict_B = {idx: (ang, res) for idx, ang, res in zip(Indices_B, Angles_B, Results_B)}

    # Solo qubit ricevuti da entrambi
    common = set(dict_A.keys()) & set(dict_B.keys())

    # Convertiamo i bit in spin fisici (+1 e -1)
    somma_prodotti = {}
    conteggi = {}

    for idx in sorted(common):
        ang_A, res_A = dict_A[idx]
        ang_B, res_B = dict_B[idx]
        coppia = (ang_A, ang_B)

        if coppia in coppie_chsh:
            spin_A = 1 if res_A == 0 else -1
            spin_B = 1 if res_B == 0 else -1
            prodotto = spin_A * spin_B

            if coppia not in somma_prodotti:
                somma_prodotti[coppia] = 0
                conteggi[coppia] = 0

            somma_prodotti[coppia] += prodotto
            conteggi[coppia] += 1

    E = {}
    for coppia in somma_prodotti:
        E[coppia] = somma_prodotti[coppia] / conteggi[coppia]

    try:
        E_1 = E.get((0, math.pi / 4), 0)
        E_2 = E.get((0, 3 * math.pi / 4), 0)
        E_3 = E.get((math.pi / 2, math.pi / 4), 0)
        E_4 = E.get((math.pi / 2, 3 * math.pi / 4), 0)

        S = -E_1 + E_2 - E_3 - E_4
        return abs(S)

    except Exception as e:
        print(f"Errore nel calcolo CHSH: {e}")
        return 0.0
