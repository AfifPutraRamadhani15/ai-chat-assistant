# AI Chat Assistant (GRATIS: Groq / Ollama)

Asisten AI berbasis terminal yang menjawab berdasarkan **data sendiri**
(file `.txt` / `.md` di folder `data/`).

## Pilihan penyedia AI
| PROVIDER | Biaya | Butuh |
|---|---|---|
| `groq` (default) | Gratis, tanpa kartu kredit (ada batas pemakaian) | API key gratis + internet |
| `ollama` | Gratis | Instal Ollama + unduh model, tanpa internet saat dipakai |
| `anthropic` | Berbayar | API key + saldo |

## A. Pakai Groq (default)
1. Daftar di https://console.groq.com lalu buat key di https://console.groq.com/keys
2. Instal proyek:

Windows:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```
macOS / Linux:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
3. Buka `.env`, ganti `GROQ_API_KEY` dengan key kamu.
4. Jalankan: `python main.py`

Jika batas gratis tercapai, ubah `GROQ_MODEL=llama-3.1-8b-instant` (batas harian lebih longgar).

## B. Pakai Ollama (tanpa API key)
1. Instal dari https://ollama.com/download, lalu: `ollama pull qwen2.5:3b`
2. Di `.env`: `PROVIDER=ollama`
3. `python main.py`

## C. Pakai Anthropic (berbayar)
Di `.env`: `PROVIDER=anthropic` + `ANTHROPIC_API_KEY=...`, lalu `pip install anthropic`.

## Alternatif: uv
```
uv sync
uv run main.py
```

## Data sendiri
Ganti/tambah file `.txt`/`.md` di folder `data/`.
Perintah di chat: `reset` (hapus riwayat), `keluar` (berhenti).

> Jangan pernah upload file `.env` ke GitHub (sudah ada di `.gitignore`).
