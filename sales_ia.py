import streamlit as st
import pandas as pd
import time
from functions import *
from PIL import Image


#***************************** STYLE CONF **************************************************
#Esconde o header e o menu lateral usando CSS
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# CSS para alterar o estilo do botão específico
custom_css = """
    <style>
        button[data-testid="baseButton-secondary"] {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s ease;
         }

         button[data-testid="baseButton-secondary"]:hover {
        background-color: #45a049;
        color: white;
    }
    </style>
    """
    # Aplica o CSS na página
st.markdown(custom_css, unsafe_allow_html=True)
    
#***************************** MAIN **************************************************
  
init_session_state()    

st.session_state.status_conexao = verificar_conectado()

if st.session_state.status_conexao == 500:
    st.warning("Nenhuma conta conectada ainda!")
    result = reset_messages()
    st.session_state.started_scrapping_process = False
elif st.session_state.status_conexao == 200:
    #verifica se o scrapper já foi inicializado
    if st.session_state.started_scrapping_process == False:        
        print(start_process())
        st.session_state.started_scrapping_process = True

verify_new_message()

#***************************** SIDEBAR **************************************************
with st.sidebar:
    logo = Image.open("logo.png")                
     # Centralizar a imagem usando HTML e CSS
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center;">
            <img src="data:image/png;base64,{image_to_base64(logo)}" width="100" />
        </div>
        """,
        unsafe_allow_html=True
    )                    
    st.divider()
    
    #*********** qrcode area **************
    if st.session_state.status_conexao == 500:
        with st.spinner("Gerando o Qr Code..."):
            show_qrcode()
            
    elif st.session_state.status_conexao == 200:
        #*********** messages area **************
        st.markdown("### Mensagens:")
        if not st.session_state.df.empty:
            unique_names = st.session_state.df['nome_contato'].unique().tolist()
            build_contact_area(unique_names)
        else:
            st.warning("Nenhuma mensagem!")        
                
        #*********** AI area **************
        if st.session_state.selected_name != '':
            st.divider()             
            st.markdown("## Análise de IA:")        
            temp_df = st.session_state.df_ia_analysis[st.session_state.df_ia_analysis['nome'] == st.session_state.selected_name]
            if temp_df.empty:
                # Gera a resposta da OpenAI e exibe no markdown
                st.session_state.resposta_openai = gerar_resposta_openai(st.session_state.selected_name)                                
                # Cria um DataFrame a partir dos dados
                data = {'nome': [st.session_state.selected_name], 'analise': [st.session_state.resposta_openai]}
                data_df = pd.DataFrame(data=data)
                
                # Concatena o novo DataFrame ao DataFrame existente no session_state
                st.session_state.df_ia_analysis = pd.concat([st.session_state.df_ia_analysis, data_df], ignore_index=True)
            
            with st.spinner("Gerando resposta..."):
                st.markdown(st.session_state.resposta_openai)
        
        #*********** model training area **************        
        st.divider()
        with st.expander("Treinamento do Modelo de IA"):
            # Multiplicando por 10 para ajustar a escala do slider
            slider_value = int(st.session_state.model_temperature * 10)
            temperature = st.slider("Temperatura", 0, 10, slider_value, step=1)
                                                
            model_training = st.text_area("Treinamento do Modelo:",st.session_state.model_training, placeholder="Treine aqui o seu modelo")
            
            if st.button("Salvar"):
                st.session_state.model_temperature = temperature / 10
                st.session_state.model_training =  model_training   
                st.toast("Treinamento Salvo!")
            
        
#***************************** CHAT AREA *****************************************************
if st.session_state.status_conexao == 200:
    if st.session_state.selected_name != '':
        with st.spinner("Carregando Mensagens..."):
            build_chat()
        
        
        prompt = st.chat_input("Say something")
        if prompt:
                send_message_to_backend(st.session_state.selected_name, prompt)
    else:
        st.markdown("## Inicie um Chat! 💬")


if st.session_state.status_conexao == 200:
    time.sleep(2)
    st.rerun()