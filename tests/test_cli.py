import base64
import subprocess
import sys

import pytest

from modes import MODES

KEY = bytes(range(16)).hex()


def run(*args):
    return subprocess.run([sys.executable, "-m", "app", *args], capture_output=True)


@pytest.mark.parametrize("mode", MODES)
def test_cli_text_roundtrip(mode):
    plaintext = "Halo Diky é\n"
    encrypted = run("encrypt", "--text", plaintext, "--key", KEY, "--mode", mode)
    assert encrypted.returncode == 0, encrypted.stderr
    assert base64.b64decode(encrypted.stdout).startswith(b"TENUN128")
    restored = run("decrypt", "--text", encrypted.stdout.decode(), "--key", KEY)
    assert restored.returncode == 0, restored.stderr
    assert restored.stdout == plaintext.encode()


def test_cli_file_and_errors(tmp_path):
    source = tmp_path / "sample.bin"
    encrypted = tmp_path / "sample.tenun"
    restored = tmp_path / "restored.bin"
    source.write_bytes(bytes(range(256)))
    assert run("encrypt", "-i", str(source), "-o", str(encrypted), "--key", KEY).returncode == 0
    assert run("decrypt", "-i", str(encrypted), "-o", str(restored), "--key", KEY).returncode == 0
    assert source.read_bytes() == restored.read_bytes()
    assert run("decrypt", "-i", str(encrypted), "-o", str(restored), "--key", KEY).returncode == 1
    assert run("encrypt", "-i", str(source), "--key", KEY).returncode == 2
    assert run("decrypt", "--text", "invalid!", "--key", KEY).returncode == 1
    assert run("encrypt", "--text", "", "--key", "00").returncode == 1
