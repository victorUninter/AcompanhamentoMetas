import pandas as pd
import datetime as dt
import numpy as np
import sqlite3
import locale
import streamlit as st
from io import StringIO,BytesIO
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from streamlit.logger import get_logger
import matplotlib.pyplot as plt
import calendar

# locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

LOGGER = get_logger(__name__)

st.set_page_config(
    page_title="Acompanhamento Metas",
    layout="wide",
    initial_sidebar_state="expanded"
)

col1,col2=st.columns([1,2])
with col1:
    st.image('marca-uninter-horizontal.png',width=500)
with col2:
    # st.title('ACOMPANHAMENTO DE METAS')
    st.markdown("<h1 style='text-align: left; font-size: 80px;'>ACOMPANHAMENTO DE METAS</h1>", unsafe_allow_html=True)

# ttl=120.0
@st.cache_data(ttl=240.0)
def buscaDadosSQL(tabela,equipe=None):
    config = {
        'host': 'roundhouse.proxy.rlwy.net',
        'user': 'root',
        'port':'26496',
        'password': '2b632BA2FhGFeFb4BHdcdC3G6B6-6-3d',
        'database': 'railway'
    }

    # Cria a string de conexão
    conn = f"mysql+mysqlconnector://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    # Cria o objeto de conexão usando create_engine
    engine = create_engine(conn)

    if tabela == 'Equipe_Completa':
         query=f"SELECT * FROM {tabela};"
         Base=pd.read_sql(query, engine)
         return Base
    elif tabela=='metas_cobranca_geral':
        query=f"SELECT * FROM {tabela};"
        Base=pd.read_sql(query, engine)
        return Base
    else:
        query=f"SELECT * FROM {tabela};"
        Base=pd.read_sql(query, engine)
        Base=Base.drop_duplicates()
        Base.to_sql(tabela, con=engine, if_exists='replace', index=False)
        return Base

def exibeEquipe(LiquidadoEquipeMerge,colaborador,eqp,rpt):
    if colaborador == 'TODOS':
        filtro_sit = LiquidadoEquipeMerge['Nome_Colaborador'].notnull()  # Qualquer valor diferente de NaN
    else:
        filtro_sit = LiquidadoEquipeMerge['Nome_Colaborador'] == colaborador
    if eqp == 'TODOS':
        filtro_eqp = LiquidadoEquipeMerge['EQUIPE'].notnull()  # Qualquer valor diferente de NaN
    else:
        filtro_eqp = LiquidadoEquipeMerge['EQUIPE'] == eqp
    if rpt == 'TODOS':
        filtro_rpt = LiquidadoEquipeMerge['REPORTE'].notnull()  # Qualquer valor diferente de NaN
    else:
        filtro_rpt = LiquidadoEquipeMerge['REPORTE'] == rpt

    DfEqpFiltro=LiquidadoEquipeMerge.loc[filtro_sit & filtro_eqp & filtro_rpt].reset_index(drop=True)
    qtdeColabs=len(DfEqpFiltro)
    return DfEqpFiltro,qtdeColabs

# Define uma função para criar um container personalizado com cor de fundo
def colored_metric(content, color):
    return f'<div style="padding: 10px; background-color: {color}; border: 2px solid white; border-radius: 5px;">{content}</div>'

def get_color(value):
    return "red" if value < 0 else "green"

def filtroMesAno(mesNum,anoLiq):
    pass
#Relatório de Liquidação
def import_base():
    BaseLiq=buscaDadosSQL('Liquidado')
    BaseAliq=buscaDadosSQL('Areceber')

    BaseLiq['Valor Liquidado']=BaseLiq['Valor Liquidado'].str.replace(",",".").astype(float)
    BaseAliq['Valor Original']=BaseAliq['Valor Original'].str.replace(",",".").astype(float)

    BaseLiq['Data Liquidacao']=pd.to_datetime(BaseLiq['Data Liquidacao'],dayfirst=True)
    BaseAliq['Data Vencimento']=pd.to_datetime(BaseAliq['Data Vencimento'],dayfirst=True)
    return BaseLiq,BaseAliq


EquipeGeral=buscaDadosSQL('Equipe_Completa')

EquipeMetas=EquipeGeral[EquipeGeral['EQUIPE']!='MARCOS']
colaborador=list(EquipeMetas['Nome_Colaborador'].unique())
colaborador.insert(0,'TODOS')
Equipe=list(EquipeMetas['EQUIPE'].unique())
Equipe.insert(0,'TODOS')
Reporte=list(EquipeMetas['REPORTE'].unique())
Reporte.insert(0,'TODOS')

