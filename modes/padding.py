BLOCK_SIZE = 16


def pad(data: bytes) -> bytes:
    count = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + bytes([count]) * count


def unpad(data: bytes) -> bytes:
    if not data or len(data) % BLOCK_SIZE:
        raise ValueError("Data PKCS#7 harus berisi blok lengkap.")
    count = data[-1]
    if not 1 <= count <= BLOCK_SIZE or data[-count:] != bytes([count]) * count:
        raise ValueError("Padding PKCS#7 tidak valid.")
    return data[:-count]
