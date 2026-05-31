from oqs import oqs 

import hashlib

class SignatureWrapper:
    def sign(algo, sk, value):
        with oqs.Signature(algo, sk) as signer:
            hashed_value = SignatureWrapper._hash(value)
            print(f"HASHED VALUE: {hashed_value.hex()}")
            try:
                signature = signer.sign(hashed_value)
            except Exception as signE:
                return signE, None

            return None, signature

    def verify(algo, pk, signature, value):
        with oqs.Signature(algo) as verifier:
            hashed_value = SignatureWrapper._hash(value)
            print(f"HASHED VALUE: {hashed_value.hex()}")
            verified_result = verifier.verify(hashed_value, signature, pk)
            
            return verified_result



    def _hash(value):
        sha3_256 = hashlib.sha3_256()
        sha3_256.update(value)

        return sha3_256.digest()
