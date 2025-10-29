from src.bot import KencotBotV2
from src.config import Config
from src.database.connection import db_instance

# === Inisialisasi koneksi database ===
db_instance.connect()  # <-- ini otomatis pilih Mongo atau JSON
print("✅ Database initialized.")

# === Inisialisasi bot ===
bot = KencotBotV2()

print("\n🤖 Chat CLI untuk KencotBot (ketik 'quit' untuk keluar)")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "exit"]:
        db_instance.close()  # tutup koneksi / simpan JSON
        print("👋 Keluar...")
        break

    response = bot.handle_message("user123", user_input)
    print("Bot:", response)
