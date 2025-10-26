from src.bot import KencotBot
from src.config import Config

bot = KencotBot(Config)

print("Chat CLI untuk KencotBot (ketik 'quit' untuk keluar)")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "exit"]:
        print("Keluar...")
        break
    response = bot.handle_message("user123", user_input)
    print("Bot:", response)
