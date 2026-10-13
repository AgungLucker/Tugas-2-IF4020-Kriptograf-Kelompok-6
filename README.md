# TENUN-128

Program enkripsi dan dekripsi teks dan berkas untuk Tugas 2 IF4020 Kriptografi
2026/2027. Program memakai block cipher buatan sendiri, TENUN-128 (blok 128 bit,
kunci 128 bit, 16 round), dengan mode operasi ECB, CBC, CFB, OFB, dan CTR. Padding
memakai PKCS#7, dan integritas hasil dekripsi dijaga dengan CMAC yang dibangun di
atas TENUN-128.

Algoritma cipher, mode operasi, padding, dan CMAC ditulis sendiri tanpa pustaka
kriptografi pihak ketiga. Program dapat dijalankan di Windows dan Linux.

## Teknologi dan dependensi

- Python 3.12 atau lebih baru (proyek ini memakai 3.13)
- Textual 8.2.8 atau lebih baru, untuk antarmuka terminal
- uv, untuk mengelola dependensi
- Untuk pengujian: pytest, pytest-asyncio, dan matplotlib (matplotlib hanya dipakai
  `tests/test_script.py` untuk menggambar histogram)

## Menjalankan

Dari direktori proyek:

```sh
uv sync --locked
uv run python -m app
```

Perintah di atas membuka antarmuka terminal. Untuk CLI:

```sh
uv run python -m app --help
uv run python -m app encrypt --text "Halo" --key 000102030405060708090a0b0c0d0e0f --mode CBC
uv run python -m app decrypt --text <hasil base64> --key 000102030405060708090a0b0c0d0e0f
uv run python -m app encrypt -i berkas.bin -o berkas.tenun --key 000102030405060708090a0b0c0d0e0f
```

Kunci berupa 32 digit heksadesimal (16 byte). IV atau counter awal diberikan dengan
`--iv` (32 digit heksadesimal), dan jika dikosongkan dibuat acak.

## Pengujian

```sh
uv run pytest -q
uv run python -u tests/test_script.py | tee tests/files/result.txt
```

Perintah pertama menjalankan seluruh tes otomatis. Perintah kedua menjalankan uji
avalanche, entropi, histogram, dan performa untuk kelima mode. Berkas uji ada di
`tests/files/`, dan hasil uji enkripsi dan dekripsi pada teks dan berkas biner ada di
`testcases/implementation/`.

## Struktur

- `core/` : cipher TENUN-128 (S-box, permutasi, round key, fungsi round)
- `modes/` : mode operasi dan padding
- `app/` : CLI, antarmuka terminal, format berkas hasil enkripsi, dan CMAC
- `tools/` : pencari S-box dan pembangkit berkas uji
- `tests/` dan `testcases/` : tes otomatis, berkas uji, dan hasil pengujian
- `docs/` : laporan
