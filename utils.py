import math

def sifting(Angles_A, Angles_B, Results_A, Results_B):
    # liste per salvare le chiavi da assegnare ad Alice e Bob
    key_A = []
    key_B = []

    num_meas = len(Angles_A)
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
    num_meas = len(Angles_A)

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

        return abs(S)

    except Exception as e:
        print(f"Errore nel calcolo CHSH: {e}")
        return 0.0
