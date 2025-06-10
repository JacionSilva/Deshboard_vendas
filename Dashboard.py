import streamlit as st
import pandas as pd
import plotly.express as px
import requests 


st.set_page_config(page_title='Dashboard de Vendas', layout='wide') # configurando o título do dashboard


cliente = 'Jácion Silva'
st.title(f"Dashboard de Vendas :blue[{cliente}] :sunglasses:")

def formata_numero(valor, prefixo= ''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} Milhões'

url = 'https://labdados.com/produtos'
regioes = ['Brasil','Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul'] # lista de regiões do Brasil

st.sidebar.title('Filtros') # título da barra lateral
regiao = st.sidebar.selectbox('Selecione a região', regioes) # filtro de região
if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Todos os anos', value=True) # filtro de anos
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao': regiao.lower(), 'ano':ano}

response = requests.get(url, params=query_string) # fazendo a requisição para a API
dados = pd.DataFrame.from_dict(response.json()) # transformando reponse em json e json em dataframe

#quero converter o preço para float
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')# convertendo a coluna de data para o formato datetime
filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique(), default=dados['Vendedor'].unique()) # filtro de vendedores
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)] # filtrando os dados pelos vendedores selecionados

## Tabelas

### Tabelas de Receitas mensais e por estado
receita_estados = dados.groupby('Local da compra')[['Preço']].sum().reset_index()
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))[['Preço']].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()
receita_mensal['Ano-Mês'] = receita_mensal['Data da Compra'].dt.strftime('%Y-%m')
receita_mensal = receita_mensal.sort_values('Data da Compra')
# Junta as receitas com as coordenadas
coordenadas = dados.drop_duplicates(subset=['Local da compra'])[['Local da compra', 'lat', 'lon']]  # Pega as coordenadas únicas de cada estado
receita_estados = receita_estados.merge(coordenadas, on='Local da compra', how='left')

### Tabelas de quantidade de vendas por estado, mensal e por categoria
mapa_qtd_vend = dados.groupby('Local da compra')[['Produto']].count().reset_index()


# Junta as receitas com as coordenadas
mapa_qtd_vend = mapa_qtd_vend.merge(coordenadas, on='Local da compra', how='left')

#Quantidade de vendas mensal
qtd_venda_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))[['Produto']].count().reset_index()
qtd_venda_mensal['Ano'] = qtd_venda_mensal['Data da Compra'].dt.year
qtd_venda_mensal['Mes'] = qtd_venda_mensal['Data da Compra'].dt.month_name()
qtd_venda_mensal['Ano-Mês'] = qtd_venda_mensal['Data da Compra'].dt.strftime('%Y-%m')
qtd_venda_mensal = qtd_venda_mensal.sort_values('Data da Compra')

## Agrupando os dados por categoria de produtos e receita por categoria
receitas_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().reset_index().sort_values('Preço', ascending=False)
qtd_categoria_mensal = dados.groupby('Categoria do Produto')[['Produto']].count().reset_index()
qtd_vendas = pd.DataFrame(dados.groupby('Categoria do Produto')[['Produto']].agg(['count']))
### Tabebelas Vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))
receita_por_vendedor = dados.groupby('Vendedor')[['Preço']].sum().reset_index()



## Gráficos
fig_mapa_receita = px.scatter_geo(
                                    receita_estados,
                                    lat='lat',
                                    lon='lon',
                                    scope='south america',
                                    size='Preço',
                                    template='seaborn',
                                    hover_name='Local da compra',
                                    hover_data={'lat': False, 'lon': False},
                                    title='Receita por Estado'
                                )
fig_mapa_receita.update_layout(coloraxis_colorbar=dict(title='Receita (R$)'),yaxis_title='Receita (R$)')  # Atualiza o título da barra de cores e do eixo Y
#grafico de receita mensal
fig_receita_mensal = px.line(
                                    receita_mensal,
                                    x='Mes',
                                    y='Preço',
                                    markers=True,
                                    color='Ano',
                                    line_dash='Ano',
                                    title='Receita Mensal'
                                )
