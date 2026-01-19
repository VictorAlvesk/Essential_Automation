import re

def normalizar_numero_br(valor: str) -> float:
    if not valor:
        return 0.0
    # Remove pontos de milhar (ex: 1.200,50 -> 1200,50)
    valor = valor.replace(".", "")
    # Troca vírgula decimal por ponto (ex: 1200,50 -> 1200.50)
    valor = valor.replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return 0.0

def normalizar_texto(texto: str) -> str:
    # Remove quebras de linha e normaliza espaços
    return " ".join(texto.upper().split())

def extrair_fatura(texto: str) -> dict:
    dados = {}
    texto = normalizar_texto(texto)

    # --- 1. MÊS E ANO ---
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

    # --- 3. DATAS DE LEITURA ---
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

    # --- 5. ENERGIA ATIVA (Consumo) ---
    dados["energia_ativa"] = 0.0
    m_ativa = re.search(r"ENERGIA ATIVA - KWH ÚNICO\s+\d+\s+\d+\s+[\d,]+\s+([\d,]+)", texto)
    if m_ativa:
        dados["energia_ativa"] = normalizar_numero_br(m_ativa.group(1))

    # --- 6. GERAÇÃO (Injetada) ---
    dados["energia_gerada"] = 0.0
    m_geracao_linha = re.search(r"ENERGIA GERAÇÃO - KWH ÚNICO\s+\d+\s+\d+\s+[\d,]+\s+([\d,]+)", texto)
    if m_geracao_linha:
        dados["energia_gerada"] = normalizar_numero_br(m_geracao_linha.group(1))
    
    # --- 7. BLOCO SCEE (Crédito e Saldo) ---
    dados["credito_recebido"] = 0.0
    dados["saldo"] = 0.0

    idx_scee = texto.find("INFORMAÇÕES DO SCEE")
    if idx_scee != -1:
        # Pega um bloco maior para garantir que o Saldo esteja dentro
        bloco_busca = texto[idx_scee : idx_scee + 1000]
        
        # Fallback Geração (se não achou na linha do medidor)
        if dados["energia_gerada"] == 0:
            m_ger_scee = re.search(r"GERAÇÃO CICLO.*?UC\s+\d+\s*:\s*([\d,]+)", bloco_busca)
            if m_ger_scee:
                dados["energia_gerada"] = normalizar_numero_br(m_ger_scee.group(1))
        
        # CRÉDITO RECEBIDO (Usa busca 'preguiçosa' .*?)
        m_credito = re.search(r"CRÉDITO RECEBIDO.*?(\d+,\d+)", bloco_busca)
        if m_credito:
            dados["credito_recebido"] = normalizar_numero_br(m_credito.group(1))

        # SALDO KWH (CORRIGIDO)
        # Procura "SALDO KWH", ignora dois pontos ou espaços, e pega números que podem ter PONTO (.) e VÍRGULA (,)
        # Exemplo que ele captura: "1.250,55" ou "0,00"
        m_saldo = re.search(r"SALDO KWH\s*[:=]?\s*([\d\.]+,\d{2})", bloco_busca)
        if m_saldo:
            dados["saldo"] = normalizar_numero_br(m_saldo.group(1))

    # --- 8. VALOR TOTAL ---
    m = re.search(r"TOTAL\s+(\d+,\d+)", texto)
    dados["valor_fatura"] = normalizar_numero_br(m.group(1)) if m else 0.0

    return dados