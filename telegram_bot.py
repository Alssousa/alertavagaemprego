import telebot
import os
from dotenv import load_dotenv
import json
from web_scraper import logger

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
    

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
                 "Olá! Seja bem vindo ao bot que irá notificar vagas de emprego de acordo com suas preferências."                
                 "Para continuar, por favor, envie o nome da cidadade que você deseja buscar vagas de emprego."
                 )
    #bot.send_message(message.chat.id, "Para continuar, por favor, envie o nome da cidadade que você deseja buscar vagas de emprego.")
    bot.register_next_step_handler(message, process_city)
    
    
def process_city(message):
    data = load_user_date()
    city = (message.text or "").strip()
    user_id = str(message.from_user.id)
    print('User: ', str(message.from_user.id), ' Cidade recebida: ', city, ' Type: ', type(city))
    if not city:
        bot.reply_to(message, "Cidade inválida. Por favor, envie o nome da cidade novamente.")
        bot.register_next_step_handler(message, process_city)
    
    data[user_id] = data.get(user_id, {})
    if not data[user_id]['city']:
        data[user_id]['city'] = []
        logger.info("Usuario ainda não possui cidades cadastradas. Criando lista...")
    logger.info("Obj citys: %s", data[user_id]['city'])
    if data[user_id]['city'] and city in data[user_id]['city']:
        text = (
            f'A cidade {city} já está em sua lista preferencial.'
            f'Caso queira adicionar mais cidades para acompanhar o surgimento de novas oportunidade, digite o comando /adicionar_cidade ou clique sobre ele.'
            )
        bot.reply_to(message, text)
    else:
        data[user_id]['city'].append(city)
        save_user_data(data)
        bot.reply_to(message, f"A cidade {city} foi adicionada em sua lista de preferências. Aguarde para novas notificações :)")
    
@bot.message_handler(commands=['cidades_cadastrada'])
def my_citys(message):
    user_id = message.from_user.id
    if user_id:
        bot.reply_to(message, "Aguarde um momento...")
        try:
            data = load_user_date()
            print("Dados do usuario: ", user_id, "\nDados: ", data)
            user_citys =  data[str(user_id)]['city']
            print('teste 2: ', user_citys)
            text = (
                f"SUA LISTA DE CIDADES CADASTRADAS:\n"
                f'{user_citys}'
            )
            bot.send_message(user_id, text)
        except Exception as e:
            logger.exception("Ocorreu um erro ao carregar dados do usuario. Err-:%s", e)
            bot.send_message(user_id, "Por favor, tente mais tarde. Estamos com um pequeno problema no servidor.")

def send_alert_new_job(user_id, job_info: dict):
    try:
        chat_id = int(user_id)
        text = (
            f"Uma nova oportunidade de emprego foi encontrada!\n\n"
            f"Vaga: {job_info.get('job', '-')}\n"
            f"Empresa: {job_info.get('empresa', '-')}\n"
            f"Modalidade: {job_info.get('modalidade', '-')}\n"
            f"Local: {job_info.get('local', '-')}\n"
            f"Feedback: {job_info.get('feedback', '-')}\n"
            f"Link: {job_info.get('link', '-')}\n\n"
            "Acesse o site para mais informações."
        )
        logger.info("Enviando mensagem para %s -> %s - %s", chat_id, job_info.get('empresa'), job_info.get('job'))
        bot.send_message(chat_id, text)
    except Exception as e:
        logger.exception("Falha ao enviar alerta para %s: %s", user_id, e)