fig_receita_mensal.update_layout(yaxis_title='Receita (R$)')
#fig_receita_mensal.update_yaxes(tickformat=",.0f")  # Mostra 120,000 ao invés de 120k ou 120.000  # Mostra sem casas decimais e com separador# Força separador de milhar americano
# Gráfico de receita por estado
fig_receita_estados = px.bar(receita_estados.head(),
                                    x = 'Local da compra',
                                    y = 'Preço',
                                    text_auto = True,
                                    title = 'Top estados')

fig_receita_estados.update_layout(yaxis_title = 'Receita')
# Gráfico de receita por categoria
fig_receita_categorias = px.bar(
                                    receitas_categoria,
                                    x='Categoria do Produto',
                                    y='Preço',
                                    text_auto=True,
                                    title='Receita por categoria'
                                )
fig_receita_categorias.update_layout(yaxis_title = 'Receita')

# Gráfico de quantidade de vendas por estado
fig_mapa_qtd_venda = px.scatter_geo(
                                    mapa_qtd_vend,
                                    lat='lat',
                                    lon='lon',
                                    scope='south america',
                                    size='Produto',
                                    template='seaborn',
                                    hover_name='Local da compra',
                                    hover_data={'lat': False, 'lon': False},
                                    title='Quantidade de vendas por Estado'
                                )
# Gráfico de quantidade de vendas mensal
fig_qtd_venda_mensal = px.line(
                                    qtd_venda_mensal,
                                    x='Mes',
                                    y='Produto',
                                    markers=True,
                                    color='Ano',
                                    line_dash='Ano',
                                    title='Quantidade de vendas por mês'
                                )
fig_qtd_venda_mensal.update_layout(yaxis_title='Quantidade')
# Gráfico de quantidade de vendas por categoria
fig_qtd_venda_mensal_categoria = px.bar(
                                    qtd_categoria_mensal,
                                    x='Categoria do Produto',
                                    y='Produto',
                                    text_auto=True,
                                    title='Quantidade por categoria'
                                )
fig_qtd_venda_mensal_categoria.update_layout(yaxis_title = 'Quantidade')



# Gráfico de receita por vendedor
fig_receita_vendedores = px.bar(
                                    receita_por_vendedor.head(),
                                    x = 'Vendedor',
                                    y = 'Preço',
                                    text_auto = True,
                                    title = 'Top Vendedores')
fig_receita_vendedores.update_layout(yaxis_title = 'Receita (R$)')

# Tabs para organizar as visualizações
st.sidebar.header('Configurações')  # Cabeçalho da barra lateral
aba1, aba2, aba3= st.tabs(['Mapa de Receita', 'Quantidade de vendas', 'Vendedores'])
with aba1: # aba1 receitas 
    ## Visualização no streamlit
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_categorias, use_container_width = True)
with aba2:# aba2 quantidade de vendas
    ## Visualização no streamlit
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_qtd_venda, use_container_width = True)
        st.plotly_chart(fig_qtd_venda_mensal_categoria, use_container_width = True)
        #st.plotly_chart(fig_qtd_vendas, use_container_width = True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_qtd_venda_mensal, use_container_width = True)

with aba3:# aba3 vendedores
    #qtd_vendedores = st.number_input('Quantidade de vendedores', min_value=1, max_value=50, value=10, step=1)
    qtd_vendedores = st.number_input('Quantidade de Vendedores', 2, 10, 5)

    ## Visualização no streamlit
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_receita_vendedores, use_container_width = True)
        #criando um gráfico de barras para os vendedores
        fig_receita_vendedores_top = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                            x='sum',
                                            y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                            text_auto=True,
                                            title=f'Top {qtd_vendedores} Vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores_top)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores_top = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                            x='count',
                                            y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                            text_auto=True,
                                            title=f'Top {qtd_vendedores} Vendedores (Quantidade de Vendas)')
        st.plotly_chart(fig_vendas_vendedores_top)



#st.write("Amostra dos valores de Preço após conversão:", dados['Preço'].head(10))
#st.write("Tipo dos dados em Preço:", dados['Preço'].dtype)
#st.dataframe(dados) # forma de apresentar dataframe no streamlit

