# Kencot Bot - Mamang UGM 🤖🍽️

Kencot Bot adalah chatbot WhatsApp **teman terbaikmu saat kencot (lapar berat)** di sekitar kampus UGM.
Cukup chat "laper", dan Mamang UGM akan menanyakan lokasi, tingkat kelaparan, dan budget-mu untuk memberikan **rekomendasi makanan paling mantul**.

Didesain dengan bahasa **Gen Z**, bot ini bikin percakapan santai tapi tetap cerdas.

---

## Nama Tim
| No | Nama                        | NIM                |
|----|-----------------------------|--------------------|
| 1  | Adinda Putri Romadhon       | 22/505508/TK/55321 |
| 2  | Fatimah Nadia Eka Putri     | 22/497876/TK/554588|

---

## Link
- **Demo Video:**
  - [https://bit.ly/VideoDemoKencot-Bot](https://bit.ly/VideoDemoKencot-Bot)

- **Link PPT:**
  - [PDF PPT Presentasi](https://drive.google.com/file/d/1KkjctXrmL1yCzlNhx7YkXp80rip9fY7a/view?usp=sharing)
  - [PPT Presentasi](https://docs.google.com/presentation/d/14aagyh5VrmLZ-b4oezT8jvQyUHmKAQV5/edit?usp=sharing&ouid=110910143854406637416&rtpof=true&sd=true)

- **Demo GIF:**
    ![Demo BOT GIF](documentation/demo.gif)

## Fitur Utama

* **Rekomendasi Cerdas**: Disesuaikan dengan lokasi (fakultas), tingkat kelaparan, dan budget.
* **Database Kantin UGM**: Lengkap dengan kantin populer di sekitar kampus.
* **Santai & Seru**: Bahasa Gen Z yang bikin interaksi nggak kaku.
* **Mudah Digunakan**: Chat langsung di WhatsApp seperti ngobrol biasa.

---

## Arsitektur Proyek

Bot ini menggunakan **arsitektur hybrid** yang efisien:

1. **Backend (Python & Flask)**: Otak bot yang memproses pesan dan mencari rekomendasi dari database.
2. **Konektor (Node.js & whatsapp-web.js)**: Jembatan yang menghubungkan WhatsApp ke backend API.
3. **Integrasi LLM (Gemini)**: Return rekomendasi dari AI Gemini jika tidak ada data yang sesuai dari database.

![Arsitektur KencotBot](documentation/arsitektur.png)

---

## Pra-syarat

Pastikan sebelum mulai, kamu sudah menyiapkan:

* **Python 3.8+**
* **Node.js 18+**
* **Akun WhatsApp** yang akan dijadikan bot

---

## Setup Proyek

### 1. Clone Repository

```bash
git clone https://github.com/fatimahnadiaekaputri/kencot-bot.git
cd kencot-bot
```

### 2. Siapkan file `.env`

Buat file `.env` di folder utama. Tidak perlu token khusus untuk WhatsApp. `.env` digunakan untuk token API GEMINI yang bisa didapatkan di [Google AI Studio]](https://aistudio.google.com/)

```bash
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

### 3. Setup Backend Python

```bash
# Buat virtual environment
python -m venv .venv

# Aktifkan virtual environment
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Mac/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Setup Konektor Node.js

```bash
cd whatsapp-connector
npm install
```

---

## Menjalankan Bot

Kamu perlu **dua terminal**: satu untuk backend Python, satu untuk konektor WhatsApp.

### Terminal 1: Jalankan API Python

```bash
python main.py
```

> Server API aktif di `http://localhost:5000`. Jangan ditutup!
> **Stop server:** Tekan `Ctrl + C` di terminal untuk menghentikan server Python.

### Terminal 2: Jalankan Konektor WhatsApp

```bash
cd whatsapp-connector
node index.js
```

> Saat pertama kali, QR code akan muncul. Scan menggunakan WhatsApp di HP-mu (Pengaturan > Perangkat Tertaut > Tautkan Perangkat).
> Setelah berhasil, bot **ONLINE** dan siap diajak chat!
> **Stop server:** Tekan `Ctrl + C` di terminal untuk menghentikan konektor Node.js.

---

## Cara Menggunakan Bot

1. Chat nomor WhatsApp bot-mu.
2. Mulai percakapan dengan kata kunci: **“laper”**, **“makan”**, atau **“rekomen”**.
3. Jawab pertanyaan bot: lokasi, tingkat kelaparan, dan budget.
4. Nikmati rekomendasi makanan yang paling pas!

---

## Struktur Folder

```
kencot-bot/
│
├─ main.py              # Entry point backend Python
├─ requirements.txt     # Dependencies Python
├─ .env                 # Rahasia & config
├─ whatsapp-connector/  # Folder konektor Node.js
│  ├─ index.js
│  └─ package.json
├─ app/                 # Logic bot
│  ├─ bot.py
│  ├─ config.py
│  ├─ llm.py            # openai bot
│  └─ utils.py
├─ test/                # test code
│  ├─ functional_test.py           
│  └─ unit_test.py
└─ database/            # Data kantin
```

---

## Tips

* Pastikan **dua server berjalan bersamaan**.
* Scan QR code hanya saat pertama kali.
* Simpan `.env` agar rahasia tetap aman.
* Kalau ada error install dependencies, coba upgrade pip & npm:

```bash
pip install --upgrade pip
npm install -g npm
```

* Gunakan terminal terpisah untuk tiap server agar gampang debug.
* Cek console log di Node.js untuk melihat status koneksi WhatsApp.

---

*Selamat mencoba! Semoga Mamang UGM siap nemenin kencot-mu setiap saat! 🤤*
