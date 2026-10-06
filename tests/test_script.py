from pathlib import Path
import os
import sys
import math
from collections import Counter
import time
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modes.operations import encrypt, decrypt

def flip_bit(data: bytes, bit_index: int = 0) -> bytes:
    arr = bytearray(data)
    byte_idx = bit_index // 8
    bit_offset = bit_index % 8
    arr[byte_idx] ^= (1 << bit_offset)
    return bytes(arr)

def hamming_distance(b1: bytes, b2: bytes) -> int:
    return sum((x ^ y).bit_count() for x, y in zip(b1, b2))

def hitung_entropi(data: bytes) -> float:
    if not data:
        return 0.0
    panjang = len(data)
    frekuensi = Counter(data)
    entropi = 0.0
    for jumlah in frekuensi.values():
        p = jumlah / panjang
        entropi -= p * math.log2(p)
    return entropi

def hitung_distribusi(data: bytes) -> float:
    counts = Counter(data)
    freq = [counts[i] for i in range(256)]
    return freq

def ukur_waktu(func, *args) -> tuple[float, any]:
    mulai = time.perf_counter()
    hasil = func(*args)
    selesai = time.perf_counter()
    durasi_detik = selesai - mulai
    return durasi_detik, hasil

key = bytes.fromhex("b9d1062a71a0dbdaee7b02e916ceca39")
iv = bytes.fromhex("da0773423b2a300f3f75430ef76d0f7f")
counter = bytes.fromhex("17884be59a8704dbb659d13141910cb3")

FILES = {
    "small.txt": Path("tests/files/small.txt"),
    "medium.txt": Path("tests/files/medium.txt"),
    "big.txt": Path("tests/files/big.txt")
}

MODES = ("ECB", "CBC", "CFB", "OFB", "CTR")

def uji_avalanche():
    file_path = FILES["medium.txt"]

    plaintext = file_path.read_bytes()
    plaintext_flipped = flip_bit(plaintext, bit_index=0)
    key_flipped = flip_bit(key, bit_index=0)

    print(f"UJI AVALANCHE \nfile: {file_path.name}")
    print(f"{'Mode'} | {'Flipped Plaintext'} | {'Flipped Key'}")

    for mode in MODES:
        mode_iv = None if mode == "ECB" else (counter if mode == "CTR" else iv)

        c1 = encrypt(plaintext, key, mode=mode, iv=mode_iv)
        c2 = encrypt(plaintext_flipped, key, mode=mode, iv=mode_iv)
        c3 = encrypt(plaintext, key_flipped, mode=mode, iv=mode_iv)

        total_bits = len(c1) * 8
        h2 = hamming_distance(c1, c2)
        h3 = hamming_distance(c1, c3)

        a2 = (h2 / total_bits) * 100
        a3 = (h3 / total_bits) * 100

        print(f"{mode} | {a2:.2f}% | {a3:.2f}%")
    print("=" * 65)

def uji_entropi():
    file_path = FILES["medium.txt"]

    plaintext = file_path.read_bytes()

    print(f"ANALISIS ENTROPI \nfile: {file_path.name}")
    print(f"{'Mode'} | {'Entropi (bit/byte)'}")

    for mode in MODES:
        mode_iv = None if mode == "ECB" else (counter if mode == "CTR" else iv)
        ciphertext = encrypt(plaintext, key, mode=mode, iv=mode_iv)
        entropi = hitung_entropi(ciphertext)
        print(f"{mode} | {entropi:.6f}")
    print("=" * 65)

def uji_histogram():
    file_path = FILES["medium.txt"]

    plaintext = file_path.read_bytes()
    hasil = {}
    hasil["Plaintext"] = hitung_distribusi(plaintext)

    for mode in MODES:
        mode_iv = None if mode == "ECB" else (counter if mode == "CTR" else iv)
        ciphertext = encrypt(plaintext, key, mode=mode, iv=mode_iv)
        hasil[mode] = hitung_distribusi(ciphertext)

    # Buat Histogram
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    for idx, (nama, freq) in enumerate(hasil.items()):
        ax = axes[idx]
        ax.bar(range(256), freq, color="royalblue", width=1.0, edgecolor="none")
        ax.set_title(f"{nama}")
        ax.set_xlim(0, 255)
        ax.set_xlabel("Nilai Byte (0-255)")
        ax.set_ylabel("Frekuensi")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    output_img = Path("tests/files/histogram.png")
    plt.savefig(output_img, dpi=300)

    print(f"ANALISIS HISTOGRAM \nfile: {file_path.name}")
    print(f"Histogram disimpan ke: {output_img}")
    print("=" * 65)

def uji_performa():
    data_files = {}
    for label, path in FILES.items():
        data_files[label] = path.read_bytes()

    print("UJI PERFORMA")
    print(f"| {'File'} | " + " | ".join(f"{f}" for f in FILES) + " |")
    print(f"| {'Size (byte)'} | " + " | ".join(f"{len(data_files[f])}" for f in FILES) + " |")
    print()

    print(f"| {'Mode'} | {'File'} | {'Encrypt (ms)'} | {'Decrypt (ms)'} | {'Throughput Encrypt (MB/s)'} | {'Throughput Decrypt (MB/s)'} |")
    print("-" * 100)

    for mode in MODES:
        mode_iv = None if mode == "ECB" else (counter if mode == "CTR" else iv)
        for label, _ in FILES.items():
            data = data_files[label]
            size_bytes = len(data)
            size_mb = size_bytes / (1024 * 1024)

            t_enc, c_data = ukur_waktu(encrypt, data, key, mode, mode_iv)
            enc_ms = t_enc * 1000.0
            tp_enc = size_mb / t_enc if t_enc > 0 else 0.0

            t_dec, _ = ukur_waktu(decrypt, c_data, key, mode, mode_iv)
            dec_ms = t_dec * 1000.0
            tp_dec = size_mb / t_dec if t_dec > 0 else 0.0

            print(f"| {mode} | {label} | {enc_ms:.3f} | {dec_ms:.3f} | {tp_enc:.2f} | {tp_dec:.2f} |")
        print("-" * 100)

if __name__ == "__main__":
    uji_avalanche()
    uji_entropi()
    uji_histogram()
    uji_performa()