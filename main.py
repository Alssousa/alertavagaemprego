import threading
import time
from web_scraper import startup, list_jobs, new_job
from telegram_bot import bot, load_user_date, send_alert_new_job

data = load_user_date()
CHECK_INTERVAL = 2000


def verify_new_jobs(city:str, user_id):
    print("Verificando novas vagas...")
    update = new_job(city)
    if update:
        print(f"\n\nNovas vagas encontradas para a cidade {city}: ", update)
        for vaga in update:
            send_alert_new_job(user_id, vaga)
    

def scraper_loop():
    while True:
        try:
            for user_id, item in data.items():
                citys = item['city']
                print("Dentro 1")
                if citys:
                    for city in citys:
                        print("Execuntando scraper")
                        verify_new_jobs(city, user_id)
        except Exception as e:
            print("Erro ao executar o loop do scraper..: ", e)
        time.sleep(CHECK_INTERVAL)
                    

######### EXECUTABLE CODE ##########

if __name__ == "__main__":
    t = threading.Thread(target=scraper_loop, daemon=True)
    #t.start()
    
    bot.infinity_polling()
    