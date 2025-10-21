from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from time import sleep


driver = webdriver.Firefox()

def startup():   
    driver.get('https://www.infojobs.com.br/empregos.aspx?poblacion=5204517')
    sleep(2)
    cookies_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'didomi-notice-agree-button')))
    cookies_btn.click()
    
    return BeautifulSoup(driver.page_source, 'html.parser')

def list_jobs(html_homepage):
    content = html_homepage.select_one('div.js_vacanciesGridFragment')
    print('tamanho: ', len(content), 'type: ', type(content))
    content = content.select('div.js_rowCard')
    for itens in content:
        job = itens.find('h2')
        empresa = itens.select_one('div.text-body > a')
        modalidade = itens.select('div.d-inline-flex > div')
        modalidade = modalidade[-1].text.strip()
        local = itens.select_one('div.js_cardLink > div.mb-8').text.strip()
        feedback = itens.select_one('div.mr-8 > div.text-nowrap > span').text.strip()
        ''' 
            adicionar link da vaga -> pegar um link predefinido com a localização da vaga + &iv=data-id da vaga
        '''
        
        job_name = job.text.strip()
        empresa_name = empresa.text.replace('\n', '').strip()

        print('Vaga: ', job_name, ' | Empresa: ', empresa_name, ' | Modalidade: ', modalidade, ' | Local: ', local, ' | Feedback: ', feedback)
        sleep(5)

# teste 
html_homepage = startup()
list_jobs(html_homepage)