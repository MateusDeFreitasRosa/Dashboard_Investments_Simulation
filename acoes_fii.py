import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime

# Configurar a página para wide mode
st.set_page_config(layout="wide")

st.title("Simulação de Investimentos em Ações ou FIIs")

# Entrada de dados pelo usuário
st.sidebar.header("Parâmetros da Simulação")

# Tipo de investimento
tipo_investimento = st.sidebar.selectbox("Tipo de Investimento", ["Ações", "FIIs"])

# Aporte inicial
aporte_inicial = st.sidebar.number_input("Aporte Inicial (R$)", value=10000.0, step=1000.0, format="%.2f")

# Aporte mensal
aporte_mensal = st.sidebar.number_input("Aporte Mensal (R$)", value=1000.0, step=100.0, format="%.2f")

# Tempo de investimento
tempo_meses = st.sidebar.number_input("Tempo de Investimento (meses)", value=60, step=1)

# Taxa de retorno
taxa_tipo = st.sidebar.selectbox("Tipo de Taxa de Retorno", ["Anual", "Mensal"])
taxa_retorno = st.sidebar.number_input(f"Taxa de Retorno {taxa_tipo} (%)", value=12.0, step=0.1, format="%.2f")

# Dividend Yield médio
dividend_yield = st.sidebar.number_input("Dividend Yield Médio (%)", value=6.0, step=0.1, format="%.2f")

# Reinvestimento dos dividendos
reinvestir_dividendos = st.sidebar.checkbox("Reinvestir Dividendos", value=True)

# Inflação
inflacao_anual = st.sidebar.number_input("Inflação Anual (%)", value=4.0, step=0.1, format="%.2f")

# Conversão da taxa de retorno para mensal se necessário
if taxa_tipo == "Anual":
    taxa_retorno_mensal = (1 + taxa_retorno / 100) ** (1/12) - 1
else:
    taxa_retorno_mensal = taxa_retorno / 100

# Taxa de inflação mensal
inflacao_mensal = (1 + inflacao_anual / 100) ** (1/12) - 1

# Obter a data atual
data_inicial = datetime.date.today()

# Criar um range de datas mensais a partir de hoje
datas = pd.date_range(start=data_inicial, periods=tempo_meses, freq='MS')

# Cálculo da simulação
saldo = np.zeros(tempo_meses)
valor_aplicado = np.zeros(tempo_meses)
dividendos = np.zeros(tempo_meses)

saldo[0] = aporte_inicial
valor_aplicado[0] = aporte_inicial

for i in range(1, tempo_meses):
    saldo[i] = saldo[i - 1] * (1 + taxa_retorno_mensal)
    valor_aplicado[i] = valor_aplicado[i - 1] + aporte_mensal
    dividendos[i] = saldo[i - 1] * (dividend_yield / 100) / 12
    if reinvestir_dividendos:
        saldo[i] += aporte_mensal + dividendos[i]
    else:
        saldo[i] += aporte_mensal

# Ajuste pela inflação
meses = np.arange(1, tempo_meses + 1)
saldo_real = saldo / ((1 + inflacao_mensal) ** meses)
valor_aplicado_real = valor_aplicado / ((1 + inflacao_mensal) ** meses)

# Criação do DataFrame para visualização
df = pd.DataFrame({
    'Data': datas,
    'Mês': meses,
    'Saldo Total (R$)': saldo,
    'Valor Aplicado (R$)': valor_aplicado,
    'Saldo Real (R$)': saldo_real,
    'Valor Aplicado Real (R$)': valor_aplicado_real,
    'Dividendos Mensais (R$)': dividendos
})

# Adicionar coluna de ano
df['Ano'] = df['Data'].dt.year

# Agregar dados por ano
df_ano = df.groupby('Ano').agg({
    'Dividendos Mensais (R$)': 'sum',
    'Saldo Total (R$)': 'last',
    'Valor Aplicado (R$)': 'last',
    'Saldo Real (R$)': 'last',
    'Valor Aplicado Real (R$)': 'last'
}).reset_index()

