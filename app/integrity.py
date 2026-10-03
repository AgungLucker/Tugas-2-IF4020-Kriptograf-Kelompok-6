from core.cipher import TENUN128Cipher
from modes.operations import xor_bytes


def double_block(block: bytes) -> bytes:
    number = int.from_bytes(block, "big")
    carry = number >> 127
    return (((number << 1) & ((1 << 128) - 1)) ^ (0x87 if carry else 0)).to_bytes(16, "big")


def cmac(data: bytes, key: bytes) -> bytes:
    cipher = TENUN128Cipher(key)
    k1 = double_block(cipher.encrypt_block(bytes(16)))
    k2 = double_block(k1)
    complete = bool(data) and len(data) % 16 == 0
    last_offset = ((len(data) - 1) // 16) * 16 if data else 0
    last = data[last_offset:]
    if complete:
        last = xor_bytes(last, k1)
    else:
        last = xor_bytes(last + b"\x80" + bytes(15 - len(last)), k2)
    state = bytes(16)
    for offset in range(0, last_offset, 16):
        state = cipher.encrypt_block(xor_bytes(state, data[offset:offset + 16]))
    return cipher.encrypt_block(xor_bytes(state, last))


def authentication_tag(data: bytes, master_key: bytes) -> bytes:
    mac_key = TENUN128Cipher(master_key).encrypt_block(b"TENUN-MAC-KEY-v1")
    return cmac(data, mac_key)
