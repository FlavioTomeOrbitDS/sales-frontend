import streamlit as st
import pandas as pd
import requests
from openai import OpenAI
from PIL import Image
import io
import base64
import concurrent.futures
import os
from dotenv import load_dotenv

load_dotenv()
# Lê a variável API_KEY
api_key = os.getenv("API_KEY")


base_url = "http://37.60.254.26:8080"
#base_url = "http://127.0.0.1:5000"
#base_url = "https://8080-cs-762104477964-default.cs-us-east1-dogs.cloudshell.dev"

# Funções que você já tem definidas
def get_dataframe_length():
    response = requests.get(f"{base_url}/getdataframelen")
    if response.status_code == 200:
        return response.json()
    else:
        return "Erro ao obter dados"

def get_dataframe():
    response = requests.get(f"{base_url}/getmessages")
    if response.status_code == 200:
        data = response.json()
        
        # Converte diretamente a lista de dicionários para um DataFrame
        dataframe = pd.DataFrame(data)
        return dataframe
    else:
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
        st.error("Erro ao obter a resposta da api")
    
def reinicia_dataframe():
    response = requests.get(f"{base_url}/apagadf")
    if response.status_code == 200:
        return "DataFrame apagado com sucesso."
    else:
        return "Erro ao apagar o DataFrame."

def start_process_request():
    """
    Função que faz a requisição para iniciar o processo.
    """
    try:
        response = requests.get(f"{base_url}/startprocess", timeout=2)
        if response.status_code == 200:
            return "Processo iniciado."
        else:
            return f"Erro: Status {response.status_code} ao conectar a API."
    except requests.Timeout:
        return "Erro: A requisição excedeu o tempo limite (Timeout)."
    except requests.RequestException as e:
        return f"Erro: Falha na conexão com a API. Detalhes: {str(e)}"

def start_process():
    """
    Executa a função de requisição em uma thread separada para evitar bloqueios.
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(start_process_request)
        try:
            result = future.result(timeout=1)  # Timeout para a execução da thread
            return result
        except concurrent.futures.TimeoutError:
            return "Erro: O tempo limite foi excedido na execução."

def gera_resposta(text):
    
    return f"Olá {text}"

# Função que usa o GPT-4 para gerar uma resposta com base na conversa
def gerar_resposta_openai(nome):
    """
    Função que utiliza o modelo GPT-4 para gerar a próxima resposta baseada no histórico da conversa.
    """
    #filtra o dataframe conforme o contato e Constrói o histórico da conversa em formato adequado para a API OpenAI
    #df_filtrado = data[data['nome_contato'] == nome]        
    
    base_training = """ 1. Requisitos Funcionais
- *Cadastro de Clientes*: 
  - O cliente deve poder se registrar e criar uma conta.
  - Sistema deve suportar autenticação (ex: JWT, OAuth).
  
- *Gerenciamento de Números de WhatsApp*:
  - O cliente pode cadastrar e gerenciar múltiplos números de WhatsApp.
  - Cada número deve ser associado a um vendedor específico.
  - Conversas de Whastsapp pode ser dado seguimento por vendedores diferentes, ou seja a conversa pode ser iniciada por um 
  vendedor, mas pode ser dado seguimento por outro. 
  
- *Recebimento e Processamento de Mensagens*:
  - Integrar com a API do WhatsApp para receber mensagens.
  - As mensagens devem ser processadas em tempo real para a analise da I.A(Já temos a I.A).
  - As conversas devem ser armazenadas para futuras analises ou mesmo futuras tratativas com o prospecto.
  
- *Análise de Mensagens*:
  - Atualmente ja temos um modelo que vai trabalhar com as ações que devem ser dadas para o 
  front-end. devemos apenas trabalhar com o consumo de uma API para 
  fornecer as informações e ações.
  - A I.A deve ter uma base para cada perfil de cliente, pois os tipos de produtos são diferentes,
  logo cada tenant(Cliente) terá sua configuração de I.A inicial configurada, mas deverá ter seu treinamento separado para 
  melhor atendimento do cliente.  
  
- *Dashboard de Vendas*:
  - Interface para que o cliente visualize as mensagens e a classificação da IA.
  - Relatórios sobre potencial de vendas e métricas de desempenho.

### 2. Requisitos Não Funcionais
- *Escalabilidade*:
  - Sistema deve suportar múltiplos clientes simultaneamente.
  - Uso de contêineres (Docker, Kubernetes) para facilitar a escalabilidade.
  - Devemos ter uma aplicação para criação destes clientes onde 
  uma rotina irá colocar eles em produção on-demand.

