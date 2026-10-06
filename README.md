# TENUN-128

Program enkripsi dan dekripsi teks/berkas untuk Tugas 2 IF4020 Kriptografi
2026/2027, menggunakan block cipher 128-bit dengan mode ECB, CBC, CFB, OFB, dan CTR.

Menggunakan Python 3.13 dan Textual. Dependensi dikelola dengan [uv](https://docs.astral.sh/uv/).

## Menjalankan

Dari direktori proyek:

```sh
uv sync --locked
uv run python -m app
```

Untuk bantuan CLI: `uv run python -m app --help`.

## Pengujian

```sh
uv run python -u tests/test_script.py | tee tests/files/result.txt
```
