Kencot Bot - Mamang UGM 🤖🍽️
Kencot Bot adalah chatbot WhatsApp yang siap membantumu menemukan rekomendasi makanan paling mantul di sekitar kampus UGM. Dibuat dengan gaya Gen Z, bot ini akan menjadi teman terbaikmu saat lagi kencot (lapar berat)!

Cukup bilang "laper", dan Mamang UGM akan menanyakan lokasi, tingkat kelaparan, dan budget-mu untuk memberikan rekomendasi yang paling pas.

# Fitur Utama
- Rekomendasi Cerdas: Berdasarkan lokasi (fakultas), budget, dan tingkat kelaparan.
- Database Kantin UGM: Mencakup berbagai kantin populer di sekitar kampus.
- Bahasa Gen Z: Interaksi yang santai dan seru.
- Mudah Digunakan: Cukup chat seperti biasa di WhatsApp.

# Arsitektur Proyek
Bot ini menggunakan arsitektur hybrid yang efisien:
- Backend (Python & Flask): Bertindak sebagai "otak" bot yang berisi semua logika cerdas untuk memproses pesan dan mencari rekomendasi dari database.
- Konektor (Node.js & whatsapp-web.js): Bertindak sebagai "jembatan" yang menghubungkan akun WhatsApp ke backend API.

# Cara Menjalankan Bot Secara Lokal
Untuk menjalankan bot ini di komputermu, kamu perlu menjalankan dua server secara bersamaan di dua terminal terpisah.

### Pra-syarat
Python (versi 3.8+)

Node.js (versi 18+)

Akun WhatsApp yang akan dijadikan nomor bot

### 1. Setup Proyek
Pertama, siapkan proyek dan install semua dependensi yang dibutuhkan.

Clone repository ini:

Bash

git clone https://github.com/namamu/kencot-bot.git
cd kencot-bot
Siapkan file .env:
Buat file bernama .env di folder utama. File ini untuk menyimpan rahasia dan tidak akan di-push ke GitHub.

Code snippet
.env
Tidak ada token yang dibutuhkan untuk whatsapp-web.js
- Cukup siapkan file kosong atau isi dengan SECRET_KEY
  SECRET_KEY=kunci-rahasia-bebas
  Setup Backend Python:

Bash

#### Buat dan aktifkan virtual environment
python -m venv .venv

#### Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

#### Mac/Linux
source .venv/bin/activate

#### Install semua library Python
pip install -r requirements.txt
Setup Konektor Node.js:

Bash

#### Masuk ke folder konektor
cd whatsapp-connector

#### Install semua library Node.js
npm install
### 2. Jalankan Bot
Sekarang, jalankan kedua server di dua terminal terpisah.

#### Terminal 1: Jalankan API Python 
Pastikan kamu berada di folder utama kencot-bot dan .venv sudah aktif.

Bash

python main.py
Biarkan terminal ini berjalan. Server API-mu sekarang aktif di http://localhost:5000.

#### Terminal 2: Jalankan Konektor WhatsApp 
Buka terminal baru, lalu masuk ke folder whatsapp-connector.

Bash

node index.js
Pada saat pertama kali menjalankan, sebuah QR code akan muncul di terminal. Scan QR code tersebut menggunakan aplikasi WhatsApp di HP-mu (Pengaturan > Perangkat tertaut > Tautkan perangkat).

Setelah berhasil, bot-mu akan ONLINE dan siap menerima pesan!

# Cara Menggunakan Bot
Kirim pesan ke nomor WhatsApp yang kamu gunakan untuk scan.
Mulai percakapan dengan kata kunci seperti "laper", "makan", atau "rekomen". Jawab pertanyaan dari bot mengenai lokasi, tingkat kelaparan, dan budget.
