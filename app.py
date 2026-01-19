import streamlit as st
import pdfplumber
import os
from services.fatura_mapper import extrair_fatura
from services.excel_writer import salvar_dados_em_lote

st.set_page_config(page_title="Balanço Equatorial", layout="wide")

st.title("⚡ Sistema de Balanço Energético")
st.info("Preenchimento automático das abas 'RESUMO' (UC/Endereço) e 'UC GERADORA'.")

col1, col2 = st.columns(2)
with col1:
    arquivo_excel = st.file_uploader("1. Envie a planilha Excel", type=["xlsx"])
with col2:
    arquivos_pdfs = st.file_uploader("2. Envie as 12 faturas (PDF)", type=["pdf"], accept_multiple_files=True)

if arquivo_excel and arquivos_pdfs:
    if st.button("Executar Preenchimento"):
        
        # Salva o Excel temporariamente
        with open("temp_base.xlsx", "wb") as f:
            f.write(arquivo_excel.getbuffer())
        
        lista_dados = []
        bar = st.progress(0)
        
        for i, pdf_file in enumerate(arquivos_pdfs):
            texto = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    texto += page.extract_text() or ""
            
            dados = extrair_fatura(texto)
            dados['arquivo'] = pdf_file.name
            lista_dados.append(dados)
            bar.progress((i + 1) / len(arquivos_pdfs))
        
        # Mostra tabela para conferência
        st.write("### Conferência dos Valores Extraídos")
        st.dataframe(lista_dados)
        
        # Salva no Excel
        arquivo_gerado = salvar_dados_em_lote("temp_base.xlsx", lista_dados)
        
        if arquivo_gerado:
            st.success("Planilha gerada com sucesso!")
            with open(arquivo_gerado, "rb") as f:
                st.download_button(
                    label="📥 Baixar Planilha Preenchida",
                    data=f,
                    file_name="Balanco_Preenchido.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            # Limpeza
            os.remove("temp_base.xlsx")