"""AI Chat Assistant - asisten obrolan di terminal yang menjawab berdasarkan data sendiri.

Mendukung tiga penyedia AI (atur lewat file .env):
  - groq      : GRATIS (tanpa kartu kredit), cloud, butuh API key gratis
  - ollama    : GRATIS, berjalan lokal di komputer kamu, tanpa API key
  - anthropic : berbayar, butuh API key + saldo
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("PROVIDER", "ollama").lower()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

DATA_DIR = Path(__file__).parent / "data"
MAX_RIWAYAT = 20  # jumlah pesan terakhir yang dikirim

def muat_data() -> str:
    """Baca semua file .txt dan .md di folder data/ sebagai basis pengetahuan."""
    file_data = sorted([*DATA_DIR.glob("*.txt"), *DATA_DIR.glob("*.md")])
    if not file_data:
        print(f"[!] Tidak ada file .txt/.md di folder {DATA_DIR}. Tambahkan data kamu dulu.")
        sys.exit(1)
    return "\n\n".join(
        f"### {f.name}\n{f.read_text(encoding='utf-8')}" for f in file_data
    )


def buat_system_prompt(data: str) -> str:
    return (
        "Kamu adalah asisten AI yang menjawab dalam Bahasa Indonesia.\n"
        "ATURAN: Jawab HANYA berdasarkan DATA di bawah. Jangan menambahkan "
        "informasi dari luar DATA. Jika jawabannya tidak ada di DATA, jawab: "
        "'Maaf, informasi itu tidak ada di basis pengetahuan saya.' "
        "Jawab singkat dan jelas.\n\n"
        f"DATA:\n{data}"
    )


# ---------- Penyedia: Groq (gratis, cloud) ----------
def stream_groq(system_prompt: str, riwayat: list):
    from groq import Groq

    client = Groq()  # membaca GROQ_API_KEY dari .env
    pesan = [{"role": "system", "content": system_prompt}, *riwayat]
    stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=pesan,
        max_tokens=4000,
        temperature=0.2,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


# ---------- Penyedia: Ollama (gratis, lokal) ----------
def stream_ollama(system_prompt: str, riwayat: list):
    import ollama

    pesan = [{"role": "system", "content": system_prompt}, *riwayat]
    for chunk in ollama.chat(
        model=OLLAMA_MODEL,
        messages=pesan,
        stream=True,
        options={"num_ctx": 8192, "temperature": 0.2},
    ):
        yield chunk["message"]["content"]


# ---------- Penyedia: Anthropic (berbayar) ----------
def stream_anthropic(system_prompt: str, riwayat: list):
    import anthropic

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=ANTHROPIC_MODEL,
        max_tokens=1000,
        system=system_prompt,
        messages=riwayat,
    ) as stream:
        yield from stream.text_stream


def pesan_error(e: Exception) -> str:
    nama = type(e).__name__
    if PROVIDER == "groq":
        if "NotFound" in nama:
            return (
                f"Model '{GROQ_MODEL}' tidak tersedia di akun Groq kamu. Ganti GROQ_MODEL di .env "
                "(contoh: openai/gpt-oss-20b) atau lihat daftar model di console.groq.com."
            )
        if "Authentication" in nama or "api_key" in str(e).lower():
            return "GROQ_API_KEY belum ada/tidak valid. Periksa file .env (key dari console.groq.com/keys)."
        if "RateLimit" in nama:
            return "Batas gratis Groq tercapai. Tunggu sebentar lalu coba lagi, atau pakai PROVIDER=ollama."
        if "Connection" in nama:
            return "Tidak bisa terhubung ke internet/Groq."
        return f"{nama}: {e}"
    if PROVIDER == "ollama":
        if "ResponseError" in nama and "not found" in str(e).lower():
            return (
                f"Model '{OLLAMA_MODEL}' belum diunduh. Jalankan di terminal:\n"
                f"    ollama pull {OLLAMA_MODEL}"
            )
        return (
            "Tidak bisa terhubung ke Ollama. Pastikan aplikasi Ollama sudah "
            f"terinstal dan berjalan.\n    Detail: {nama}: {e}"
        )
    if "Authentication" in nama:
        return "API key tidak valid. Periksa file .env kamu."
    return f"{nama}: {e}"


def main() -> None:
    if PROVIDER == "groq":
        stream_fn, info = stream_groq, f"Groq (gratis, cloud) - model {GROQ_MODEL}"
        if not os.getenv("GROQ_API_KEY"):
            print("[!] GROQ_API_KEY belum diisi di file .env")
            print("    Buat key gratis di https://console.groq.com/keys")
            sys.exit(1)
    elif PROVIDER == "ollama":
        stream_fn, info = stream_ollama, f"Ollama (gratis, lokal) - model {OLLAMA_MODEL}"
    elif PROVIDER == "anthropic":
        stream_fn, info = stream_anthropic, f"Anthropic - model {ANTHROPIC_MODEL}"
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("[!] ANTHROPIC_API_KEY belum diisi di file .env")
            sys.exit(1)
    else:
        print(f"[!] PROVIDER '{PROVIDER}' tidak dikenal. Gunakan 'groq', 'ollama', atau 'anthropic'.")
        sys.exit(1)

    system_prompt = buat_system_prompt(muat_data())
    riwayat: list[dict] = []

    print("=" * 56)
    print(" AI Chat Assistant")
    print(f" Penyedia: {info}")
    print(" Ketik 'keluar' untuk berhenti, 'reset' untuk hapus riwayat")
    print("=" * 56 + "\n")

    while True:
        try:
            pesan = input("Kamu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSampai jumpa!")
            break

        if not pesan:
            continue
        if pesan.lower() in ("keluar", "exit", "quit"):
            print("Sampai jumpa!")
            break
        if pesan.lower() == "reset":
            riwayat.clear()
            print("[Riwayat percakapan dihapus]\n")
            continue

        riwayat.append({"role": "user", "content": pesan})
        print("\nAsisten: ", end="", flush=True)

        try:
            jawaban = ""
            for teks in stream_fn(system_prompt, riwayat[-MAX_RIWAYAT:]):
                print(teks, end="", flush=True)
                jawaban += teks
            print("\n")
            riwayat.append({"role": "assistant", "content": jawaban})
        except Exception as e:  # noqa: BLE001
            print(f"\n[!] {pesan_error(e)}\n")
            riwayat.pop()


if __name__ == "__main__":
    main()