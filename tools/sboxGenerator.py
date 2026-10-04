import random


def compute_ddt(sbox):
    ddt = [[0] * 16 for _ in range(16)]
    for dx in range(16):
        for x in range(16):
            dy = sbox[x] ^ sbox[x ^ dx]
            ddt[dx][dy] += 1
    return ddt

def differential_uniformity(sbox):
    ddt = compute_ddt(sbox)
    return max(max(ddt[dx]) for dx in range(1, 16))

def parity(x):
    return bin(x).count("1") % 2

def compute_lat(sbox):
    lat = [[0] * 16 for _ in range(16)]
    for a in range(16):
        for b in range(16):
            count = sum(1 for x in range(16) if parity(x & a) == parity(sbox[x] & b))
            lat[a][b] = count - 8
    return lat


def linear_uniformity(sbox):
    lat = compute_lat(sbox)
    return max(abs(lat[a][b]) for a in range(1, 16) for b in range(1, 16))

def is_valid_sbox(sbox):
    return (
        differential_uniformity(sbox) == 4
        and linear_uniformity(sbox) == 4
        and all(sbox[x] != x for x in range(16))
    )

def search_sbox(seed):
    rng = random.Random(seed)
    candidate = list(range(16))
    attempt = 0
    while True:
        attempt += 1
        rng.shuffle(candidate)
        if is_valid_sbox(candidate):
            return tuple(candidate), attempt

if __name__ == "__main__":
    sbox, attempts = search_sbox(seed=42)
    print(f"S-box found after {attempts} attempts:")
    print(", ".join(hex(x) for x in sbox))
    print("DU:", differential_uniformity(sbox))
    print("LU:", linear_uniformity(sbox))
