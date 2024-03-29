import pandas as pd
from pandas.tseries.offsets import BDay
import datetime as dt
from datetime import datetime
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
import requests
import base64

load_dotenv()

# locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

LOGGER = get_logger(__name__)

st.set_page_config(
    page_title="Acompanhamento Metas",
    layout="wide",
    initial_sidebar_state="expanded"
)

col1,col2=st.columns([1,2])
with col1:
    st.image('marca-uninter-horizontal.png',width=300)
with col2:
    # st.title('ACOMPANHAMENTO DE METAS')
    st.markdown("<h1 style='text-align: left; font-size: 60px;'>ACOMPANHAMENTO DE METAS</h1>", unsafe_allow_html=True)

# ttl=240.0
@st.cache_data(ttl=900.0)
def buscaDadosSQL(tabela,equipe=None):

    config = {
        'host': 'roundhouse.proxy.rlwy.net',
        'user': os.getenv('MYSQLUSER'),
        'port':'26496',
        'password': os.getenv('MYSQLPASSWORD'),
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
    
def dias_uteis_no_mes(ano, mes):
    data_inicial = pd.Timestamp(f'{ano}-{mes}-01')
    data_final = pd.Timestamp(f'{ano}-{mes + 1}-01') - pd.DateOffset(days=1)
    
    datas = pd.date_range(start=data_inicial, end=data_final, freq=BDay())
    
    return len(datas)

def dias_uteis_que_faltam():
    hoje = pd.Timestamp(datetime.now())
    
    # Encontrar o último dia do mês atual
    ultimo_dia_do_mes = hoje + pd.offsets.MonthEnd(0)
    
    # Calcular os dias úteis restantes
    datas = pd.date_range(start=hoje, end=ultimo_dia_do_mes, freq=BDay())
    
    return len(datas)

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
    return f'<div style="display: flex;padding: 10px; background-color: rgb({color}/0.4); border: 2px solid white; border-radius: 5px;">{content}</div>'

def get_color(value):
    return "255 0 0" if value < 0 else "50 205 50"

#Relatório de Liquidação
def import_base():
    BaseLiq=buscaDadosSQL('Liquidado')
    BaseAliq=buscaDadosSQL('Areceber')
    try:
        BaseLiq['Valor Liquidado']=BaseLiq['Valor Liquidado'].str.replace(",",".").astype(float)
        BaseAliq['Valor Original']=BaseAliq['Valor Original'].str.replace(",",".").astype(float)
    except:
        pass

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


col1, col2,col3,col4,col5,col6,col7,col8, = st.columns([3,3,5,5,5,5,5,5])

with col1:
    meses={i:j for j,i in enumerate(calendar.month_abbr)}

    mesLiq = st.selectbox(
    'Mês',list(meses.keys())[1:])
    mesNum=meses[f"{mesLiq}"]
with col2:
    anoInicio=2024
    anoFim=anoInicio+20

    anoLiq = st.selectbox(
    'Ano',range(anoInicio,anoFim))

with st.container(border=True):
    col1, col2, col3 = st.columns([5,5,5])

    with col1:
        optionsEqp = st.selectbox(
        'Filtro por Equipe',
        Equipe)
    with col2:
        optionsRpt = st.selectbox(
        'Filtro por Responsável',
        Reporte)

    with col3:
        colaborador = st.selectbox(
        'Filtro por Colaborador',
        colaborador)

BaseLiq,BaseAliq=import_base()

BaseAliq['Valor Original']=BaseAliq['Valor Original'].str.replace(",",".").astype(float)

aliqcolabs=BaseAliq[BaseAliq['Parcela']==1]

aliqcolabs=aliqcolabs.groupby('Criado Por',as_index=False)['Valor Original'].sum()

aliqcolabs=aliqcolabs.rename(columns={'Valor Original':'A Receber'})

BaseLiqmes=BaseLiq.loc[(BaseLiq['Data Liquidacao'].dt.month==mesNum) & (BaseLiq['Data Liquidacao'].dt.year==anoLiq)]

BaseaLiqmes=BaseAliq[BaseAliq['Data Vencimento'].dt.month==mesNum]

BaseAliqMetas=BaseaLiqmes[BaseaLiqmes['Parcela']==1]

BaseAliqMetas=BaseAliqMetas.rename(columns={'Valor Original':'A Receber'})

acordoOnline=BaseLiqmes[BaseLiqmes['Criado Por']=='Acordo Online']

BaseLiqSemAO=BaseLiqmes[BaseLiqmes['Criado Por']!='Acordo Online']

LiquidadoEquipe=BaseLiqSemAO[BaseLiqSemAO['Criado Por'].isin(EquipeGeral['Nome_Colaborador'])]

LiquidadoEquipeMerge=BaseLiqSemAO.merge(EquipeGeral,left_on='Criado Por',right_on='Nome_Colaborador')

LiquidadoEquipeMerge['valorPcolab']=LiquidadoEquipeMerge.groupby('Nome_Colaborador')['Valor Liquidado'].transform(sum)

LiquidadoEquipeMerge=LiquidadoEquipeMerge.sort_values(by='valorPcolab',ascending=False)

LiquidadoEquipeMerge['RANK'] = LiquidadoEquipeMerge['valorPcolab'].rank(method='dense', ascending=False).astype(int)

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
    MetaTele=list(metasFiltro['Meta_Tele'])[0]
    Metaindividual=list(metasFiltro['Meta Individual'])[0]
    MetaindividualTele=list(metasFiltro['Meta_Individual_Tele'])[0]
    dias_uteis=dias_uteis_no_mes(anoLiq, mesNum)
    dias_uteis_falta=dias_uteis_que_faltam()

    token=os.getenv('token')
    r = requests.get(f'https://api.invertexto.com/v1/holidays/{anoLiq}?token={token}&state=PR',verify=False)
    feriados=r.json()

    feriadoNacionais=[data['date'] for data in feriados]

    feriadosDF=pd.DataFrame(feriadoNacionais,columns=["Data"])
    feriadosDF["Data"]=pd.to_datetime(feriadosDF["Data"])
    feriadosDF["DiaSemana"]=feriadosDF["Data"].dt.strftime("%A")
    feriadosDF["Mês"]=feriadosDF["Data"].dt.month
    domingo="Sunday"
    sabado="Saturday"
    feriadosDUtil=feriadosDF.loc[(feriadosDF['DiaSemana']!=domingo) & (feriadosDF['DiaSemana']!=sabado)]

    qtdeFeriados=feriadosDF.groupby('Mês',as_index=False)['Data'].count()
    qtdeFeriadosMes=qtdeFeriados[qtdeFeriados['Mês']==mesNum]

    try:
        nFer=list(qtdeFeriadosMes['Data'])[0]
        dias_uteis=dias_uteis-nFer
        dias_uteis_falta=dias_uteis_falta-nFer
    except:
        nFer=0
        dias_uteis=dias_uteis-nFer
        dias_uteis_falta=dias_uteis_falta-nFer

    diaHj=dt.datetime.now().day
    cobgeral=cobranca_geral['Valor Liquidado'].sum()
    tele=telecobranca['Valor Liquidado'].sum()
    acOn=acordoOnline['Valor Liquidado'].sum()
    totalLiq=BaseLiqmes['Valor Liquidado'].sum()
    liqDia=BaseLiqmes.loc[(BaseLiqmes['Data Liquidacao'].dt.day==diaHj),'Valor Liquidado'].sum()
    aLiquidar=BaseAliqMetas['A Receber'].sum()
    faltaMeta=totalLiq-MetaLiq
    faltaMetaTele=tele-MetaTele

    with st.container(border=True,height=270):
       
        col1, col2, col3, col4= st.columns([2,4,4,3])

        with col1:
            #BLOCO INICIAL MÉTRICAS COBRANÇA E ACORDO ONLINE
            corPad="105 105 105"
            # Usa a função para criar um container verde
            green_metric = f"""<div style='display: inline-block;padding: 5px;width: 300px;background-color: rgb({corPad}/0.4); border: 2px solid white; border-radius: 5px;
            white-space: nowrap;text-align: center;font-size: 20px'>Cobrança Geral<br>R$ {cobgeral:,.0f}</div>""".replace(',', '.')
            st.markdown(green_metric, unsafe_allow_html=True)
            # Usa a função para criar um container azul
            blue_metric = f"""<div style='display: inline-block;padding: 5px;width: 300px;background-color: rgb({corPad}/0.4); border: 2px solid white; border-radius: 5px;
            white-space: nowrap;text-align: center;font-size: 20px'>Acordo Online<br>R$ {acOn:,.0f}</div>""".replace(',', '.')
            st.markdown(blue_metric, unsafe_allow_html=True)

            blue_metric = f"""<div style='display: inline-block;padding: 5px;width: 300px;background-color: rgb({corPad}/0.4); border: 2px solid white; border-radius: 5px;
            white-space: nowrap;text-align: center;font-size: 20px'>Dias de Trabalho<br>{dias_uteis} Dias Úteis &nbsp - Faltam &nbsp{dias_uteis_falta} dias</div>"""
            st.markdown(blue_metric, unsafe_allow_html=True)

        # with col1:
        #     # Usa a função para criar um container azul
        #     blue_metric = colored_metric(f"Acordo Online<br>R$ {acOn:,.0f}".replace(',', '.'), "#363636")
        #     st.markdown(blue_metric, unsafe_allow_html=True)

        with col2:
            #BLOCO MÉTRICAS METAS TELECOBRANÇA
            valorDefSupTel=tele-(MetaTele/dias_uteis)*(dias_uteis-dias_uteis_falta)
            defsupTel=f"{valorDefSupTel:,.2f}".replace(",",";").replace(".",",").replace(";",".")
            alteraCor='0 0 255' if valorDefSupTel>0 else '255 0 0' 
            # Usa a função para criar um container amarelo
            # Criar a métrica colorida
            n1 = 12
            nnbsp_repeated1 = '&nbsp;' * n1
            n2 = 10
            nnbsp_repeated2 = '&nbsp;' * n2
            # Se o valor for negativo, a cor será vermelha, caso contrário, será verde
            color = get_color(faltaMetaTele)

            yellow_metric1 = f"""<div style='display: flex'>
                                <div style='display: flex;padding: 5px;width: 350px;background-color: rgb({corPad}/0.4); border: 2px solid white; border-radius: 5px;
                                white-space: nowrap;justify-content: center;font-size: 20px'>Meta Telecobrança<br>R$ {MetaTele:,.0f}</div>
                                <div style='display: flex;padding: 5px;width: 350px;background-color: rgb({corPad}/0.4); border: 2px solid white; border-radius: 5px;white-space: nowrap;justify-content: center;font-size: 20px'>Meta Diária Telecobrança<br>R$ {MetaTele/dias_uteis:,.0f}</div>
                                </div>
                                <div style="display: flex;padding: 15px; background-color: rgb({color}/0.4); border: 2px solid white;justify-content: center; border-radius: 5px;width: 700px">
                                <div style='display: inline-block;font-size: 17px;text-align: center'> Liquidado: R$ {tele: ,.0f}
                                <span style='font-size: 20px; color: blue;'>{(tele/MetaTele)*100: .0f}%</span><br>
                                Falta para Meta:R$ {faltaMetaTele: ,.0f} <span style='font-size: 25px; color: blue;'>{((tele-MetaTele)/MetaTele)*100: .0f}%</span>
                                </div>{nnbsp_repeated2}
                                <div style="display: inline-block; padding: 10px; text-align: center; width: 180px; border: 2px solid white; border-radius: 10px; white-space: nowrap; background-color: rgb({alteraCor} / 0.5  ); font-size: 20px;">
                                Déficit/Superávit <br>R${defsupTel}
                                </div>
                                <div style="display: inline-block; padding: 10px; text-align: center; width: 180px; border: 2px solid white; border-radius: 10px; white-space: nowrap; background-color: rgb({alteraCor} / 0.5  ); font-size: 18px;">
                                Meta Diária Atual <br>Meta R${(faltaMetaTele/dias_uteis_falta)*-1:,.0f}</div></div>""".replace(',', '.')
            
            st.markdown(yellow_metric1, unsafe_allow_html=True)

        with col3:
            #BLOCO MÉTRICAS METAS COBRANÇA GERAL
            n5 = 12
            n6 = 8
            nnbsp_repeated5 = '&nbsp;' * n5
            nnbsp_repeated6 = '&nbsp;' * n6
            # Usa a função para criar um container laranja
            metaCob=f"{MetaLiq:,.0f}".replace(',', '.')
            metaDia=f"{MetaLiq/dias_uteis:,.0f}".replace(',', '.')
            valorDefSup=totalLiq-(MetaLiq/dias_uteis)*(dias_uteis-dias_uteis_falta)
            defsup=f"{valorDefSup:,.2f}".replace(",",";").replace(".",",").replace(";",".")
            alteraCor='0 0 255' if valorDefSup>0 else '255 0 0' 

            color = get_color(faltaMeta)

            percentual_completado = (totalLiq / MetaLiq) * 100
            percentual_falta = ((totalLiq - MetaLiq) / MetaLiq) * 100

            # Formate os resultados para inseri-los no f-string
            percentual_completado_formatado = f"{percentual_completado:.0f}%"
            percentual_falta_formatado = f"{percentual_falta:.0f}%"
            # color = float(color)

            orange_metric1 = f"""<div style='display:flex; justify-content: center'>
                                <div style='display: flex;padding: 5px;width: 350px;background-color: rgb({corPad}/0.4); border: 2px solid white; border-radius: 5px;
                                white-space: nowrap;justify-content: center;font-size: 20px'>Meta Cobrança<br> R${metaCob}</div>
                                <div style='display: flex;padding: 5px;width: 350px;background-color: rgb({corPad}/0.4); border: 2px solid white; border-radius: 5px;
                                white-space: nowrap;justify-content: center;font-size: 20px'>Meta Diária<br> R${metaDia}</div>
                                </div>
                                <div style="display: flex;padding: 15px; background-color: rgb({color}/0.4); border: 2px solid white;justify-content: center; border-radius: 5px;width: 700px">
                                <div style='display: inline-block;font-size: 17px'> Liquidado: R$ {totalLiq: ,.0f}
                                <span style='font-size: 25px; color: blue;'>{(totalLiq/MetaLiq)*100: .0f}%</span><br>
                                Falta para Meta:R$ {faltaMeta: ,.0f} <span style='font-size: 25px; color: blue;'>{((MetaLiq-totalLiq) / MetaLiq)*100: .0f}%
                                </span><br>A Liquidar (entradas):R$ {aLiquidar: ,.0f}</div>
                                {nnbsp_repeated2}<div style="display: inline-block; padding: 10px; text-align: center; width: 180px; border: 2px solid white; border-radius: 10px; white-space: nowrap; background-color: rgb({alteraCor} / 0.5  ); font-size: 20px;">
                                Déficit/Superávit <br>R${defsup}</div>
                                <div style="display: inline-block; padding: 10px; text-align: center; width: 180px; border: 2px solid white; border-radius: 10px; white-space: nowrap; background-color: rgb({alteraCor} / 0.5  ); font-size: 18px;">
                                Meta Diária Atual <br>Meta R${(faltaMeta/dias_uteis_falta)*-1:,.0f}</div></div>""".replace(',', '.')


            st.markdown(orange_metric1, unsafe_allow_html=True)
            # st.markdown(orange_metric2, unsafe_allow_html=True)

        with col4:
            try:
                def grafico_rosca(meta, realizado):
                    # Calculando o restante
                    restante = meta - realizado

                    # Criando o gráfico de rosca com fundo transparente
                    fig1, ax1 = plt.subplots()
                    fig1.patch.set_alpha(0)  # Define a transparência do fundo da figura
                    sizes = [realizado, restante]
                    labels = ['Realizado', 'Falta']
                    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['green', 'red'], textprops={'fontsize': 20})
                    ax1.axis('equal')  # Garante que o gráfico seja desenhado como um círculo.
                    ax1.set_title('Progresso em relação à meta', fontsize=12)

                    return fig1

                    def _generate_base64_grafico(fig):
                        # Converte o gráfico Matplotlib para uma imagem base64
                        img = BytesIO()
                        fig.savefig(img, format='png', bbox_inches='tight', transparent=True)
                        img.seek(0)
                        img_base64 = base64.b64encode(img.getvalue()).decode()
                        return img_base64

                    # Definindo a meta e o que foi realizado (valores fictícios para exemplo)
                    meta = (totalLiq/MetaLiq)*100
                    realizado = ((MetaLiq-totalLiq) / MetaLiq) * 100

                    # Exibindo o gráfico de rosca dentro de um div personalizado
                    st.markdown(
                                f"""
                                <div style="
                                    max-width: 400px; 
                                    max-height: 250px; 
                                    overflow: hidden; 
                                    display: flex; 
                                    justify-content: center; 
                                    align-items: center; 
                                    padding: 15px; 
                                    border: 2px solid white; 
                                    border-radius: 5px;
                                ">
                                <img src="data:image/png;base64,{_generate_base64_grafico(grafico_rosca(meta, realizado))}" style="max-width: 100%; max-height: 100%;" />
                                </div>
                                """, unsafe_allow_html=True
                            )
            except:
                pass
    DfEqpFiltro,qtdeColabs = exibeEquipe(LiquidadoEquipeMerge,colaborador, optionsEqp, optionsRpt)

    if optionsEqp=='Telecobrança':
        cobranca_geral=DfEqpFiltro.query("CARGO=='ASSISTENTE_TELE'")
        meta=MetaindividualTele
    else:
        cobranca_geral=DfEqpFiltro.query("CARGO=='ASSISTENTE'")
        meta=Metaindividual

    grafCobGeral=(cobranca_geral.groupby(['Nome_Colaborador','REPORTE','SIT_ATUAL'],as_index=False)['Valor Liquidado'].sum()).sort_values(by='Valor Liquidado',ascending=False)

    col4,col5=st.columns([5,6])
    with col4:
        with st.container(border=True):
            # Seu código para criar o gráfico
            fig, ax = plt.subplots(figsize=(25  , 27))  # Ajuste os valores conforme necessário
            colabs = grafCobGeral['Nome_Colaborador']
            y_pos = range(len(colabs))
            performance = grafCobGeral['Valor Liquidado']

            bars=ax.barh(y_pos, performance, align='center')

            for bar, val in zip(bars, performance):
                ax.text(bar.get_x() + bar.get_width(), bar.get_y() + bar.get_height() / 2, 
                        f'{(val/meta)*100:,.2f}%'.replace(',', '.'), color='white', fontweight='bold', fontsize=20, va='center')

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
    
    with col5:
        # with st.container(border=True,height=750):
        cobranca_geral['Meta']=meta
        cobranca_geral=cobranca_geral.merge(aliqcolabs,left_on='Nome_Colaborador',right_on='Criado Por',how='left')
        metaDiaria=round(meta/dias_uteis)
        diasPassados=dias_uteis-dias_uteis_falta
        # agroupTab=cobranca_geral.groupby('REPORTE')[['Nome_Colaborador','Valor Liquidado']].agg({'Nome_Colaborador':'first','Valor Liquidado':'sum'})
        # cobranca_geral['RANK']=range(1,len(cobranca_geral['Nome_Colaborador'])+1)

        try:
            agroupTab = cobranca_geral.pivot_table(index=['RANK','REPORTE','Nome_Colaborador','A Receber'], values='Valor Liquidado', aggfunc='sum').reset_index().sort_values(by='Valor Liquidado',ascending=False)
        except:
            agroupTab=cobranca_geral[['RANK','REPORTE','Nome_Colaborador','Valor Liquidado','A Receber']]

        agroupTab['% Atingido Meta']=agroupTab['Valor Liquidado'].apply(lambda x:f"{x/meta*100:.2f}%")

        # agroupTab['RANK']=range(1,len(agroupTab['Nome_Colaborador'])+1)

        agroupTab['Meta Diária']=f"R${metaDiaria:,.2f}".replace(",",";").replace(".",",").replace(";",".")
        agroupTab['Realizado por Dia (Média)']=agroupTab['Valor Liquidado'].apply(lambda x:f"R${x/diasPassados:,.2f}".replace(",",";").replace(".",",").replace(";","."))
        agroupTab['Déficit/Superávit Diário']=agroupTab['Valor Liquidado'].apply(lambda x:f"R${((x/diasPassados)-metaDiaria):,.2f}".replace(",",";").replace(".",",").replace(";","."))
        agroupTab['Realizado Total']=agroupTab['Valor Liquidado'].apply(lambda x: f"R${x:,.2f}".replace(",",";").replace(".",",").replace(";","."))
        agroupTab['Déficit/Superávit Total']=agroupTab['Déficit/Superávit Diário'].apply(lambda x: f"R${float(x.replace('R$','').replace('.','').replace(',','.'))*diasPassados:,.2f}".replace(",",";").replace(".",",").replace(";","."))
        agroupTab['Receber']=agroupTab['A Receber'].apply(lambda x: f"R${x:,.2f}".replace(",",";").replace(".",",").replace(";","."))
        # agroupTab['PREVISÃO_META']=agroupTab['Realizado Total']+agroupTab['A Receber']
        # Função para verificar se a meta foi batida
        def verificar_meta(row):
            if row['Valor Liquidado'] >= meta:
                return 'Meta Batida'
            elif (row['Valor Liquidado']+ row['A Receber']) >= meta:
                return 'Pode Bater Meta'
            elif (row['Valor Liquidado']+ row['A Receber']+(dias_uteis_falta*metaDiaria)) >= meta:
                return 'Chance de bater a meta'
            else:
                return 'Não irá bater Meta'
            
        agroupTab['Resultado']=agroupTab.apply(verificar_meta, axis=1)


        agroupTab=agroupTab[['RANK','REPORTE','Nome_Colaborador','Realizado Total','% Atingido Meta','Meta Diária','Realizado por Dia (Média)','Déficit/Superávit Diário','Déficit/Superávit Total','Receber','Resultado']]
        
        # Função para definir a cor do texto com base no conteúdo da coluna 'Resultado'
        def color_text(value):
            if value == 'Meta Batida':
                color = 'blue'
            elif value == 'Pode Bater Meta':
                color = 'lightblue'
            elif value == 'Chance de bater a meta':
                color = 'orange'
            elif value == 'Não irá bater Meta':
                color = 'red'
            else:
                color = 'black'  # Cor padrão para outros valores
            return f'color: {color};'

        # Aplicando a formatação condicional à coluna 'Resultado'
        styled_df = agroupTab.style.applymap(lambda x: color_text(x), subset=['Resultado'])

        # Exibindo o DataFrame com a formatação
        # st.write(styled_df)
        
        # st.dataframe(agroupTab.style.applymap(color_text, subset=['Resultado']), unsafe_allow_html=True,hide_index=True,height=1500,width=1600)

        st.dataframe(styled_df,hide_index=True,height=1400,width=1500) 

if __name__ == "__main__":
    run(cobranca_geral,telecobranca,acordoOnline,BaseLiqmes,BaseAliqMetas,colaborador)
    
