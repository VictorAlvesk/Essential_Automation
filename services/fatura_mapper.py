import re

def normalizar_numero_br(valor: str) -> float:
    if not valor:
        return 0.0
    valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return 0.0

def normalizar_texto(texto: str) -> str:
    return " ".join(texto.upper().split())

def extrair_historico_consumo(texto: str) -> list:
    """
    Busca o bloco de histórico (Ex: NOV/24 230) para preencher meses passados.
    Retorna lista: [{'mes': 'NOV', 'ano': 24, 'kwh': 230.0}, ...]
    """
    historico = []
    # Regex para capturar: MES/ANO (2 digitos) espaço NUMERO (kWh)
    # Ex: DEZ/24 518
    padrao = r"(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)[\/\-](\d{2,4})\s+([\d\.,]+)"
    
    matches = re.findall(padrao, texto)
    
    for mes, ano, kwh in matches:
        consumo = normalizar_numero_br(kwh)
        if consumo > 0:
            historico.append({
                "mes": mes.upper(),
                "ano": int(ano),
                "consumo": consumo
        })
    return historico

def extrair_fatura(texto: str) -> dict:
    dados = {}
    texto = normalizar_texto(texto)

    # --- 1. MÊS E ANO ATUAL ---
    m = re.search(r"(\d{7,})\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)/(\d{4})", texto)
    dados["uc"] = m.group(1) if m else ""
    dados["mes"] = m.group(2) if m else ""
    dados["ano"] = int(m.group(3)) if m else 0

    # --- 2. ENDEREÇO ---
    if "ENDEREÇO DE ENTREGA:" in texto:
        trecho = texto.split("ENDEREÇO DE ENTREGA:", 1)[1]
        dados["endereco"] = trecho.split("CEP:", 1)[0].strip()
    else:
        dados["endereco"] = ""

    # --- 3. DATAS ---
    m = re.search(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+\d+\s+\d{2}/\d{2}/\d{4}", texto)
    dados["data_leitura_anterior"] = m.group(1) if m else ""
    dados["data_leitura_atual"] = m.group(2) if m else ""

    # --- 4. MEDIDOR ---
    m = re.search(r"(\d{7,}-\d)\s+ENERGIA ATIVA - KWH ÚNICO\s+(\d+)\s+(\d+)", texto)
    if m:
        dados["medidor"] = m.group(1)
        dados["leitura_anterior"] = int(m.group(2))
        dados["leitura_atual"] = int(m.group(3))
    else:
        dados["medidor"] = "" 
        dados["leitura_anterior"] = 0
        dados["leitura_atual"] = 0

    # --- 5. ENERGIA ATIVA (Consumo Atual) ---
    dados["energia_ativa"] = 0.0
    m_ativa = re.search(r"ENERGIA ATIVA - KWH ÚNICO\s+\d+\s+\d+\s+[\d,]+\s+([\d,]+)", texto)
    if m_ativa:
        dados["energia_ativa"] = normalizar_numero_br(m_ativa.group(1))

    # --- 6. GERAÇÃO, CRÉDITO E SALDO ---
    dados["energia_gerada"] = 0.0
    dados["credito_recebido"] = 0.0
    dados["saldo"] = 0.0

    # Tenta geração na linha
    m_geracao_linha = re.search(r"ENERGIA GERAÇÃO - KWH ÚNICO\s+\d+\s+\d+\s+[\d,]+\s+([\d,]+)", texto)
    if m_geracao_linha:
        dados["energia_gerada"] = normalizar_numero_br(m_geracao_linha.group(1))
    
    # Bloco SCEE
    idx_scee = texto.find("INFORMAÇÕES DO SCEE")
    if idx_scee != -1:
        bloco_busca = texto[idx_scee : idx_scee + 1000]
        
        # Fallback Geração
        if dados["energia_gerada"] == 0:
            m_ger_scee = re.search(r"GERAÇÃO CICLO.*?UC\s+\d+\s*:\s*([\d,]+)", bloco_busca)
            if m_ger_scee:
                dados["energia_gerada"] = normalizar_numero_br(m_ger_scee.group(1))
        
        # Crédito
        m_credito = re.search(r"CRÉDITO RECEBIDO.*?([\d\.]+,\d{2})", bloco_busca)
        if m_credito:
            dados["credito_recebido"] = normalizar_numero_br(m_credito.group(1))

        # Saldo (com regex robusta para pontos e vírgulas)
        m_saldo = re.search(r"SALDO KWH\s*[:=]?\s*([\d\.]+,\d{2})", bloco_busca)
        if m_saldo:
            dados["saldo"] = normalizar_numero_br(m_saldo.group(1))

    # --- 7. VALOR ---
    m = re.search(r"TOTAL\s+([\d\.]+,\d{2})", texto)
    dados["valor_fatura"] = normalizar_numero_br(m.group(1)) if m else 0.0

    # --- 8. HISTÓRICO DE CONSUMO (NOVO) ---
    # Extrai lista de consumos passados para caso seja enviado apenas 1 PDF
    dados["historico"] = extrair_historico_consumo(texto)

    return dados