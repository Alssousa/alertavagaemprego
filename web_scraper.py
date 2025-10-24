from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from time import sleep


vagas = []

def startup(city:str):   
    try:
        driver = webdriver.Firefox()
        driver.get('https://www.infojobs.com.br/empregos.aspx')
    except Exception as e:
        print("Erro ao iniciar o navegador ou acessar o site:", e)
        raise e
    sleep(2)
    cookies_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'didomi-notice-agree-button')))
    cookies_btn.click()
    try:
        input_city = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'city')))
        input_city.clear()
        input_city.send_keys(city)
    except Exception as e:
        print("Erro ao localizar o campo de cidade:", e)
        raise e
    try:
        element_city_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'autocomplete-suggestion')))
        element_city_option.click()
    except Exception as e:
        print("Erro ao selecionar a cidade sugerida:", e)
        raise e
    btn_search = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-d-block')))
    btn_search.click()
    sleep(2)
    
    return BeautifulSoup(driver.page_source, 'html.parser'), driver
    

def list_jobs(html_homepage, driver:webdriver.Firefox):
    list_vagas = []
    content = html_homepage.select_one('div.js_vacanciesGridFragment')
    print('tamanho: ', len(content), 'type: ', type(content))
    content = content.select('div.js_rowCard')
    for itens in content:
        job = itens.find('h2')
        empresa = itens.select_one('div.text-body > a')
        modalidade = itens.select('div.d-inline-flex > div')
        modalidade = modalidade[-1].text.strip()
        local = itens.select_one('div.js_cardLink > div.mb-8').text.strip()
        feedback = (itens.select_one('div.mr-8 > div.text-nowrap > span').text.strip() if itens.select_one('div.mr-8 > div.text-nowrap > span') else 'Sem feedback')
        ''' 
            adicionar link da vaga -> pegar um link predefinido com a localização da vaga + &iv=data-id da vaga
        '''
        
        job_name = job.text.strip()
        empresa_name = (empresa.text.replace('\n', '').strip() if empresa else 'Empresa não informada')
        list_vagas.append({'job': job_name, 'empresa': empresa_name, 'modalidade': modalidade, 'local': local, 'feedback': feedback})
        print('Vaga: ', job_name, ' | Empresa: ', empresa_name, ' | Modalidade: ', modalidade, ' | Local: ', local, ' | Feedback: ', feedback)
        #sleep(1)
    driver.quit()
    
    return list_vagas

def new_job():
    html_homepage, driver = startup()
    vagas.pop(0)  # remover a primeira vaga para teste
    print("Buscando novas vagas...")
    new_vagas = list_jobs(html_homepage, driver)
    new_vagas.append({'job': 'TECNICO PCM I (PCD)', 'empresa': 'GRUPO    SELPE', 'modalidade': 'Remoto', 'local': 'Imperatriz - MA, 0 Km de você.', 'feedback': '4,4'})
    print("verificando novas vagas...")
    for i, new_vaga in enumerate(new_vagas):
        print(f'vaga {i}: ', new_vaga)
        #[vagas.append(new_vaga) if new_vaga['job'] not in [vaga['job'] for vaga in vagas] else print(f"Vaga {new_vaga['job']} já cadastrada.")]
        if new_vaga not in vagas:
            vagas.append(new_vaga)
            print(f"\n\nNova vaga cadastrada: {new_vaga['job']}, Empresa: {new_vaga['empresa']}")
            ################ AÇÃO DE ALERTA PARA NOVA VAGA AQUI ################

    


# teste
startup('imperatriz')