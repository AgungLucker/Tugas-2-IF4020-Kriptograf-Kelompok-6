from core.cipher import TENUN128Cipher
from .padding import BLOCK_SIZE, pad, unpad

MODES = ("ECB", "CBC", "CFB", "OFB", "CTR")


def xor_bytes(left: bytes, right: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(left, right))


def _transform(data: bytes, key: bytes, mode: str, iv: bytes | None, decrypting: bool) -> bytes:
    cipher = TENUN128Cipher(key)
    mode = mode.upper()
    if mode not in MODES:
        raise ValueError(f"Mode tidak dikenal: {mode}.")
    if mode == "ECB":
        if iv is not None:
            raise ValueError("ECB tidak memakai IV/counter.")
    elif iv is None or len(iv) != BLOCK_SIZE:
        raise ValueError("IV/counter harus tepat 16 byte.")

    if mode in ("ECB", "CBC"):
        if decrypting:
            if not data or len(data) % BLOCK_SIZE:
                raise ValueError("Ciphertext ECB/CBC harus berisi blok lengkap dan tidak kosong.")
        else:
            data = pad(data)

    feedback = iv
    counter = int.from_bytes(iv, "big") if mode == "CTR" else 0
    block_count = (len(data) + BLOCK_SIZE - 1) // BLOCK_SIZE
    if mode == "CTR" and counter + block_count > 1 << 128:
        raise ValueError("Counter CTR akan melampaui 128 bit; pilih counter awal lain.")

    result = bytearray()
    for offset in range(0, len(data), BLOCK_SIZE):
        block = data[offset:offset + BLOCK_SIZE]
        if mode == "ECB":
            transformed = cipher.decrypt_block(block) if decrypting else cipher.encrypt_block(block)
        elif mode == "CBC":
            if decrypting:
                transformed = xor_bytes(cipher.decrypt_block(block), feedback)
                feedback = block
            else:
                transformed = cipher.encrypt_block(xor_bytes(block, feedback))
                feedback = transformed
        elif mode == "CFB":
            transformed = xor_bytes(block, cipher.encrypt_block(feedback))
            feedback = block if decrypting else transformed
        elif mode == "OFB":
            feedback = cipher.encrypt_block(feedback)
            transformed = xor_bytes(block, feedback)
        else:
            transformed = xor_bytes(block, cipher.encrypt_block(counter.to_bytes(16, "big")))
            counter += 1
        result.extend(transformed)

    output = bytes(result)
    return unpad(output) if decrypting and mode in ("ECB", "CBC") else output


def encrypt(data: bytes, key: bytes, mode: str = "CBC", iv: bytes | None = None) -> bytes:
    return _transform(data, key, mode, iv, False)


def decrypt(data: bytes, key: bytes, mode: str = "CBC", iv: bytes | None = None) -> bytes:
    return _transform(data, key, mode, iv, True)
