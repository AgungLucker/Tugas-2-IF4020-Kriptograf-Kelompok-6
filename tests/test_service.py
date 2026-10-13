import pytest

from app.integrity import cmac, double_block, authentication_tag
from app.service import HEADER, IntegrityError, decrypt, decrypt_file, encrypt, encrypt_file, inspect_verified, parse_iv, parse_key
from modes import MODES

KEY = bytes(range(16))
IV = bytes(range(16, 32))


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("data", [b"", b"x", bytes(16), bytes(range(256)), "Halo Diky é\n\x00".encode()])
def test_authenticated_roundtrip(mode, data):
    envelope = encrypt(data, KEY, mode)
    assert decrypt(envelope, KEY) == data
    meta = inspect_verified(envelope, KEY)
    assert meta.mode == mode
    assert meta.plaintext_size == len(data)
    assert (meta.iv is None) == (mode == "ECB")


@pytest.mark.parametrize("mode", MODES)
def test_every_byte_is_authenticated(mode):
    envelope = encrypt(b"Authenticating header, IV, size, ciphertext and tag!", KEY, mode)
    for position in range(len(envelope)):
        damaged = bytearray(envelope)
        damaged[position] ^= 1
        with pytest.raises(IntegrityError):
            decrypt(bytes(damaged), KEY)
    for damaged in (envelope[:-1], envelope + b"x", envelope[:20]):
        with pytest.raises(IntegrityError):
            decrypt(damaged, KEY)
    with pytest.raises(IntegrityError):
        decrypt(envelope, bytes(reversed(KEY)))


@pytest.mark.parametrize("mode", MODES)
def test_binary_files_and_failed_decryption_preserves_output(tmp_path, mode):
    original = tmp_path / "binary.bin"
    encrypted = tmp_path / "binary.tenun"
    restored = tmp_path / "restored.bin"
    failed = tmp_path / "failed.bin"
    data = bytes(range(256)) + b"\x00\xff\x00"
    original.write_bytes(data)
    encrypt_file(original, encrypted, KEY, mode)
    decrypt_file(encrypted, restored, KEY)
    assert restored.read_bytes() == data
    with pytest.raises(FileExistsError):
        decrypt_file(encrypted, restored, KEY)
    assert restored.read_bytes() == data
    damaged = bytearray(encrypted.read_bytes())
    damaged[-1] ^= 1
    encrypted.write_bytes(damaged)
    with pytest.raises(IntegrityError):
        decrypt_file(encrypted, failed, KEY)
    assert not failed.exists()


def test_invalid_authentication_never_calls_decrypt(monkeypatch):
    envelope = encrypt(b"never release this", KEY)
    def forbidden(*args):
        pytest.fail("Raw decrypt called before successful authentication")
    monkeypatch.setattr("app.service.decrypt_raw", forbidden)
    with pytest.raises(IntegrityError):
        decrypt(envelope[:-1] + bytes([envelope[-1] ^ 1]), KEY)


def test_iv_generation_and_deterministic_override():
    assert encrypt(b"same", KEY) != encrypt(b"same", KEY)
    assert encrypt(b"same", KEY, "CBC", IV) == encrypt(b"same", KEY, "CBC", IV)
    assert inspect_verified(encrypt(b"same", KEY, "CTR", IV), KEY).iv == IV


@pytest.mark.parametrize("version,mode_id,size", [(2, 1, 3), (1, 255, 3), (1, 1, 100)])
def test_authenticated_but_invalid_metadata(version, mode_id, size):
    envelope = encrypt(b"abc", KEY, "CBC", IV)
    body = HEADER.pack(b"TENUN128", version, mode_id, IV, size) + envelope[HEADER.size:-16]
    with pytest.raises(ValueError):
        decrypt(body + authentication_tag(body, KEY), KEY)


def test_parsing():
    assert parse_key(KEY.hex()) == KEY
    assert parse_key("abcdefghijklmnop", "text") == b"abcdefghijklmnop"
    assert parse_iv("") is None
    assert parse_iv(IV.hex()) == IV
    for key in ("zz", "00", ""):
        with pytest.raises(ValueError):
            parse_key(key)
    with pytest.raises(ValueError):
        parse_key("é" * 16, "text")
    for iv in ("gg", "00"):
        with pytest.raises(ValueError):
            parse_iv(iv)


def test_cmac_subkey_reduction_and_length_separation():
    assert double_block(bytes.fromhex("80000000000000000000000000000000")) == bytes.fromhex("00000000000000000000000000000087")
    assert double_block(bytes.fromhex("00000000000000000000000000000001")) == bytes.fromhex("00000000000000000000000000000002")
    tags = [cmac(bytes(size), KEY) for size in (0, 1, 15, 16, 17, 32)]
    assert len(set(tags)) == len(tags)
    assert all(len(tag) == 16 for tag in tags)
