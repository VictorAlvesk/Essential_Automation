import streamlit as st
import pdfplumber
import os
from services.fatura_mapper import extrair_fatura
from services.excel_writer import preparar_planilha, salvar_dados_multiplos

st.set_page_config(page_title="Balanço Equatorial Multi-UC", layout="wide")

st.title("⚡ Sistema de Balanço Energético (Multi-UC)")
st.subheader("Essencial Energia Eficiente")
st.markdown("Configure a quantidade de UCs, faça o upload da planilha base e das faturas.")

# --- BARRA LATERAL PARA CONFIGURAÇÃO ---
with st.sidebar:
    st.header("Configuração")
    qtd_geradoras = st.number_input("Qtd. de UC Geradoras", min_value=1, value=1, step=1)
    qtd_beneficiarias = st.number_input("Qtd. de UC Beneficiárias", min_value=0, value=0, step=1)

# --- UPLOAD DA PLANILHA BASE ---
st.subheader("1. Planilha Modelo")
arquivo_excel = st.file_uploader("Envie o arquivo 'BALANÇO E COMPENSAÇÃO.xlsx'", type=["xlsx"])

# --- UPLOADS DINÂMICOS ---
if arquivo_excel:
    dados_processamento = []
    
    st.subheader("2. Upload das Faturas")
    
    # Cria abas visuais no Streamlit para organizar os uploads
    abas_titulos = [f"Geradora {i+1}" for i in range(qtd_geradoras)] + \
                   [f"Beneficiária {i+1}" for i in range(qtd_beneficiarias)]
    tabs = st.tabs(abas_titulos)
    
    idx_tab = 0
    
    # --- Loop para Geradoras ---
    for i in range(qtd_geradoras):
        with tabs[idx_tab]:
            st.markdown(f"**Geradora {i+1}**: Envie as 12 faturas (Jan a Dez)")
            pdfs = st.file_uploader(f"Faturas - Geradora {i+1}", type=["pdf"], accept_multiple_files=True, key=f"ger_{i}")
            
            if pdfs:
                dados_processamento.append({
                    'tipo': 'geradora',
                    'indice': i + 1,
                    'arquivos': pdfs
                })
        idx_tab += 1

    # --- Loop para Beneficiárias ---
    for i in range(qtd_beneficiarias):
        with tabs[idx_tab]:
            st.markdown(f"**Beneficiária {i+1}**: Envie as 12 faturas (Jan a Dez)")
            pdfs = st.file_uploader(f"Faturas - Beneficiária {i+1}", type=["pdf"], accept_multiple_files=True, key=f"ben_{i}")
            
            if pdfs:
                dados_processamento.append({
                    'tipo': 'beneficiaria',
                    'indice': i + 1,
                    'arquivos': pdfs
                })
        idx_tab += 1

    # --- BOTÃO DE PROCESSAMENTO ---
    st.markdown("---")
    if st.button("🚀 Processar Todas as UCs e Gerar Planilha"):
        if len(dados_processamento) == 0:
            st.warning("Por favor, envie faturas para pelo menos uma UC.")
        else:
            # Barra de progresso geral
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            lista_dados_finais = []
            
            # Passo 1: Extrair dados de todos os PDFs
            total_items = len(dados_processamento)
            
            for idx, item in enumerate(dados_processamento):
                status_text.text(f"Processando UC {item['tipo'].title()} {item['indice']}...")
                
                faturas_extraidas = []
                for pdf_file in item['arquivos']:
                    texto = ""
                    with pdfplumber.open(pdf_file) as pdf:
                        for page in pdf.pages:
                            texto += page.extract_text() or ""
                    
                    dados = extrair_fatura(texto)
                    faturas_extraidas.append(dados)
                
                # Guarda os dados extraídos estruturados
                lista_dados_finais.append({
                    'tipo': item['tipo'],
                    'indice': item['indice'],
                    'dados': faturas_extraidas
                })
                
                progress_bar.progress((idx + 1) / (total_items + 1)) # +1 pois ainda tem o Excel
            
            # Passo 2: Manipular o Excel
            status_text.text("Gerando abas e escrevendo no Excel...")
            
            # Carrega e prepara abas (duplicação)
            wb_preparado = preparar_planilha(arquivo_excel, qtd_geradoras, qtd_beneficiarias)
            
            # Preenche os dados
            wb_final = salvar_dados_multiplos(wb_preparado, lista_dados_finais)
            
            progress_bar.progress(100)
            status_text.text("Concluído!")
            
            # Salva em memória para download
            nome_saida = "BALANÇO_COMPLETO.xlsx"
            wb_final.save(nome_saida) 
            
            st.success("Planilha gerada com sucesso! As abas foram criadas e o Resumo atualizado.")
            
            with open(nome_saida, "rb") as f:
                st.download_button(
                    label="📥 Baixar Planilha Final",
                    data=f,
                    file_name=nome_saida,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )