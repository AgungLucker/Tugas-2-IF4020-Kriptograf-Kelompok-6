from dataclasses import dataclass
from pathlib import Path
import secrets
import struct

from core.cipher import TENUN128Cipher
from modes import MODES, decrypt as decrypt_raw, encrypt as encrypt_raw
from .integrity import authentication_tag

MAGIC = b"TENUN128"
VERSION = 1
HEADER = struct.Struct(">8sBB16sQ")
TAG_SIZE = 16


class IntegrityError(ValueError):
    pass


@dataclass(frozen=True)
class Metadata:
    mode: str
    iv: bytes | None
    plaintext_size: int
    ciphertext_size: int


def parse_key(value: str, encoding: str = "hex") -> bytes:
    if encoding == "hex":
        try:
            key = bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError("Kunci hex tidak valid.") from exc
    elif encoding == "text":
        key = value.encode("utf-8")
    else:
        raise ValueError("Format kunci harus hex atau text.")
    TENUN128Cipher(key)
    return key


def parse_iv(value: str) -> bytes | None:
    if not value.strip():
        return None
    try:
        iv = bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError("IV/counter hex tidak valid.") from exc
    if len(iv) != 16:
        raise ValueError("IV/counter harus 32 digit hex (16 byte).")
    return iv


def encrypt(data: bytes, key: bytes, mode: str = "CBC", iv: bytes | None = None) -> bytes:
    mode = mode.upper()
    if mode not in MODES:
        raise ValueError(f"Mode tidak dikenal: {mode}.")
    if mode != "ECB" and iv is None:
        iv = secrets.token_bytes(16)
    encryption_key = TENUN128Cipher(key).encrypt_block(b"TENUN-ENC-KEY-v1")
    ciphertext = encrypt_raw(data, encryption_key, mode, iv)
    header = HEADER.pack(MAGIC, VERSION, MODES.index(mode), iv if iv is not None else bytes(16), len(data))
    authenticated = header + ciphertext
    return authenticated + authentication_tag(authenticated, key)


def inspect_verified(envelope: bytes, key: bytes) -> Metadata:
    TENUN128Cipher(key)
    if len(envelope) < HEADER.size + TAG_SIZE:
        raise IntegrityError("Berkas TENUN terlalu pendek atau tidak valid.")
    body, tag = envelope[:-TAG_SIZE], envelope[-TAG_SIZE:]
    if not secrets.compare_digest(authentication_tag(body, key), tag):
        raise IntegrityError("Verifikasi integritas gagal: kunci salah atau data berubah.")
    magic, version, mode_id, iv, size = HEADER.unpack_from(body)
    if magic != MAGIC or version != VERSION or mode_id >= len(MODES):
        raise ValueError("Format/versi berkas TENUN tidak didukung.")
    mode = MODES[mode_id]
    ciphertext_size = len(body) - HEADER.size
    expected = (size // 16 + 1) * 16 if mode in ("ECB", "CBC") else size
    if ciphertext_size != expected or (mode == "ECB" and iv != bytes(16)):
        raise ValueError("Metadata ukuran/IV berkas TENUN tidak valid.")
    return Metadata(mode, None if mode == "ECB" else iv, size, ciphertext_size)


def decrypt(envelope: bytes, key: bytes) -> bytes:
    metadata = inspect_verified(envelope, key)
    encryption_key = TENUN128Cipher(key).encrypt_block(b"TENUN-ENC-KEY-v1")
    output = decrypt_raw(envelope[HEADER.size:-TAG_SIZE], encryption_key, metadata.mode, metadata.iv)
    if len(output) != metadata.plaintext_size:
        raise IntegrityError("Ukuran hasil dekripsi tidak sesuai metadata.")
    return output


def write_new(path: str | Path, data: bytes) -> None:
    target = Path(path).expanduser()
    stream = target.open("xb")
    try:
        with stream:
            stream.write(data)
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def encrypt_file(source: str | Path, destination: str | Path, key: bytes, mode: str = "CBC", iv: bytes | None = None) -> None:
    write_new(destination, encrypt(Path(source).expanduser().read_bytes(), key, mode, iv))


def decrypt_file(source: str | Path, destination: str | Path, key: bytes) -> None:
    write_new(destination, decrypt(Path(source).expanduser().read_bytes(), key))