with st.container(border=True):
        col1, col2, col3,col4 = st.columns([1,2,2,2])
        with col1:
            meses={i:j for j,i in enumerate(calendar.month_abbr)}
            mesLiq = st.selectbox(
            'Mês',list(meses.keys())[1:])
            mesNum=meses[f"{mesLiq}"]

            anoInicio=2024
            anoFim=anoInicio+20

            anoLiq = st.selectbox(
            'Ano',range(anoInicio,anoFim))

        with col2:
            optionsEqp = st.selectbox(
            'Selecione a Equipe',
            Equipe)
        with col3:
            optionsRpt = st.selectbox(
            'Selecione o Responsável',
            Reporte)

        with col4:
            colaborador = st.selectbox(
            'Selecione o Colaborador',
            colaborador)

BaseLiq,BaseAliq=import_base()

BaseLiqmes=BaseLiq.loc[(BaseLiq['Data Liquidacao'].dt.month==mesNum) & (BaseLiq['Data Liquidacao'].dt.year==anoLiq)]
# BaseLiqmes=filtroMesAno()
BaseaLiqmes=BaseAliq[BaseAliq['Data Vencimento'].dt.month==mesNum]

BaseAliqMetas=BaseaLiqmes[BaseaLiqmes['Parcela']==1]

acordoOnline=BaseLiqmes[BaseLiqmes['Criado Por']=='Acordo Online']

BaseLiqSemAO=BaseLiqmes[BaseLiqmes['Criado Por']!='Acordo Online']

LiquidadoEquipe=BaseLiqSemAO[BaseLiqSemAO['Criado Por'].isin(EquipeGeral['Nome_Colaborador'])]

LiquidadoEquipeMerge=BaseLiqSemAO.merge(EquipeGeral,left_on='Criado Por',right_on='Nome_Colaborador')

cobranca_geral=LiquidadoEquipeMerge[LiquidadoEquipeMerge['EQUIPE']=='COBRANÇA_GERAL']
telecobranca=LiquidadoEquipeMerge[LiquidadoEquipeMerge['EQUIPE']=='Telecobrança']
Apoio=LiquidadoEquipeMerge[LiquidadoEquipeMerge['EQUIPE']=='MARCOS']
ColabsExternos=BaseLiqSemAO[~BaseLiqSemAO['Criado Por'].isin(EquipeGeral['Nome_Colaborador'])]

# cobranca_geral.columns
# cobranca_geral.groupby(['REPORTE','Nome_Colaborador'],as_index=False)['Valor Liquidado'].sum()

