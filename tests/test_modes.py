import random

import pytest

from core.cipher import TENUN128Cipher
from modes import MODES, decrypt, encrypt
from modes.padding import pad, unpad

KEY = bytes(range(16))
IV = bytes(range(16, 32))


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("size", [0, 1, 15, 16, 17, 31, 32, 33, 255, 1024])
def test_roundtrip(mode, size):
    data = random.Random(size).randbytes(size)
    iv = None if mode == "ECB" else IV
    ciphertext = encrypt(data, KEY, mode, iv)
    assert decrypt(ciphertext, KEY, mode, iv) == data
    expected_size = (size // 16 + 1) * 16 if mode in ("ECB", "CBC") else size
    assert len(ciphertext) == expected_size


@pytest.mark.parametrize("mode", MODES)
def test_mode_against_explicit_recurrence(mode):
    data = bytes(range(35))
    cipher = TENUN128Cipher(KEY)
    source = pad(data) if mode in ("ECB", "CBC") else data
    blocks = [source[i:i + 16] for i in range(0, len(source), 16)]
    expected = []
    if mode == "ECB":
        expected = [cipher.encrypt_block(block) for block in blocks]
    elif mode == "CBC":
        previous = IV
        for block in blocks:
            previous = cipher.encrypt_block(xor(block, previous))
            expected.append(previous)
    elif mode == "CFB":
        previous = IV
        for block in blocks:
            previous = xor(block, cipher.encrypt_block(previous))
            expected.append(previous)
    elif mode == "OFB":
        stream = IV
        for block in blocks:
            stream = cipher.encrypt_block(stream)
            expected.append(xor(block, stream))
    else:
        initial = int.from_bytes(IV, "big")
        expected = [xor(block, cipher.encrypt_block((initial + i).to_bytes(16, "big"))) for i, block in enumerate(blocks)]
    ciphertext = b"".join(expected)
    iv = None if mode == "ECB" else IV
    assert encrypt(data, KEY, mode, iv) == ciphertext
    assert decrypt(ciphertext, KEY, mode, iv) == data


def test_ecb_repetition_and_cbc_chaining():
    data = bytes(32)
    ecb = encrypt(data, KEY, "ECB")
    cbc = encrypt(data, KEY, "CBC", IV)
    assert ecb[:16] == ecb[16:32]
    assert cbc[:16] != cbc[16:32]


def test_ctr_boundary():
    maximum = ((1 << 128) - 1).to_bytes(16, "big")
    assert decrypt(encrypt(bytes(16), KEY, "CTR", maximum), KEY, "CTR", maximum) == bytes(16)
    for operation in (encrypt, decrypt):
        with pytest.raises(ValueError, match="Counter"):
            operation(bytes(17), KEY, "CTR", maximum)


@pytest.mark.parametrize("mode", MODES[1:])
@pytest.mark.parametrize("iv", [None, b"", bytes(15), bytes(17)])
def test_invalid_iv(mode, iv):
    with pytest.raises(ValueError, match="IV"):
        encrypt(b"message", KEY, mode, iv)


@pytest.mark.parametrize("data", [b"", b"a", bytes(16), bytes([17]) * 16, b"a" * 14 + b"\x01\x02"])
def test_invalid_padding(data):
    with pytest.raises(ValueError):
        unpad(data)


def test_full_padding_block():
    assert pad(b"") == bytes([16]) * 16
    assert pad(bytes(16)) == bytes(16) + bytes([16]) * 16


@pytest.mark.parametrize("mode", ["ECB", "CBC"])
@pytest.mark.parametrize("data", [b"", b"short", bytes(17)])
def test_incomplete_ciphertext(mode, data):
    with pytest.raises(ValueError):
        decrypt(data, KEY, mode, None if mode == "ECB" else IV)


def test_invalid_mode_key_and_ecb_iv():
    with pytest.raises(ValueError):
        encrypt(b"", KEY, "unknown")
    with pytest.raises(ValueError):
        encrypt(b"", bytes(15), "ECB")
    with pytest.raises(ValueError):
        encrypt(b"", KEY, "ECB", IV)
