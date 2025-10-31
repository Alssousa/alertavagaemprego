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
                 "Olá! Seja bem vindo ao bot que irá notificar vagas de emprego de acordo com suas preferências.\n\n"                
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
            f'A cidade {city} já está em sua lista preferencial.\n\n'
            f'Caso queira adicionar mais cidades para acompanhar o surgimento de novas oportunidade, digite o comando /adicionar_cidade ou clique sobre ele.'
            )
        bot.reply_to(message, text)
    else:
        data[user_id]['city'].append(city)
        save_user_data(data)
        bot.reply_to(message, f"A cidade {city} foi adicionada em sua lista de preferências. \n\nAguarde para novas notificações :)")
    
@bot.message_handler(commands=['cidades_cadastradas'])
def my_citys(message):
    user_id = message.from_user.id
    if user_id:
        bot.reply_to(message, "Aguarde um momento...")
        try:
            data = load_user_date()
            print("Dados do usuario: ", user_id, "\nDados: ", data)
            user_citys =  data[str(user_id)]['city']
            if not user_citys:
                text = (f"Você não possui cidades cadastrada.\n\nPara adicionar cidades, use o comando /adicionar.")
            else:
                print('teste 2: ', user_citys)
                user_citys = '\n'.join([item for item in user_citys])
                text = (
                    f"SUA LISTA DE CIDADES CADASTRADAS:\n"
                    f'{user_citys}'
                )
            bot.send_message(user_id, text)
        except Exception as e:
            logger.exception("Ocorreu um erro ao carregar dados do usuario. Err-:%s", e)
            bot.send_message(user_id, "Por favor, tente mais tarde. Estamos com um pequeno problema no servidor.")

@bot.message_handler(commands=['adicionar'])
def add_city(message):
    user_id = message.from_user.id
    if message.text.lower().startswith('/'):
        print("Adicionar cidade: comando / ESCOPO")
        bot.reply_to(message, "Digite o nome da cidade que você deseja receber alerta de emprego:\n\nCaso queira cancelar o comando, digite 'cancelar'. ")
        bot.register_next_step_handler(message, add_city)
    else:
        print("Adicionando cidade parte 2 / ESCOPO")
        if 'cancelar' not in message.text.lower():
            try:
                data = load_user_date()
                user_data = data.get(str(user_id), {})
                print('dados do usuario: ', user_data)
                if message.text:
                    print("cidade a ser adicionada: ", message.text)
                    new_city = message.text.strip()   
                    if new_city not in user_data['city']:
                        user_data['city'].append(new_city)
                        data[str(user_id)] = user_data
                        try:
                            save_user_data(data)
                            print("Cidade salva com sucesso.")
                            bot.send_message(user_id, f"A cidade {message.text} foi adicionada com sucesso.")
                        except Exception as e:
                            print("Ocorreu um erro ao salvar o arquivo.., e", e)
                            raise
                    else:
                        print("A cidade já está cadastrada.")
                        bot.send_message(user_id, f"A cidade {message.text} já está cadastrada. Verifique as cidades que você cadastrou pelo comando /cidades_cadastradas.")
            except Exception as e:
                print("Erro ao salvar a cidade, e", e)
                bot.send_message(user_id, "Erro ao cadastrar a cidade. Por favor, aguarde um pouco e tente novamente.")
                
    
@bot.message_handler(commands=['remover'])
def remove_city(message):
    user_id = message.from_user.id
    print("FUNÇÃO REMOVER ACESSADA")
    if message.text.lower().startswith('/'):
        print("DENTRO DO COMANDO /")
        try:
            data = load_user_date()
            user_citys = data[str(user_id)].get('city', {})
            print('carregando dados do usuario: ', user_citys)
            if user_citys:
                citys_formated = '\n'.join([item for item in user_citys])
                print("O PROBLEMA É NA FORMATAÇÃO? ", citys_formated)
                text = (
                    f'Para remover uma cidade de sua lista, digite o nome da mesma conforme mostrado representado abaixo: \n\n'
                    f'{citys_formated}'
                    f'\n\nCaso queira cancelar o comando, digite "cancelar".\n'
                )
                bot.send_message(user_id, text)
                bot.register_next_step_handler(message, remove_city)
        except Exception as e:
            logger.exception('Erro ao enviar as possíveis cidades a serem removidas. e-> %s', e)
    else:
        if 'cancelar' not in message.text.lower():
            logger.info("Acessando escopo de remoção de cidades")
            try:
                data = load_user_date()
                user_citys = data[str(user_id)].get('city', {})
                print("User_Citys: ", user_citys)
                if user_citys:
                    print("Tipo variavel -> ", type(user_citys))
                    if message.text in user_citys:
                        print(f"{message.text} está na lista de cidades.")
                        user_citys.remove(message.text)
                        data[str(user_id)]['city'] = user_citys
                        save_user_data(data)
                        print(f'cidade {message.text} foi removida com sucesso')
                        bot.reply_to(message, f"A cidade {message.text} foi removida. Você não receberá mais notificações de oportunidades dessa cidade.")
                    else:
                        bot.reply_to(message, "A cidade que você forneceu não está correta.\n\nTente novamente inserindo o nome da cidade corretamente:")
                        bot.register_next_step_handler(message, remove_city)
                        
            except Exception as e:
                logger.exception('Erro ao remover a cidade %s, err.%s', message.text, e)

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
        

@bot.message_handler(func=lambda message: True)
def help(message):
    text = (
        f'Comando não identificado. Para acessar as funções, clique sobre os comandos ou digte-os:\n\n'
        f'/adicionar ->\n/remover ->\n/cidades_cadastradas ->\n'
    )
    bot.reply_to(message, text)