- *Segurança*:
  - Dados dos clientes devem ser isolados (multi-tenancy).
  - Implementar criptografia para dados sensíveis(LGPD).

- *Desempenho*:
  - O sistema deve processar mensagens em tempo real ou quase em tempo real.
  
- *Manutenção*:
  - Sistema de logs para monitoramento e troubleshooting."""
    
    df_filtrado = st.session_state.df[st.session_state.df['nome_contato'] == nome]        
    
    
    historico_conversa = []    

    # Adiciona uma mensagem inicial do sistema para definir o comportamento do assistente
    historico_conversa.append({
        'role': 'system',
        #'content': """Você é um assistente de vendas da Sales IA. Cumprimente a pessoa chamando pelo nome e a ajude com o que ela precisar"""    })
        'content': f"""Você é um assistente de vendas da Sales IA. Aja conforme o treinamento e realize as seguintes tarefas:
        1. Informe qual a melhor resposta para a mensagem do cliente.
        2. informe a probabilidade da venda.
        3. informe o sentimento expressado pelo usuário (positivo, negativo, interessado, descontente...).
        Observação: Não utilize emojis ou caracteres fora do Basic Multilingual Plane (BMP). 
        Treinamento : {base_training}        
        Output: Um markdown no seguinte formato: 
        ### Probabilidade de venda
        ### Sentimento do Cliente
        ### Resposta sugerida"""    })
    
    if st.session_state.model_training != "":
        historico_conversa.append({
        'role': 'system',        
        'content': st.session_state.model_training})
        

    # Adiciona o histórico de mensagens da conversa
    for index, row in df_filtrado.iterrows():
        role = row['role']
        mensagem = row['mensagem']

        historico_conversa.append({
            'role': role,
            'content': mensagem
        })
                    
    # Faz a chamada à API da OpenAI para gerar a resposta
    try:
        client = OpenAI(api_key=api_key)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=historico_conversa,
            temperature= st.session_state.model_temperature
        )

        
        
        
        resposta =  completion.choices[0].message.content
        
        print(resposta)
        #json_content = json.loads(completion.choices[0].message.content)        
        #print(json_content)
        
        #return completion.choices[0].message.content
        return resposta
    
    except Exception as e:
        print(e)
        st.error(f"Erro ao gerar resposta com a OpenAI: {str(e)}")
        return "Erro ao gerar resposta."
    

# insere a mensagem enviada no dataframe de mensagens do backend
def insertmessagedataframe(nome_contato, mensagem):
    url = f"{base_url}/insertmessagedataframe"
    payload = {
        "nome_contato": nome_contato,
        "mensagem": mensagem,
        "role": "assistant"  # Adiciona o campo 'role' com valor 'assistant'
    }
    
    headers = {"Content-Type": "application/json"}
    
    # Envia a solicitação POST para o backend
    response = requests.post(url, json=payload, headers=headers)
    
    # Verifica a resposta do servidor
    if response.status_code != 200:
        st.error(f"Erro ao salvar a mensagem. Status: {response.status_code}")
    
        

# Função para enviar a mensagem para o endpoint Flask
def send_message_to_backend(nome_contato, mensagem):
    url = f"{base_url}/sendmessage"
    payload = {
        "nome_contato": nome_contato,
        "mensagem": mensagem,
        "role": "assistant"  # Adiciona o campo 'role' com valor 'assistant'
    }
    
    headers = {"Content-Type": "application/json"}
    
    # Envia a solicitação POST para o backend
    response = requests.post(url, json=payload, headers=headers)
    
    # Verifica a resposta do servidor
    if response.status_code == 200:
        #st.success("Mensagem enviada com sucesso!")
        insertmessagedataframe(nome_contato, mensagem)
    else:
        st.error(f"Erro ao enviar a mensagem. Status: {response.status_code}")

def verificar_conectado():
    """
    Faz uma chamada ao endpoint /verifyconnected e retorna o status da conexão.
    """
    url = f"{base_url}/verifyconnected"  # Ajuste conforme o URL do servidor

    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json().get('result')            
            return result
        else:
            st.error("Erro na chamada ao servidor!")
            return "Erro ao verificar a conexão."
    except Exception as e:
        st.error(f"Erro ao conectar ao servidor: {str(e)}")
        return "Erro ao conectar ao servidor."
    
