def sifting(Angles_A, Angles_B, Results_A, Results_B):
    

# liste per salvare le chiavi da assegnare ad Alice e Bob
 key_A=[]
 key_B=[]

 num_meas=len(Angles_A)
# Controllo per ogni elemento della lista che abbiano usato stesso angolo, in caso positivo allora per Alice salvo bit corrispondente, mentre per Bob essendo che ho usato stato di bell che produce misurazione opposta sulle due parti, lo devo flippare, ci basta fare 1-x.
 for i in range (num_meas):
      ang_A=round(Angles_A[i],5)
      ang_B=round(Angles_B[i],5)
      if ang_A==ang_B:
          bit_A=Results_A[i]
          key_A.append(bit_A)
          bit_B=Results_B[i]
          key_B.append(1-bit_B)
 return key_A, key_B
    
