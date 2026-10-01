import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cipher import TENUN128Cipher


def test_cipher():
    master_key = bytes(range(16))            
    plaintext = b"LOREM IPSUM SIAM"    

    cipher = TENUN128Cipher(master_key)
    ciphertext = cipher.encrypt_block(plaintext)
    decrypted = cipher.decrypt_block(ciphertext)

    print("plaintext :", plaintext.hex())
    print("ciphertext:", ciphertext.hex())
    print("decrypted :", decrypted.hex())

    assert decrypted == plaintext, f"Hasil Dekripsi tidak sesuai: {decrypted} != {plaintext}"
    print("CIPHER BERHASIL")


if __name__ == "__main__":
    test_cipher()