def obter_qr_code():
    """
    Faz uma chamada ao endpoint /getqrcode e retorna a imagem do QR code.
    """
    url = f"{base_url}/getqrcode"  # Ajuste para o URL correto do seu servidor
    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json().get('result')
            if result and result != 'Erro ao gerar qr code!':
                # Decodifica a imagem em base64 para exibir no Streamlit
                qr_image = Image.open(io.BytesIO(base64.b64decode(result)))
                return qr_image
            else:
                st.error("Erro ao gerar o QR code!")
                return None
        else:
            st.error("Erro na chamada ao servidor!")
            return None
    except Exception as e:
        st.error(f"Erro ao conectar ao servidor: {str(e)}")
        return None

    # Função para chamar o endpoint /resetmessages
def reset_messages():
    try:
        response = requests.get(f"{base_url}/resetmessages")
        response.raise_for_status()  # Levanta um erro se a requisição falhar
        data = response.json()
        return data.get("result", "Nenhum resultado encontrado.")
    except requests.RequestException as e:
        return f"Erro ao conectar-se ao servidor: {e}"


def verify_new_message():    
    if st.session_state.status_conexao == 200:
        df = get_dataframe()
        if not st.session_state.df.equals(df):
            st.session_state.df = df
            ultima_linha = st.session_state.df.iloc[-1]
            nome = ultima_linha["nome_contato"]
            role = ultima_linha["role"]
            if role != 'assistant':
                st.toast(f'Você tem uma nova mensagem de {nome}!', icon='🔔')                        
                # Se a nova mensagem for do chat atual, atualiza a resposta da IA
                if nome == st.session_state.selected_name:
                    st.session_state.resposta_openai = gerar_resposta_openai(st.session_state.selected_name)                                   
                
            return True
        else:
            return False

def init_session_state():    
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame()
    if 'df_ia_analysis' not in st.session_state:
        data = [{"nome" : '', "analise" : ''}]
        st.session_state.df_ia_analysis = pd.DataFrame(data=data)

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'selected_name' not in st.session_state:
        st.session_state.selected_name = ''
    
    if 'status_conexao' not in st.session_state:
        st.session_state.status_conexao = 500
    
    if 'resposta_openai' not in st.session_state:
        st.session_state.resposta_openai = ''
    
    if 'started_scrapping_process' not in st.session_state:
       st.session_state.started_scrapping_process = False
        
    if 'model_temperature' not in st.session_state:
       st.session_state.model_temperature = 0.1
    
    if 'model_training' not in st.session_state:
       st.session_state.model_training = " "
        

def build_contact_area(unique_names):    
    for i in unique_names:
            #mostra o nome do contato
            st.markdown(f"**{i}**:")
            col_last_message, col_view_button = st.columns([3, 1])
            with col_last_message:
                #mostra a ultima mensagem
                last_message = st.session_state.df[st.session_state.df['nome_contato'] == i].iloc[-1]['mensagem']
                st.write(last_message)
            with col_view_button:
                #Botao Ver mensagens
                if st.button("Ver", key=f"btn_{i}"):
                    st.session_state.selected_name = i       
                    st.session_state.resposta_openai = gerar_resposta_openai(st.session_state.selected_name)                                   

def build_chat(): 
    #limpa o chat
    st.session_state.chat_history = [] 
    
    # filtra o dataframe
    filtered_df = st.session_state.df[st.session_state.df['nome_contato'] == st.session_state.selected_name]
    
    st.markdown(f"## Chat com: {st.session_state.selected_name}")
    
    for index, row in filtered_df.iterrows():
                        # Verifica se o 'role' é 'user' ou 'assistant'
                        if row['role'] == 'user':
                            nome_exibido = row['nome_contato']  # Mostra o nome do usuário
                        else:
                            nome_exibido = "Você"  # Mostra 'Você' para o assistente

                        # Formata a mensagem completa
                        mensagem_completa = f"**{nome_exibido}**: {row['mensagem']}"

                        # Adiciona a mensagem formatada ao histórico
                        st.session_state.chat_history.append(mensagem_completa)

                    
    for mensagem, role in zip(st.session_state.chat_history,filtered_df['role']):
            with st.chat_message(role):  # Utiliza o role da mensagem ('user' ou 'assistant')
                st.markdown(mensagem)                            

def show_qrcode():
    qrcode = obter_qr_code()    
    if qrcode:
        print("Mostrando imagem")
        st.image(qrcode, caption="Após escanear o código, aguarde alguns segundos e clique em 'Verificar Conexão'", use_column_width=True)                    
        st.button("Verificar conexão")

# Função para converter a imagem para base64
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str
