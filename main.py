# Imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys as SK
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import *

import os
import time
import string
import json

class Timer:
    def __init__(self, duration=10):
        self.duration = float(duration)
        self.start = time.perf_counter()
        # print("The timer has started. Self.start: " + str(self.start))

    def reset(self):
        self.start = time.perf_counter()
        # print("The timer has been reset. Self.start: " + str(self.start))

    def explode(self):
        self.duration = 0
        # print("The timer has been force-expired.")

    def increment(self, increment=0):
        self.duration += increment
        # print("The timer has been incremented by " + str(increment) + " seconds")

    @property
    def not_expired(self):
        # duration == -1 means dev wants a infinite loop/Timer
        if self.duration == -1:
            return True
        return False if time.perf_counter() - self.start > self.duration else True

    @property
    def expired(self):
        return not self.not_expired

    @property
    def at(self):
        # print("The timer is running. Self.at: " + str(time.perf_counter() - self.start))
        return time.perf_counter() - self.start


def abrir_chrome(*, 
        maximize: bool = True,
        kill_last_instance: bool = True,
        modo: str = "procurar", # Default
        path_driver: str = r"C:\BPATech\prd\chromedriver.exe", # Example 
        path_id_chrome: str = f"C:\BPATech\prd\chrome_id.json", # Example
        path_downloads: str = r"C:\BPAEngine\downloads", # Example
        exact_window_id: str = None, # CDwindow-37B07E091E9B36D94780119AD78F5407
        ):
    
    """
    Função abrir_chrome:
    
    Input:
        maximize                      #Bool: Manter navegador maximizado
        kill_last_instance            #Bool: Matar ultima instancia do chrome
        
        modo                          #Str: abrir - Instancia chrome
                                            procurar - Procurar qualquer instancia do chrome
                                            acessar - Acessar instancia a partir do exact_window_id 
        path_driver                   #Str: Path do chromedriver
        path_id_chrome                #Str: Path do chrome_id.json
        path_downloads                #Str: Path para dazer os downloads                         
        exact_window_id               #Str: id da janela a acessar, utilizar: driver.current_window_handle
        
    Output: 
        driver                        #Sucess: Conectado ao navegador com sucesso
        None                          #Error: Erro ao abrir navegador
        
    """
    
    print("\n\n[Função]--> abrir_chrome()")
    print(f"abrir_chrome() - Modo: {modo}")
    
    # Precisa para manter a sessao do Selenium aberta durante os diferente NoseTests
    global driver # NAO REMOVER O GLOBAL
    
    # Configurações para abrir novo navegador
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('prefs', {
    "download.default_directory": path_downloads, #Change default directory for downloads
    "download.prompt_for_download": False, #To auto download the file
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
    })
        
    # Se não existir path_id_chrome, criar o arquivo
    if not os.path.isfile(path_id_chrome):
        os.mkdir(path_id_chrome)
        print(f"abrir_chrome() - Arquivo criado: {path_id_chrome}")
    
    # Dados da sessão anterior
    retorno_session_data = get_session_data(path_id_chrome=path_id_chrome)
    
    # Validar sucesso da função get_session_data
    if retorno_session_data["status_code"] == 0:
        session_id = retorno_session_data["session_id"]
        remote_machine_url = retorno_session_data["remote_machine_url"]
    
    #------------------------------------------------------------------------------------------------
    # Procurar qualquer sessão ja existente a partir do chrome_id, se não encontrar deve abrir
    if modo == "procurar" and session_id:
        print(f"abrir_chrome() - Aproveitando sessão já aberta do chrome: {session_id}")
        
        # Acessar navegador aberto
        retorno_attach_to_session = attach_to_session(
            executor_url=remote_machine_url, 
            session_id=session_id)

        # Acessar navegador encontrado
        if retorno_attach_to_session["status_code"] == 0:
            driver = retorno_attach_to_session["driver"]
            
            try:
                # Se conseguir acessar a sessão com id correto
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    break
                    
                print(f"abrir_chrome() - Procurar - Titulo da aba encontrada: {driver.title}")
                return driver
            
            except Exception as e:
                print(f"abrir_chrome() - Erro procurar: acessar janela: {e}")

        # Se não encontrar um navegador
        else:
            print(f"abrir_chrome() - Error procurar - attach_to_session: {retorno_attach_to_session['exception']}")
    
    elif modo == "procurar" and session_id is None:
        print("abrir_chrome() - Erro session_id não encontrado!")
        
    #------------------------------------------------------------------------------------------------
    # Acessar uma sessão ja existente a partir do exact_window_id
    elif modo == "acessar" and exact_window_id:
        print(f"abrir_chrome() - exact_window_id: {exact_window_id}")
            
        # Acessar navegador aberto
        retorno_attach_to_session = attach_to_session(
            executor_url=remote_machine_url, 
            session_id=session_id)
        
        # Acessar navegador encontrado
        if retorno_attach_to_session["status_code"] == 0:
            driver = retorno_attach_to_session["driver"]
            
            # Se conseguir acessar a sessão com exact_window_id
            try:
                driver.switch_to.window(exact_window_id)
                print(f"abrir_chrome() - Acessar - Titulo da aba encontrada: {driver.title}")
                return driver
            
            except Exception as e:
                print(f"abrir_chrome() - Erro acessar: acessar janela: {e}")
            
        # Se não encontrar um navegador
        else:
            print(f"abrir_chrome() - Error acessar - attach_to_session: {retorno_attach_to_session['exception']}")
    
    # Se não encontrar o exact_window_id
    elif modo == "acessar" and exact_window_id is None:
        print("abrir_chrome() - Erro exact_window_id não definido!")
        
    #------------------------------------------------------------------------------------------------
    # Abrir nova sessão do chrome
    # Matar antiga sessão
    if kill_last_instance:
        try:
            os.system("taskkill /f /im chromedriver.exe")
            print("abrir_chrome() - Matou o antigo navegador...")
        except:
            print("abrir_chrome() - Não matou o antigo navegador...")

    # Abrindo novo selenium
    driver = webdriver.Chrome(executable_path=path_driver, chrome_options=options)
    print("abrir_chrome() - Abrindo novo selenium...")
    
    driver.execute_cdp_cmd('Network.setUserAgentOverride', 
        {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
    )

    # Maximizar navegador
    if maximize:
        driver.maximize_window()

    # Pegar ip da sessão: http://127.0.0.1:64503
    remote_machine_url = driver.command_executor._url
    
    # Pegar id da sessão: b163b53a9477b302568704a780103fec
    session_id = driver.session_id
    
    # Concatenar valores para salvar como string no path_id_chrome
    session_id_as_str = f'{remote_machine_url} {session_id}'

    # Salvar id da sessão atual
    with open(path_id_chrome, "w") as file:
        file.write(session_id_as_str)
    
    # Sucesso
    print("abrir_chrome() - Conectado ao navegador com sucesso!")
    return driver

    
def attach_to_session(*, executor_url: str, session_id: str):
    """
    Input:
        executor_url              #Str: http://127.0.0.1:64503 
        session_id                #Str: b163b53a9477b302568704a780103fec
        
    Output:
        0                         #Success: Sessão encontrada
        -1                        #Error: Sessão não encontrada
    
    """
    print("\n\n[Função]--> attach_to_session()")
    
    # Acessar chrome ja existente 
    try:
        driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
        driver.close()
        driver.session_id = session_id
        driver.implicitly_wait(0) # seconds
        print("attach_to_session() - Sessão encontrada!")
        return {"status_code": 0, "driver": driver}
    
    except Exception as e:
        print("attach_to_session() - Sessão não encontrada!")
        return {"status_code": -1, "driver": None, "exception": e}
    

def get_session_data(*, path_id_chrome: str):
    """
    Input:
        path_id_chrome            #Str: Path do chrome_id
        
    Output:
        0                         #Success: Dados da sessão encontrados
        -1                        #Error: Erro dados da sessão nulos
        -2                        #Error: Erro dados da sessão não encontrados
    """
    
    print("\n\n[Função]--> get_session_data()")
    
    timer = Timer(10)
    while timer.not_expired:
        # Ler arquivo
        with open(path_id_chrome, "r") as file:
            session_id_as_str = file.read()

            # Verificar se é nulo
            if len(session_id_as_str) == 0:
                print("get_session_data() - Erro dados da sessão nulos!")
                return {"status_code": -1, "remote_machine_url": False, "session_id": False}

            # Se encontrar dados
            try:
                remote_machine_url, session_id = session_id_as_str.split(" ")
                print("get_session_data() - Dados da sessão encontrados!")
                return {"status_code": 0, "remote_machine_url": remote_machine_url, "session_id": session_id}
            
            except:
                pass
            
    # Timeout
    if timer.expired:
        print("get_session_data() - Erro dados da sessão não encontrados!")
        return {"status_code": -2, "remote_machine_url": False, "session_id": False}
    

def login_instagram(*, driver, dados: dict, url: str, title: str = "Instagram"):
    """
    Input: 
        driver      #WebDriver: driver do navegador
        dados       #Dict: dados de login e senha
        url         #Str: url a acessar
        title       #Str: titulo da pagina

    Output: 
        0           #Success: Clicou no botão rejeitar login com sucesso
        -1          #Error: Erro ao acessar instagram
        -2          #Error: Erro ao encontrar inputs login e senha
        -3          #Error: Erro ao encontrar botão login
        -4          #Error: Erro ao encontrar botão rejeitar salvar login
    """

    print("login_instagram() - INICIO")

    driver.get(url)

    # Validar url
    timer = Timer(10)
    while timer.not_expired:
        if title in driver.title:
            print("login_instagram() - Acessou a pagina com sucesso!")
            break

        time.sleep(1)
    
    if timer.expired:
        return {
            "status_code": -1,
            "mensagem": "login_instagram() - Erro ao acessar instagram!"
        }

    # Inserir username
    timer = Timer(20)
    while timer.not_expired:
        try:
            # Username
            driver.find_element_by_name("username").clear()
            driver.find_element_by_name("username").send_keys(dados["user"])

            # Password
            driver.find_element_by_name("password").clear()
            driver.find_element_by_name("password").send_keys(dados["pass"])
            print("login_instagram() - Inputs encontrados com sucesso!")
            break

        except:
            print("login_instagram() - Inputs não encontrados, tentando novamente...")
            time.sleep(1)

    if timer.expired:
        return {
            "status_code": -2,
            "mensagem": "login_instagram() - Erro ao encontrar inputs login e senha!"
        }

    # Clicar no login
    timer = Timer(10)
    while timer.not_expired:
        try:
            # Button login
            driver.find_elements_by_tag_name("button")[1].click()
            print("login_instagram() - Clicou no botão login com sucesso!")
            break

        except:
            print("login_instagram() - Botão login não encontrado, tentando novamente...")
            time.sleep(1)

    if timer.expired:
        return {
            "status_code": -3,
            "mensagem": "login_instagram() - Erro ao encontrar botão login!"
        }
        
    # Rejeitar salvar login
    timer = Timer(20)
    while timer.not_expired:
        try:
            driver.find_elements_by_tag_name("button")[1].click()
            print("login_instagram() - Clicou no botão rejeitar login com sucesso!")
            break
        except:
            print("login_instagram() - Botão rejeitar não encontrado, tentando novamente...")
            time.sleep(1)
            
    if timer.expired:
        return {
            "status_code": -4,
            "mensagem": "login_instagram() - Erro ao encontrar botão rejeitar salvar login!"
        }

    print("login_instagram() - FIM")
    return {
        "status_code": 0,
        "mensagem": "login_instagram() - Concluiu a função com sucesso!"
    }


def comentar(*, 
        driver, 
        url: str, 
        pessoas_por_comentario: int = 1,
        title: str = "a",
        test: bool = False, 
        list_nomes_adicionados: list = []
        ):
    """
    Input:
        driver                       #WebDriver: driver do navegador
        url                          #Str: url do sorteio
        pessoas_por_comentario       #Int: total de pessoas por comentario
        title                        #Str: titulo que contem na pagina

    Output:
        0                            #Success:
        -1                           #Error:
        -2                           #Error:

    """

    print("comentar() - INICIO")

    driver.get(url)

    # Validar url
    timer = Timer(10)
    while timer.not_expired:
        if title in driver.title:
            print("comentar() - Acessou a pagina com sucesso!")
            break

        time.sleep(1)
    
    if timer.expired:
        return {
            "status_code": -1,
            "mensagem": "comentar() - Erro ao acessar post do sorteio!"
        }
    
    # Gerar todas letras do alfabeto
    letras = list(string.ascii_lowercase)

    count_pessoas = pessoas_por_comentario
    
    # Inserir primeira letra
    for letra_1 in letras:
        # Inserir '@' e uma letra
        texto = "@" + letra_1
        
        # Inserir segunda letra
        for letra_2 in letras:
            # Inserir comentario no instagram
            retorno_validar_comentario = validar_comentario(
                driver=driver, 
                texto=f'{texto}{letra_2}', 
            )
            
            # Sucesso
            if retorno_validar_comentario["status_code"] == 0:
                print(retorno_validar_comentario["mensagem"])
                texto_digitado = retorno_validar_comentario["resposta"]

            # Erro
            else:
                if isinstance(retorno_validar_comentario, dict):
                    print("\n##########################################")
                    print("ERRO")
                    print(retorno_validar_comentario["mensagem"])
                    print("\n##########################################")

                # Apagar até o espaço: ' '
                while driver.find_elements_by_tag_name("textarea")[0].text[-1] != " ":
                    driver.find_elements_by_tag_name("textarea")[0].send_keys(SK.BACKSPACE)
                continue

            # Se a pessoa ja existe
            if texto_digitado in list_nomes_adicionados:
                print(f"comentar() - {texto_digitado} ja existe na lista")
                # Apagar até o espaço: ' '
                while driver.find_elements_by_tag_name("textarea")[0].text[-1] != " ":
                    driver.find_elements_by_tag_name("textarea")[0].send_keys(SK.BACKSPACE)
                continue
            else:
                print(f"comentar() - {texto_digitado} inserido na lista")
                count_pessoas -= 1
                list_nomes_adicionados.append(texto_digitado)
            
            # Digitar espaço
            #driver.find_elements_by_tag_name("textarea")[0].send_keys(" ")
            
            print(f'comentar() - Nomes ja adicionados: {list_nomes_adicionados}')

            # Se digitar todas pessoas
            if count_pessoas == 0:
                count_pessoas = pessoas_por_comentario
                if test:
                    print("------------------------------------------")
                    print("comentar() - Apagou tudo")
                    driver.find_elements_by_tag_name("textarea")[0].clear()
                    time.sleep(5)
                    print()
                    print()
                else:
                    print("------------------------------------------")
                    print("comentar() - Enviou o comentario")
                    driver.find_elements_by_tag_name("textarea")[0].send_keys(SK.RETURN)
                    time.sleep(5)
                    print()
                    print()

    print("comentar() - FIM")
    return {
        "status_code": 0,
        "mensagem": "comentar() - Concluiu a função com sucesso!",
        "resposta": list_nomes_adicionados
    }


def validar_comentario(*, driver, texto: str):
    """
    Input:
        driver           #WebDriver: driver do navegador
        texto            #Str: texto a ser inserido

    Output:
        0                #Success: Pessoa validada com sucesso
        -1               #Error: Erro textarea não encontrado
        -2               #Error: Erro o texto não foi inserido
        -3               #Error: Erro não pressionou 2x ENTER
        -4               #Error: Erro texto não encontrado: ' '
        -5               #Error: Erro nenhuma pessoa encontrada

    """
    
    print("validar_comentario() - INICIO")
    print("------------------------------------------")
    print(f'validar_comentario() - Texto inicio: {texto}')

    # Escrever comentario
    timer = Timer(10)
    while timer.not_expired:
        try:
            driver.find_elements_by_tag_name("textarea")[0].send_keys(" " + texto)
            print("validar_comentario() - Escreveu o texto no textarea!")

            # Tempo de inserir nome
            time.sleep(2)
            break
        except:
            time.sleep(1)

    if timer.expired:
        return {
            "status_code": -1,
            "mensagem": "validar_comentario() - Erro textarea não encontrado!"
        }

    # Validar se o texto foi inserido
    if driver.find_elements_by_tag_name("textarea")[0].text.split(" ")[-1] == texto:
        print("validar_comentario() - Texto validado com sucesso!")
        print(f'validar_comentario() - Texto valido: {driver.find_elements_by_tag_name("textarea")[0].text.split(" ")[-1]}')

    else:
        print(f'validar_comentario() - Texto invalido: {driver.find_elements_by_tag_name("textarea")[0].text.split(" ")[-1]}')
        return {
            "status_code": -2,
            "mensagem": "validar_comentario() - Erro ultimo texto invalido!"
        }

    # Pressionar enter 2 vezes
    try:
        driver.find_elements_by_tag_name("textarea")[0].send_keys(SK.RETURN)
        driver.find_elements_by_tag_name("textarea")[0].send_keys(SK.RETURN)
        time.sleep(1)
        print("validar_comentario() - Pressionou 2x ENTER")
    except:
        return {
            "status_code": -3,
            "mensagem": "validar_comentario() - Erro não pressionou 2x ENTER!"
        }

    # Apagar até o espaço: ' '
    # Para funcionar o .split(" ")[-1]
    while driver.find_elements_by_tag_name("textarea")[0].text[-1] == " ":
        driver.find_elements_by_tag_name("textarea")[0].send_keys(SK.BACKSPACE)

    # Aguardar pessoa inserida
    timer = Timer(10)
    while timer.not_expired:
        ultimo_texto = driver.find_elements_by_tag_name("textarea")[0].text.split(" ")[-1]
        try:
            if not ultimo_texto in [texto, " "]:
                print("validar_comentario() - Pessoa encontrada com sucesso!")
                print(f'validar_comentario() - Pessoa encontrada: {driver.find_elements_by_tag_name("textarea")[0].text.split(" ")[-1]}')
                break
        except:
            time.sleep(1)

    if ultimo_texto in ["", ""]:
        return {
            "status_code": -4,
            "mensagem": "validar_comentario() - Erro texto não encontrado: ' '!"
        }

    if timer.expired:
        return {
            "status_code": -5,
            "mensagem": "validar_comentario() - Erro nenhuma pessoa encontrada!"
        }
        
    print(f'validar_comentario() - Linha completa: {driver.find_elements_by_tag_name("textarea")[0].text}')
    print("validar_comentario() - FIM")

    return {
        "status_code": 0,
        "mensagem": "validar_comentario() - Pessoa validada com sucesso!",
        "resposta": driver.find_elements_by_tag_name("textarea")[0].text.split(" ")[-1]
    }


def salvar_usuarios_utilizados(list_nomes_adicionados: list):
    """
    Input:
        list_nomes_adicionados      #List: lista de nomes
    
    Output:
        0                           #Success: Salvo com sucesso
        -1                          #Erro ao salvar dados

    """
    print("salvar_usuarios_utilizados() - INICIO")

    try:
        with open("data.txt", "w") as arq:
            arq.write(json.dumps(list_nomes_adicionados))
    except:
        return {
            "status_code": -1,
            "mensagem": "salvar_usuarios_utilizados() - Erro ao salvar dados!"
        }
        
    return {
        "status_code": 0,
        "mensagem": "salvar_usuarios_utilizados() - Dados salvos com sucesso!"
    }

def ler_usuarios_utilizados():
    """
    Input:
        None

    Output:
        0                           #Success: Dados encontrados com sucesso
        -1                          #Erro ao ler dados

    """
    print("ler_usuarios_utilizados() - INICIO")

    try:
        with open("data.txt", "r") as arq:
            texto = json.loads(arq.read())
    except:
        return {
            "status_code": -1,
            "mensagem": "ler_usuarios_utilizados() - Erro ao ler dados!"
        }
        
    return {
        "status_code": 0,
        "mensagem": "ler_usuarios_utilizados() - Dados encontrados com sucesso!",
        "resposta": texto
    }


def main():
    #_______________________________________________________________
    #---------------------Preparar ambiente-------------------------
    #_______________________________________________________________
    url_instagram: str = "https://www.instagram.com/accounts/login"
    url_post: str = "https://www.instagram.com/p/CQhBk2aDclA"
    pessoas_por_comentario = 3
    ler_dados = True
    modo_test = False

    dados: dict = {
        "user": "your_username",
        "pass": "your_password"
    }

    #_______________________________________________________________
    #--------------------------Ler dados----------------------------
    #_______________________________________________________________
    if ler_dados:
        retorno_ler_usuarios_utilizados = ler_usuarios_utilizados()

        # Sucesso
        if retorno_ler_usuarios_utilizados["status_code"] == 0:
            print(retorno_ler_usuarios_utilizados["mensagem"])
            list_nomes_adicionados = retorno_ler_usuarios_utilizados["resposta"]
            print("---------------------------------------")
            print(f"Lista encontrada: {list_nomes_adicionados}")

        # Erro mapeado
        elif isinstance(retorno_ler_usuarios_utilizados, dict):
            print(retorno_ler_usuarios_utilizados["mensagem"])
            return
        
        # Erro não mapeado
        else:
            print(f"ler_usuarios_utilizados() - Erro não mapeado: {retorno_ler_usuarios_utilizados}")
            return
    else:
        list_nomes_adicionados = []

    if list_nomes_adicionados in ["", " ", None]:
        list_nomes_adicionados = []

    #_______________________________________________________________
    #-----------------------Login instagram-------------------------
    #_______________________________________________________________
    driver = abrir_chrome(
        path_driver=r"C:\BPATech\prd\chromedriver.exe", # Example 
        path_id_chrome=r"C:\BPATech\prd\chrome_id.json", # Example
    )

    retorno_login_instagram = login_instagram(
        driver=driver,
        dados=dados,
        url=url_instagram
    )

    # Sucesso
    if retorno_login_instagram["status_code"] == 0:
        print(retorno_login_instagram["mensagem"])
    
    # Erro mapeado
    elif isinstance(retorno_login_instagram, dict):
        print(retorno_login_instagram["mensagem"])
        return

    # Erro não mapeado
    else:
        print(f"login_instagram() - Erro não mapeado: {retorno_login_instagram}")
        return

    #_______________________________________________________________
    #-----------------------Comentar post---------------------------
    #_______________________________________________________________
    retorno_comentar = comentar(
        driver=driver, 
        url=url_post, 
        pessoas_por_comentario=pessoas_por_comentario, 
        test=modo_test,
        list_nomes_adicionados=list_nomes_adicionados
    )

    # Sucesso
    if retorno_comentar["status_code"] == 0:
        print(retorno_comentar["mensagem"])
        list_nomes_adicionados = retorno_comentar["resposta"]
    
    # Erro mapeado
    elif isinstance(retorno_comentar, dict):
        print(retorno_comentar["mensagem"])
        return
    
    # Erro não mapeado
    else:
        print(f"comentar() - Erro não mapeado: {retorno_comentar}")
        return
    
    #_______________________________________________________________
    #--------------------------Salvar dados-------------------------
    #_______________________________________________________________
    retorno_salvar_usuarios = salvar_usuarios_utilizados(list_nomes_adicionados)

    # Sucesso
    if retorno_salvar_usuarios["status_code"] == 0:
        print(retorno_salvar_usuarios["mensagem"])

    # Erro mapeado
    elif isinstance(retorno_salvar_usuarios, dict):
        print(retorno_salvar_usuarios["mensagem"])
        return
    
    # Erro não mapeado
    else:
        print(f"salvar_usuarios_utilizados() - Erro não mapeado: {retorno_salvar_usuarios}")
        return

    print("--------------------------------------------------------")
    print("--------------------------------------------------------")
    print("main() - Robo finalizado com sucesso")


if __name__ == '__main__':
    main()
