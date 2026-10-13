import json
from pathlib import Path

import pytest

from app import service
from core.cipher import TENUN128Cipher
from modes import MODES

FIXTURES = Path(__file__).resolve().parents[1] / "testcases" / "implementation"


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("name", ["text.txt", "binary.bin"])
def test_demo_artifacts_are_reproducible(mode, name):
    report = json.loads((FIXTURES / "results.json").read_text())
    key = bytes.fromhex(report["key_hex"])
    iv = None if mode == "ECB" else bytes.fromhex(report["iv_hex"])
    original = (FIXTURES / name).read_bytes()
    envelope = (FIXTURES / f"{name}.{mode.lower()}.tenun").read_bytes()
    assert service.encrypt(original, key, mode, iv) == envelope
    assert service.decrypt(envelope, key) == original
    assert (FIXTURES / f"{name}.{mode.lower()}.restored").read_bytes() == original
    case = next(case for case in report["cases"] if case["input"] == name and case["mode"] == mode)
    assert case["roundtrip_equal"] and case["tampering_rejected"]
    assert case["plaintext_bytes"] == len(original)
    assert case["envelope_bytes"] == len(envelope)


def test_pinned_existing_core_vector():
    cipher = TENUN128Cipher(bytes(range(16)))
    plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
    ciphertext = bytes.fromhex("23c65174394040e93ee91d5c309d112b")
    assert cipher.encrypt_block(plaintext) == ciphertext
    assert cipher.decrypt_block(ciphertext) == plaintext