# Renomear colunas para clareza
df_ano.rename(columns={
    'Dividendos Mensais (R$)': 'Dividendos Anuais (R$)',
    'Saldo Total (R$)': 'Saldo Total Anual (R$)',
    'Valor Aplicado (R$)': 'Valor Aplicado Anual (R$)',
    'Saldo Real (R$)': 'Saldo Real Anual (R$)',
    'Valor Aplicado Real (R$)': 'Valor Aplicado Real Anual (R$)'
}, inplace=True)

# Calcular o impacto da inflação
df_ano['Impacto da Inflação (R$)'] = df_ano['Saldo Total Anual (R$)'] - df_ano['Saldo Real Anual (R$)']

# Gráficos
st.header("Resultados da Simulação")

# Colocar os gráficos lado a lado
col1, col2 = st.columns(2)

with col1:
    st.subheader("Evolução do Patrimônio")
    chart_data = df[['Data', 'Saldo Total (R$)', 'Valor Aplicado (R$)']].melt('Data')
    chart = alt.Chart(chart_data).mark_line().encode(
        x=alt.X('Data:T', title='Data', axis=alt.Axis(format='%b %Y')),
        y=alt.Y('value:Q', title='Valor (R$)'),
        color=alt.Color('variable:N', title='Legenda'),
        tooltip=[
            alt.Tooltip('Data:T', title='Data', format='%b %Y'),
            alt.Tooltip('variable:N', title='Categoria'),
            alt.Tooltip('value:Q', title='Valor (R$)', format=',.2f')
        ]
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

with col2:
    st.subheader("Evolução da Renda Passiva Mensal")
    chart = alt.Chart(df).mark_line(color='green').encode(
        x=alt.X('Data:T', title='Data', axis=alt.Axis(format='%b %Y')),
        y=alt.Y('Dividendos Mensais (R$):Q', title='Dividendos Mensais (R$)'),
        tooltip=[
            alt.Tooltip('Data:T', title='Data', format='%b %Y'),
            alt.Tooltip('Dividendos Mensais (R$):Q', format=',.2f')
        ]
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

# Tabela de resultados finais
st.subheader("Resumo dos Resultados")

col1, col2 = st.columns(2)

with col1:
    st.metric("Saldo Total (R$)", f"{saldo[-1]:,.2f}")
    st.metric("Valor Aplicado (R$)", f"{valor_aplicado[-1]:,.2f}")
    st.metric("Total de Dividendos Recebidos (R$)", f"{dividendos.sum():,.2f}")

with col2:
    st.metric("Saldo Total Real (R$)", f"{saldo_real[-1]:,.2f}")
    st.metric("Valor Aplicado Real (R$)", f"{valor_aplicado_real[-1]:,.2f}")

# Seção para os novos gráficos
st.header("Análises Anuais dos Investimentos")

# Primeiro par de gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Evolução de Saldo de Dividendos por Ano")
    # Criar o gráfico de barras
    chart_dividendos = alt.Chart(df_ano).mark_bar().encode(
        x=alt.X('Ano:O', title='Ano'),
        y=alt.Y('Dividendos Anuais (R$):Q', title='Dividendos Anuais (R$)'),
        tooltip=[
            alt.Tooltip('Ano:O'),
            alt.Tooltip('Dividendos Anuais (R$):Q', format=',.2f')
        ]
    )

    # Criar a camada de texto para os labels
    text_dividendos = chart_dividendos.mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        text=alt.Text('Dividendos Anuais (R$):Q', format=',.2f')
    )

    # Combinar o gráfico de barras com os labels
    chart_dividendos = (chart_dividendos + text_dividendos).interactive()

    # Exibir o gráfico
    st.altair_chart(chart_dividendos, use_container_width=True)

with col2:
    st.subheader("Evolução de Patrimônio e Impacto da Inflação por Ano")
    
    # Gráfico de barras para o Saldo Total Anual
    chart_patrimonio = alt.Chart(df_ano).mark_bar().encode(
        x=alt.X('Ano:O', title='Ano'),
        y=alt.Y('Saldo Total Anual (R$):Q', title='Saldo Total Anual (R$)'),
        tooltip=[
            alt.Tooltip('Ano:O'),
            alt.Tooltip('Saldo Total Anual (R$):Q', format=',.2f')
        ]
    )

    # Camada de texto para as barras (Saldo Total Anual)
    text_patrimonio = chart_patrimonio.mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        text=alt.Text('Saldo Total Anual (R$):Q', format=',.2f')
    )

    # Gráfico de linha para o Impacto da Inflação
    chart_inflacao = alt.Chart(df_ano).mark_line(color='red').encode(
        x=alt.X('Ano:O', title='Ano'),
        y=alt.Y('Impacto da Inflação (R$):Q',),
        tooltip=[
            alt.Tooltip('Ano:O'),
            alt.Tooltip('Impacto da Inflação (R$):Q', format=',.2f')
        ]
    )

    # Pontos da linha de inflação com labels
    pontos_inflacao = chart_inflacao.mark_point(size=60).encode(
        y=alt.Y('Impacto da Inflação (R$):Q')
    )

    # Camada de texto para os pontos da linha de inflação
    text_inflacao = chart_inflacao.mark_text(
        align='center',
        baseline='bottom',
        dy=-10,
        color='black'
    ).encode(
        text=alt.Text('Impacto da Inflação (R$):Q', format=',.2f')
    )

    # Combinar o gráfico de barras com a linha de inflação, pontos e labels
    chart_combinado = (
        (chart_patrimonio + text_patrimonio + chart_inflacao + pontos_inflacao + text_inflacao)
        .interactive()
    )

    # Exibir o gráfico combinado
    st.altair_chart(chart_combinado, use_container_width=True)

