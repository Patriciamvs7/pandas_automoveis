# -*- coding: utf-8 -*-
"""projeto_venda_prod_ETL_pandas.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1S2rr1jXjjuY9CuttKfunxJpQIm4ATjkq

##Instalação de bibliotecas
"""

pip install gcsfs

pip install pandera

!pip install pymongo

"""##Declaração das LIBS"""

import pandas as pd
import os
import numpy as np
import pandera as pa
import matplotlib.pyplot as plt
from google.cloud import storage
import pymongo
from pymongo import MongoClient

"""##Config . do pandas"""

pd.set_option('display.max_columns',100)

"""##Conector para Cloud Storage(bucket)"""

from google.colab import drive
drive.mount('/content/drive')

#CONFIGURANDO DA CHAVE DE CONEXÃO COMO GCP

serviceAccount = 'chave_google'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = serviceAccount

#Configurações Google Cloud Storage
client = storage.Client()

bucket = client.get_bucket('projetofinal1')

bucket.blob('vendas_prod_veiculos.csv/part-00000-5e3b5a6a-4761-4f6b-9e6a-b310430ac324-c000.csv')
path = 'gs://projetofinal1/temp/vendas_prod_veiculos.csv/part-00000-5e3b5a6a-4761-4f6b-9e6a-b310430ac324-c000.csv'

"""#Conectando ao mongo DB#"""

uri = "mongodb+srv://clustere5.wjshwzt.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
client = MongoClient(uri,
                     tls=True,
                     tlsCertificateKeyFile='chave_mongo',
                     )
db = client['producao_venda']
colecao_tratado = db['tratado']

colecao_tratado.count_documents({})

"""#Extração dos dados(Extract)#"""

#Extraindo o dataset da pasta brutos do GPC
df = pd.read_csv(path,sep=',',encoding='ISO-8859-1')

"""#Pré-análise#"""

df_bkp = df.copy()

df.dtypes

df.shape

df['data'].unique()

df['data'] = pd.to_datetime(df['data'], format='%Y-%m-%d')

df.info()

df.isnull().sum()

# 144 de 70000436 = 0,0002%
df['Producao_Autoveiculos_total'].sum()

df['Producao_Autoveiculos_total'].unique()

# 108 de 69589534 = 0,00015%
df['valorVendas_concesTotal'].sum()

df['valorVendas_concesTotal'].unique()

# 108 de 69589534 = 0,00015%
df['valorVendas_ConcesComerciais'].sum()

df['valorVendas_ConcesComerciais'].unique()

# 144 de 66024475 = 0,00021%
df['Producao_Automoveis'].sum()

df['Producao_Automoveis'].unique()

df.info()

"""#Tratamento#"""

#convertendo campo data para date
df['data'] = pd.to_datetime(df['data'])

#Criando uma nova coluna ano para facilitar a nossa análise
df['ano'] = df.data.dt.year

df['ano'].unique()

df.info()

ft2018 = df.ano >= 2018

"""
Recebendo o filtro para pegar os dados somente a partir de 2018, pois todas as análises
serão realizadas a partir deste ano
"""
df = df.loc[ft2018].copy()

df

df["ano"].unique()

df.isnull().sum()

# DROP DOS DADOS NULOS, VISTO QUE POSSUEM UMA QUANTIDADE PEQUENA EM RELAÇÃO AO TODO
df = df.dropna()

df.isnull().sum()

df.info()

df['mes'] = df.data.dt.month

df

#Drop da coluna data, pois já não é mais util, visto que todos os dias se repetem 
#e as informações de ano e mês já foram extraídas
df.drop(['data'], axis=1,inplace=True)

'''
Após a analise dos dados, percebemos que a coluna referente as vendas de 
mercado interno não será útil a nível de comparação aos outros dados 
de outros dataset, por isso optamos por apagar a coluna
'''
df.drop(['valorVendas_mercadoInterno'], axis=1,inplace=True)

'''
colunas valorVendas_concesTotal e valorVendas_ConcesComerciais possuem valores
duplicados, por isso optamos por apagar a coluna valorVendas_ConcesComerciais 
'''
df.drop(['valorVendas_ConcesComerciais'], axis=1,inplace=True)

'''
A coluna Producao_Automoveis se refere a quantidade de veículos comerciais 
leves produzidos, após realizar as analises correlacionando aos outros datasets 
percebemos que este valor não será útil a nível de comparação aos outros dados 
de outros dataset, por isso optamos por apagar a coluna 
'''
df.drop(['Producao_Automoveis'], axis=1,inplace=True)

df.columns

#renomeando para facilitar a compreensão das colunas
df.rename(columns={'Producao_Autoveiculos_total' : 'Producao_veiculos_total', 
                   'valorVendas_autoveiculosTotal' : 'qtdVendas_veiculosTotal',
                   'valorVendas_concesTotal' : 'qtdVendas_concesTotal'},inplace=True)

df.columns

"""#Criação do Schema#"""

df.columns

df.dtypes

schema = pa.DataFrameSchema(
    columns = {
        'Producao_veiculos_total':pa.Column(pa.Float64),
        'qtdVendas_veiculosTotal':pa.Column(pa.Int64),
        'qtdVendas_concesTotal':pa.Column(pa.Float64),
        'ano':pa.Column(pa.Int64),
        'mes':pa.Column(pa.Int64)
    }
)

schema.validate(df)

"""##Plotagens"""



# TOTAL DE VENDAS POR ANO
df.groupby(['ano'])['valorVendas_autoveiculosTotal'].sum().sort_values(ascending=True).plot.barh(figsize=(12,8),xlabel='VENDAS TOTAL',ylabel='ANO')

# TOTAL PRODUZIDO POR ANO
df.groupby(['ano'])['Producao_Autoveiculos_total'].sum().sort_values(ascending=False).plot.bar(figsize=(12,8),xlabel='ANO',ylabel='PRODUÇÃO TOTAL')

#DISTRIBUIÇÃO DA PRODUÇÃO POR ANO

boxplot = df.groupby(['Producao_Autoveiculos_total'])['ano'].sum().plot(kind='box',
                                                        figsize=(12, 8),
                                                        xlabel='',
                                                        ylabel='ANO')

plt.plot(df.index, df['valorVendas_autoveiculosTotal'], label='Produção',color = 'orange')
plt.title('Vendas Anuais')
plt.xlabel('Ano')
plt.ylabel('Vendas')

plt.plot(df.index, df['Producao_Autoveiculos_total'], label='Produção')
plt.title('Produção Anual')
plt.xlabel('Ano')
plt.ylabel('Produção')

# Criando o gráfico de série temporal
plt.plot(df.index, df['Producao_Autoveiculos_total'], label='Produção')
plt.plot(df.index, df['valorVendas_autoveiculosTotal'], label='Vendas')

# Configurando o estilo do gráfico
plt.xlabel('Data')
plt.ylabel('Valores')
plt.title('Produção X Vendas')
plt.legend()

"""#Carregamento#"""

df.columns

df

#carregando o dado tratado a pasta de tratados no bucket
df.to_csv('gs://projetofinal1/tratados/producao_vendas.csv',index=False)

#inserindo os dados tratados no mongo
colecao_tratado.insert_many(df.to_dict('records'))

colecao_tratado.count_documents({})

