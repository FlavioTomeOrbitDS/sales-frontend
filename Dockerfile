# Use a imagem base do Python 3.9
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar o arquivo de requirements.txt para o diretório de trabalho
COPY requirements.txt ./requirements.txt

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todos os arquivos da aplicação para o diretório de trabalho do container
COPY . .

# Expor a porta 8501 (porta padrão do Streamlit)
EXPOSE 8501

# Comando para rodar a aplicação no Streamlit
CMD ["streamlit", "run", "sales_ia.py", "--server.port=8501", "--server.address=0.0.0.0"]
