from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (ElementClickInterceptedException, TimeoutException, WebDriverException)
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from bs4 import BeautifulSoup
from time import sleep
import json
import logging
import random

# CONGIFS PARA TRATAMENTOS DE ERROS E TENTATIVAS + LOGGING
MAX_RETRIES = 3
BASE_BACKOFF = 2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_FILE = "city_data.json"

def save_city_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_city_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}



def startup(driver, city:str):   
    try:
        logger.info("abrindo o webdriver.")
        driver.get('https://www.infojobs.com.br/empregos.aspx')
        logger.info("Aceitando cookies")
        cookies_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'didomi-notice-agree-button')))
        cookies_btn.click()
        input_city = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'city')))
        input_city.clear()
        input_city.send_keys(city)
        element_city_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'autocomplete-suggestion')))
        logger.info("Confirmando a cidade.")
        element_city_option.click()
        btn_search = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-d-block')))
        logger.info("Procurando vagas.")
        btn_search.click()
        
        return BeautifulSoup(driver.page_source, 'html.parser')
    except Exception as e:
        logger.exception("Erro no startup do driver para cidade %s: %s", city, e)
        raise
    

def list_jobs(city:str):
    tries = 0
    while True:
        driver = None
        tries += 1
        try:
            options = FirefoxOptions()
            options.headless = 'eager'
            logger.info("Iniciando o webdriver para a tentativa %d.", tries)
            driver = webdriver.Firefox(options=options)
            driver.set_page_load_timeout(120)
            html_homepage = startup(driver, city)
            
            list_vagas = []            
            content = html_homepage.select_one('div.js_vacanciesGridFragment')
            if not content:
                logger.warning("Estrutura da página mudou ou nenhum conteúdo encontrado para a cidade: %s.", city)   
                return []    
            logger.info("Analisando scraper...")         
            cards = content.select('div.js_rowCard')
            for itens in cards:
                # extrair id/link de forma segura
                link_el = itens.select_one('div.js_cardLink')
                link_data_id = link_el.get('data-id') if link_el else None
                # construir link simples — pode ajustar para o formato correto do site
                link = f"{driver.current_url}&iv={link_data_id}" if link_data_id and driver else None

                job = itens.find('h2')
                empresa = itens.select_one('div.text-body > a')
                modalidade = itens.select('div.d-inline-flex > div')
                modalidade = modalidade[-1].text.strip() if modalidade else "Não informado"
                local_el = itens.select_one('div.js_cardLink > div.mb-8')
                local = local_el.text.strip() if local_el else "Não informado"
                feedback_el = itens.select_one('div.mr-8 > div.text-nowrap > span')
                feedback = feedback_el.text.strip() if feedback_el else 'Sem feedback'                
                job_name = job.text.strip() if job else "Não informado"
                empresa_name = (empresa.text.replace('\n', '').strip() if empresa else 'Empresa não informada')
                
                list_vagas.append({
                    'job': job_name,
                    'empresa': empresa_name,
                    'modalidade': modalidade,
                    'local': local,
                    'feedback': feedback,
                    'link': link
                })
                #print('Vaga: ', job_name, ' | Empresa: ', empresa_name, ' | Modalidade: ', modalidade, ' | Local: ', local, ' | Feedback: ', feedback)   
            logger.info("Dados obtidos...")
            # persiste cidade caso não exista na base de dados (usar link como id)
            data = load_city_data()
            if city not in data or not data.get(city):
                logger.info("Adicionando a cidade %s à base de dados usando 'link' como id.", city)
                city_dict = {}
                for item in list_vagas:
                    jid = item.get('link') or f"{item.get('job','')}-{item.get('empresa','')}".strip()
                    if jid:
                        city_dict[jid] = item
                if city_dict:
                    data[city] = city_dict
                    save_city_data(data)            
                
            return list_vagas
            
        except (TimeoutException, ElementClickInterceptedException, WebDriverException) as selenium_exc:
            logger.exception("Erro Selenium ao listar vagas para %s (tentativa %d): %s", city, tries, selenium_exc)
            if tries >= MAX_RETRIES:
                logger.error("Máximo de tentativas atingidos para %s", city)
                return []
            sleep_time = BASE_BACKOFF * (2 ** (tries -1)) + random.random()
            logger.info("Aguardando %.2f segundos antes de tentar novamente.", sleep_time)
            sleep(sleep_time)
            continue
        
        except Exception as e:
            logger.exception("Erro inesperado ao listar vagas para cidade %s: %s", city, e)
            return []
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

def new_job(city:str):
    try:
        data = load_city_data()
        #print("Load JSON: ", type(data), '\n', data)
        # checagem simples se cidade já está na base
        if city not in data:
            logger.info("Cidade %s ainda não presente na base de dados. Coletando pela primeira vez.", city)
            list_jobs(city)
            return None
        
        logger.info("Buscando novas vagas para cidade: %s", city)
        new_vagas = list_jobs(city)
        if not isinstance(new_vagas, list):
            logger.warning("Formato inesperado retornado por list_jobs para %s", city)
            return None

        vagas = []
        city_jobs = data[city]
        print("Debug:  \n", city_jobs)
        logger.info("Verificando existência da vaga.")
        for new_vaga in new_vagas:
            jid = new_vaga.get('link') or f"{new_vaga.get('job','')}-{new_vaga.get('empresa','')}".strip()
            if jid not in city_jobs.keys():
                logger.info("Nova vaga detectada em %s: %s, \nJID: %s\n", city, new_vaga.get('job'), jid)
                city_jobs[jid] = new_vaga
                vagas.append(new_vaga)
        
        if vagas:
            #save_city_data(data)
            logger.info("Novas vagas encontradas, retornando ->")
            return vagas
        logger.info("Nenhuma nova vaga encontrada, retornando ->")
        return None
    
    except Exception as e:
        logger.exception("Erro em new_job para %s: %s", city, e)
        return None