# Segundo par de gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Evolução do Valor Aplicado por Ano")
    # Criar o gráfico de barras
    chart_valor_aplicado = alt.Chart(df_ano).mark_bar().encode(
        x=alt.X('Ano:O', title='Ano'),
        y=alt.Y('Valor Aplicado Anual (R$):Q', title='Valor Aplicado Anual (R$)'),
        tooltip=[
            alt.Tooltip('Ano:O'),
            alt.Tooltip('Valor Aplicado Anual (R$):Q', format=',.2f')
        ]
    )

    # Criar a camada de texto para os labels
    text_valor_aplicado = chart_valor_aplicado.mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        text=alt.Text('Valor Aplicado Anual (R$):Q', format=',.2f')
    )

    # Combinar o gráfico de barras com os labels
    chart_valor_aplicado = (chart_valor_aplicado + text_valor_aplicado).interactive()

    # Exibir o gráfico
    st.altair_chart(chart_valor_aplicado, use_container_width=True)

with col2:
    st.subheader("Impacto da Inflação sobre o Patrimônio por Ano")
    # Criar o gráfico de barras
    chart_inflacao = alt.Chart(df_ano).mark_bar().encode(
        x=alt.X('Ano:O', title='Ano'),
        y=alt.Y('Impacto da Inflação (R$):Q', title='Impacto da Inflação (R$)'),
        tooltip=[
            alt.Tooltip('Ano:O'),
            alt.Tooltip('Impacto da Inflação (R$):Q', format=',.2f')
        ]
    )

    # Criar a camada de texto para os labels
    text_inflacao = chart_inflacao.mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        text=alt.Text('Impacto da Inflação (R$):Q', format=',.2f')
    )

    # Combinar o gráfico de barras com os labels
    chart_inflacao = (chart_inflacao + text_inflacao).interactive()

    # Exibir o gráfico
    st.altair_chart(chart_inflacao, use_container_width=True)

# Mostrar tabela detalhada (opcional)
if st.checkbox("Mostrar tabela detalhada"):
    st.subheader("Detalhamento Mensal")
    st.write(df)

# Conclusões e insights
st.header("Análise e Insights")

st.write("""
- **Taxa de Retorno Mensal (%)**: Representa a valorização do investimento devido ao aumento do preço das ações ou cotas de FIIs. É o ganho de capital.
- **Dividend Yield Médio (%)**: Indica a renda passiva gerada pelo investimento por meio dos dividendos distribuídos.
- **Renda Passiva**: O gráfico de dividendos mensais mostra como sua renda passiva pode aumentar ao longo do tempo, especialmente se os dividendos forem reinvestidos.
- **Crescimento do Patrimônio**: A diferença entre o saldo total e o valor aplicado demonstra os ganhos obtidos com o investimento.
- **Impacto da Inflação**: Ajustar os valores pela inflação permite entender o poder de compra real do seu patrimônio ao longo do tempo.
- **Aportes Mensais**: Contribuem significativamente para o crescimento do patrimônio e da renda passiva.
""")
