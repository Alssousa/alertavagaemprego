import telebot
import os
from dotenv import load_dotenv
import json

load_dotenv()
TELEGRAM_TOOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOOKEN)
DATA_FILE = "data.json"


def save_user_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
def load_user_date():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data               
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
data = load_user_date()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, '''Olá! Seja bem vindo ao bot que irá notificar vagas de emprego de acordo com suas preferências.
                 
                 Para continuar, por favor, envie o nome da cidadade que você deseja buscar vagas de emprego.
                 ''')
    #bot.send_message(message.chat.id, "Para continuar, por favor, envie o nome da cidadade que você deseja buscar vagas de emprego.")
    bot.register_next_step_handler(message, process_city)
    
    
def process_city(message):
    city = (message.text or "").strip()
    user_id = str(message.from_user.id)
    print('User: ', str(message.from_user.id), ' Cidade recebida: ', city, ' Type: ', type(city))
    if not city:
        bot.reply_to(message, "Cidade inválida. Por favor, envie o nome da cidade novamente.")
        bot.register_next_step_handler(message, process_city)
    
    data[user_id] = data.get(user_id, {})
    data[user_id]['city'] = city
    save_user_data(data)
    bot.reply_to(message, f"A cidade {city} foi adicionada em sua lista de preferências. Aguarde para novas notificações :)")
    

def send_alert_new_job():
    pass