import streamlit as st
import pandas as pd
import plotly.express as px
import requests 
from io import BytesIO
import time



st.set_page_config(page_title='DADAOS BRUTOS', layout='wide') # configurando o título do dashboard
# Função para converter para CSV
@st.cache_data
def converter_df_para_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Função para converter para Excel
@st.cache_data
def converter_df_para_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Dados', index=False)
        # Ajustar automaticamente a largura das colunas
        worksheet = writer.sheets['Dados']
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)
    
    output.seek(0)
    return output.getvalue()
# Configuração do título e ícone
def mensagem_sucesso():
    sucesso = st.success("Dados carregados com sucesso!", icon="✅")
    time.sleep(5)  # Pausa para mostrar a mensagem
    sucesso.empty()  # Limpa a mensagem após 5 segundos


url = 'https://labdados.com/produtos'
response = requests.get(url) # fazendo a requisição para a API
dados = pd.DataFrame.from_dict(response.json()) # transformando reponse em json e json em dataframe
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y') # convertendo a coluna Data da Compra para datetime


with st.expander('Colunas'):
    colunas = st.multiselect('Selecione as colunas', list(dados.columns),list(dados.columns)) # multiselect para selecionar as colunas a serem exibidas

#filtros da barra lateral
st.sidebar.title('Filtros') # título da barra lateral

#trabalhar com cash
with st.sidebar.expander('Nome do produto'):
    produtos = st.multiselect('Selecione os produtos', dados['Produto'].unique(), dados['Produto'].unique())
with st.sidebar.expander('Categoria do produto'):
    categoria = st.multiselect('Selecione as categorias', dados['Categoria do Produto'].unique(), dados['Categoria do Produto'].unique())
with st.sidebar.expander('Preço do produto'):
    preco = st.slider('Selecione o preço', 0, 5000, (0,5000))
with st.sidebar.expander('Frete da venda'):
    frete = st.slider('Frete', 0,250, (0,250))
with st.sidebar.expander('Data da compra'):
    data_compra = st.date_input('Selecione a data', (dados['Data da Compra'].min(), dados['Data da Compra'].max()))
with st.sidebar.expander('Vendedor'):
    vendedores = st.multiselect('Selecione os vendedores', dados['Vendedor'].unique(), dados['Vendedor'].unique())
with st.sidebar.expander('Local da compra'):
    local_compra = st.multiselect('Selecione o local da compra', dados['Local da compra'].unique(), dados['Local da compra'].unique())
with st.sidebar.expander('Avaliação da compra'):
    avaliacao = st.slider('Selecione a avaliação da compra',1,5, value = (1,5))
with st.sidebar.expander('Tipo de pagamento'):
    tipo_pagamento = st.multiselect('Selecione o tipo de pagamento',dados['Tipo de pagamento'].unique(), dados['Tipo de pagamento'].unique())
with st.sidebar.expander('Quantidade de parcelas'):
    qtd_parcelas = st.slider('Selecione a quantidade de parcelas', 1, 24, (1,24))

query = '''
Produto in @produtos and \
`Categoria do Produto` in @categoria and \
@preco[0] <= Preço <= @preco[1] and \
@frete[0] <= Frete <= @frete[1] and \
@data_compra[0] <= `Data da Compra` <= @data_compra[1] and \
Vendedor in @vendedores and \
`Local da compra` in @local_compra and \
@avaliacao[0]<= `Avaliação da compra` <= @avaliacao[1] and \
`Tipo de pagamento` in @tipo_pagamento and \
@qtd_parcelas[0] <= `Quantidade de parcelas` <= @qtd_parcelas[1]
'''
dados_filtrados = dados.query(query)
dados_filtrados = dados_filtrados[colunas]

st.dataframe(dados_filtrados)
#ValueError: operands could not be broadcast together with shapes (9435,) (2,)
st.markdown(f'### Dados filtrados com {len(colunas)} colunas selecionadas')
st.markdown(f'A tabela possui :blue[{dados_filtrados.shape[0]}] linhas e :blue[{dados_filtrados.shape[1]}] colunas')
#fazer um download do dataframe filtrado
# Seção de download
st.markdown('### Escolha o formato para download:')
col1, col2 = st.columns(2)

with col1:
    formato_escolhido = st.radio("Selecione o formato:", ('CSV', 'Excel'))

with col2:
    digite_nome = st.text_input('', label_visibility = 'collapsed', value = 'dados')
    if formato_escolhido == 'CSV':
        data = converter_df_para_csv(dados_filtrados)
        nome_arquivo = digite_nome+'.csv'
        mime = 'text/csv'
        
        st.download_button(
            label=f'📥 Download em CSV',
            data=data,
            file_name=nome_arquivo,
            mime=mime,
            help='Clique para baixar os dados em formato CSV'
        )
    else:
        try:
            data = converter_df_para_excel(dados_filtrados)
            nome_arquivo = digite_nome+'.xlsx'
            mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            st.download_button(
                label=f'📥 Download em Excel',
                data=data,
                file_name=nome_arquivo,
                mime=mime,
                help='Clique para baixar os dados em formato Excel'
            )
        except Exception as e:
            st.error(f"Erro ao gerar arquivo Excel: {str(e)}")

# Adicionar informações sobre o download
with st.expander("ℹ️ Informações sobre o download"):
    st.markdown("""
    - **CSV**: Formato mais leve e universal, ideal para grandes volumes de dados
    - **Excel**: Formato mais amigável para visualização, com formatação automática
    
    Os dados baixados incluirão todas as colunas e filtros selecionados acima.
    """)

# Opções adicionais de exportação
with st.expander("⚙️ Configurações de exportação"):
    if formato_escolhido == 'Excel':
        sheet_name = st.text_input("Nome da planilha", "Dados")
        incluir_data = st.checkbox("Incluir data no nome do arquivo", True)
        
        if incluir_data:
            from datetime import datetime
            data_atual = datetime.now().strftime("%Y%m%d")
            nome_arquivo = f'dados_filtrados_{data_atual}.xlsx'

# Mostrar preview dos dados
with st.expander("👁️ Preview dos dados para download"):
    st.dataframe(dados_filtrados.head(5))
    st.info(f"Total de registros para download: {len(dados_filtrados)}")

st.markdown('---')