def run(cobranca_geral,telecobranca,acordoOnline,BaseLiqmes,BaseAliqMetas,colaborador):
    metas=buscaDadosSQL('metas_cobranca_geral',equipe=None)
    metas['Mes']=metas['Mês'].dt.month
    metas['Ano']=metas['Mês'].dt.year
    metasFiltro=metas.loc[(metas['Mes']==mesNum) & (metas['Ano']==anoLiq)]
    MetaLiq=list(metasFiltro['Meta_geral'])[0]
    MetaTele=300000
    Metaindividual=list(metasFiltro['Meta Individual'])[0]
    MetaindividualTele=61000

    cobgeral=cobranca_geral['Valor Liquidado'].sum()
    tele=telecobranca['Valor Liquidado'].sum()
    acOn=acordoOnline['Valor Liquidado'].sum()
    totalLiq=BaseLiqmes['Valor Liquidado'].sum()
    aLiquidar=BaseAliqMetas['Valor Original'].sum()
    faltaMeta=totalLiq-MetaLiq
    faltaMetaTele=tele-MetaTele

    with st.container(border=True,height=200):
       
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Usa a função para criar um container verde
            green_metric = colored_metric(f"Cobrança Geral<br>R$ {cobgeral:,.0f}".replace(',', '.'), "#363636")
            st.markdown(green_metric, unsafe_allow_html=True)
            # Usa a função para criar um container azul
            blue_metric = colored_metric(f"Acordo Online<br>R$ {acOn:,.0f}".replace(',', '.'), "#363636")
            st.markdown(blue_metric, unsafe_allow_html=True)
        # with col1:
        #     # Usa a função para criar um container azul
        #     blue_metric = colored_metric(f"Acordo Online<br>R$ {acOn:,.0f}".replace(',', '.'), "#363636")
        #     st.markdown(blue_metric, unsafe_allow_html=True)

        with col2:
            # Usa a função para criar um container amarelo
            yellow_metric1 = colored_metric(f"Meta Telecobrança<br>R$ {MetaTele:,.0f}".replace(',', '.'), "#363636")
            # Se o valor for negativo, a cor será vermelha, caso contrário, será verde
            color = get_color(faltaMetaTele)

            # Criar a métrica colorida
            yellow_metric2 = colored_metric(f"Telecobrança Liquidado<br>Liquidado:R$ {tele:,.0f}<br>Falta: R$ {faltaMetaTele:,.0f}".replace(',', '.'), color)

            st.markdown(yellow_metric1, unsafe_allow_html=True)
            st.markdown(yellow_metric2, unsafe_allow_html=True)

        with col3:
            # Usa a função para criar um container laranja
            orange_metric1 = colored_metric(f"Meta Liquidado<br>R$ {MetaLiq:,.0f}".replace(',', '.'), "#363636")

            color = get_color(faltaMeta)

            orange_metric2 = colored_metric(f"Total Liquidado<br>Liquidado:R$ {totalLiq:,.0f}<br>Falta:R$ {faltaMeta:,.0f}".replace(',', '.'), color)

            st.markdown(orange_metric1, unsafe_allow_html=True)
            st.markdown(orange_metric2, unsafe_allow_html=True)

        with col4:
            # Usa a função para criar um container vermelho
            red_metric = colored_metric(f"Total a Liquidar<br>R$ {aLiquidar:,.0f}".replace(',', '.'), "#363636")
            st.markdown(red_metric, unsafe_allow_html=True)

    DfEqpFiltro,qtdeColabs = exibeEquipe(LiquidadoEquipeMerge,colaborador, optionsEqp, optionsRpt)

    if optionsEqp=='Telecobrança':
        cobranca_geral=DfEqpFiltro.query("CARGO=='ASSISTENTE_TELE'")
        meta=MetaindividualTele
    else:
        cobranca_geral=DfEqpFiltro.query("CARGO=='ASSISTENTE'")
        meta=Metaindividual

    grafCobGeral=(cobranca_geral.groupby(['Nome_Colaborador','REPORTE','SIT_ATUAL'],as_index=False)['Valor Liquidado'].sum()).sort_values(by='Valor Liquidado',ascending=False)

    col1,col2=st.columns([5,2.4])
    with col1:
        with st.container(border=True):
            # Seu código para criar o gráfico
            fig, ax = plt.subplots(figsize=(30  , 20))  # Ajuste os valores conforme necessário
            colabs = grafCobGeral['Nome_Colaborador']
            y_pos = range(len(colabs))
            performance = grafCobGeral['Valor Liquidado']

            bars=ax.barh(y_pos, performance, align='center')

            for bar, val in zip(bars, performance):
                ax.text(bar.get_x() + bar.get_width(), bar.get_y() + bar.get_height() / 2, 
                        f'{val:,.0f}'.replace(',', '.'), color='white', fontweight='bold', fontsize=20, va='center')

            ax.vlines(x=meta, ymin=-1.5, ymax=len(colabs), color='red', linestyle='--', label='Meta')
            ax.text(meta, -1.5, f'Meta: {meta:,.0f}'.replace(',', '.'), color='red', fontsize=30, ha='right')

            ax.set_yticks(y_pos)
            ax.set_yticklabels(colabs, color="white", fontsize=20,fontweight='bold')
            ax.invert_yaxis()
            ax.set_xlabel('Valor Liquidado')
            ax.set_title('Liquidado por Colaborador')
            ax.spines['top'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_facecolor(color="none")
            fig.patch.set_alpha(0)
            

            # Ajuste a largura da figura para acomodar os nomes completos
            fig.tight_layout()

            # Salvar a figura como BytesIO
            image_stream = BytesIO()
            fig.savefig(image_stream, format="png")
            image_stream.seek(0)  # Voltar ao início do stream

            # Exibir a imagem sem use_container_width
            st.image(image_stream)
    
    with col2:
        with st.container(border=True,height=750):
            cobranca_geral['Meta']=meta
            
            # agroupTab=cobranca_geral.groupby('REPORTE')[['Nome_Colaborador','Valor Liquidado']].agg({'Nome_Colaborador':'first','Valor Liquidado':'sum'})
            try:
                agroupTab = cobranca_geral.pivot_table(index=['REPORTE','Nome_Colaborador'], values='Valor Liquidado', aggfunc='sum').reset_index().sort_values(by='Valor Liquidado',ascending=False)
            except:
                agroupTab=cobranca_geral[['REPORTE','Nome_Colaborador','Valor Liquidado']]

            agroupTab['% Meta']=agroupTab['Valor Liquidado'].apply(lambda x:f"{x/meta*100:.2f}%")

            agroupTab['RANK']=range(1,len(agroupTab['Nome_Colaborador'])+1)

            agroupTab=agroupTab[['RANK','REPORTE','Nome_Colaborador','Valor Liquidado','% Meta']]

            st.dataframe(agroupTab,hide_index=True) 

if __name__ == "__main__":
    run(cobranca_geral,telecobranca,acordoOnline,BaseLiqmes,BaseAliqMetas,colaborador)
    
    
