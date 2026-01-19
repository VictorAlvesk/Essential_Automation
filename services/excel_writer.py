import openpyxl

def salvar_dados_em_lote(caminho_arquivo, lista_dados):
    try:
        wb = openpyxl.load_workbook(caminho_arquivo)
        
        # --- 1. PREENCHER ABA RESUMO (F7 e G7) ---
        if lista_dados:
            dados_base = lista_dados[0]
            ws_resumo = None
            for sheet in wb.sheetnames:
                if "RESUMO" in sheet.upper():
                    ws_resumo = wb[sheet]
                    break
            
            if ws_resumo:
                ws_resumo["F7"] = dados_base.get("uc", "")
                ws_resumo["G7"] = dados_base.get("endereco", "")

        # --- 2. PREENCHER ABA UC GERADORA ---
        ws_geradora = wb["UC GERADORA"] if "UC GERADORA" in wb.sheetnames else wb.active

        mapa_meses = {
            "JAN": "Jan", "FEV": "Fev", "MAR": "Mar", "ABR": "Abr",
            "MAI": "Mai", "JUN": "Jun", "JUL": "Jul", "AGO": "Ago",
            "SET": "Set", "OUT": "Out", "NOV": "Nov", "DEZ": "Dez"
        }

        # --- DEFINIÇÃO DAS COLUNAS ---
        col_leitura_ant = "B"
        col_leitura_atual = "C"
        
        col_geracao_injetada = "I"  # Energia Geração
        col_credito_recebido = "J"  # Crédito Recebido
        col_energia_ativa = "K"     # Energia Ativa (Consumo)
        col_valor_fatura = "N"      # Valor Total
        col_saldo = "P"             # Saldo Kwh
        
        col_medidor = "R"
        col_leitura_med_ant = "S"
        col_leitura_med_atual = "T"

        for dados in lista_dados:
            mes_pdf = dados.get("mes", "")
            if not mes_pdf or mes_pdf not in mapa_meses:
                continue 
            
            mes_excel = mapa_meses[mes_pdf]
            
            # Encontrar a linha do mês (Procurando da linha 5 até 40)
            linha_destino = None
            for row in range(5, 40):
                celula = ws_geradora[f"A{row}"].value
                if celula and str(celula).strip() == mes_excel:
                    linha_destino = row
                    break
            
            if linha_destino:
                ws_geradora[f"{col_leitura_ant}{linha_destino}"] = dados["data_leitura_anterior"]
                ws_geradora[f"{col_leitura_atual}{linha_destino}"] = dados["data_leitura_atual"]
                
                # Valores Numéricos
                ws_geradora[f"{col_geracao_injetada}{linha_destino}"] = dados["energia_gerada"]
                ws_geradora[f"{col_credito_recebido}{linha_destino}"] = dados["credito_recebido"]
                ws_geradora[f"{col_energia_ativa}{linha_destino}"] = dados["energia_ativa"]
                ws_geradora[f"{col_valor_fatura}{linha_destino}"] = dados["valor_fatura"]
                ws_geradora[f"{col_saldo}{linha_destino}"] = dados["saldo"]
                
                # Medidor
                ws_geradora[f"{col_medidor}{linha_destino}"] = dados["medidor"]
                ws_geradora[f"{col_leitura_med_ant}{linha_destino}"] = dados["leitura_anterior"]
                ws_geradora[f"{col_leitura_med_atual}{linha_destino}"] = dados["leitura_atual"]

        output_filename = "BALANÇO_FINAL.xlsx"
        wb.save(output_filename)
        return output_filename

    except Exception as e:
        print(f"Erro ao salvar Excel: {e}")
        return None