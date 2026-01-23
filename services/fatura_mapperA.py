import re

def normalizar_numero_br(valor: str) -> float:
    if not valor: return 0.0
    valor = valor.replace(".", "").replace(",", ".")
    try: return float(valor)
    except ValueError: return 0.0

def normalizar_texto(texto: str) -> str:
    return " ".join(texto.upper().split())

def extrair_historico_consumo(texto: str) -> list:
    historico = []
    padrao = r"(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\s*[\/\-]\s*(\d{2})((?:\s+[\d\.,]+){7,9})"
    matches = re.findall(padrao, texto)
    for mes, ano, valores_str in matches:
        v = valores_str.strip().split()
        if len(v) >= 7:
            historico.append({
                "mes": mes, "ano": ano,
                "d_p": normalizar_numero_br(v[0]), "d_fp": normalizar_numero_br(v[1]),
                "d_hr": normalizar_numero_br(v[2]), "c_p": normalizar_numero_br(v[3]),
                "c_fp": normalizar_numero_br(v[4]), "c_hr": normalizar_numero_br(v[6])
            })
    return historico

def extrair_fatura(texto: str) -> dict:
    dados = {}
    texto_norm = normalizar_texto(texto)
    
    # --- 1. MÊS, ANO E UC ---
    m_uc_mes = re.search(r"(\d{7,})\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)/(\d{4})", texto_norm)
    dados["uc"] = m_uc_mes.group(1) if m_uc_mes else ""
    dados["mes"] = m_uc_mes.group(2) if m_uc_mes else ""
    dados["ano"] = m_uc_mes.group(3)[2:] if m_uc_mes else "00"

    # --- 2. ENDEREÇO (Igual ao Grupo B) ---
    if "ENDEREÇO DE ENTREGA:" in texto_norm:
        trecho = texto_norm.split("ENDEREÇO DE ENTREGA:", 1)[1]
        dados["endereco"] = trecho.split("CEP:", 1)[0].strip()
    else:
        dados["endereco"] = ""

    # --- 3. DATAS DE LEITURA ---
    m_datas = re.search(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})", texto_norm)
    dados["data_leitura_anterior"] = m_datas.group(1) if m_datas else ""
    dados["data_leitura_atual"] = m_datas.group(2) if m_datas else ""

    # --- 4. CONSUMO E DEMANDA ATUAIS ---
    pats = {
        "c_p": r"ENERGIA ATIVA - KWH PONTA\s+\d+\s+\d+\s+[\d,]+\s+([\d,]+)",
        "c_fp": r"ENERGIA ATIVA - KWH FORA PONTA\s+\d+\s+\d+\s+[\d,]+\s+([\d,]+)",
        "c_hr": r"ENERGIA ATIVA - KWH RESERVADO\s+\d+\s+\d+\s+[\d,]+\s+([\d,]+)",
        "d_p": r"DEMANDA - KW PONTA\s+\d+\s+\d+\s+[\d,]+\s+([\d,]+)",
        "d_fp": r"DEMANDA - KW FORA PONTA\s+\d+\s+\d+\s+[\d,]+\s+([\d,]+)",
        "d_hr": r"DEMANDA - KW RESERVADO\s+\d+\s+\d+\s+[\d,]+\s+([\d,]+)"
    }
    for chave, pat in pats.items():
        m = re.search(pat, texto_norm)
        dados[chave] = normalizar_numero_br(m.group(1)) if m else 0.0

    # --- 5. GERAÇÃO E SALDO ---
    m_ger = re.search(r"ENERGIA (?:ATIVA|GERAÇÃO).*?INJETADA.*?\s+[\d,]+\s+([\d,]+)", texto_norm)
    dados["energia_gerada"] = normalizar_numero_br(m_ger.group(1)) if m_ger else 0.0
    
    dados["saldo"] = 0.0
    dados["credito_recebido"] = 0.0
    if "INFORMAÇÕES DO SCEE" in texto_norm:
        bloco = texto_norm[texto_norm.find("INFORMAÇÕES DO SCEE") : texto_norm.find("INFORMAÇÕES DO SCEE")+1000]
        m_cred = re.search(r"CRÉDITO RECEBIDO.*?([\d\.]+,\d{2})", bloco)
        dados["credito_recebido"] = normalizar_numero_br(m_cred.group(1)) if m_cred else 0.0
        m_s = re.search(r"SALDO KWH.*?(?=SALDO A EXPIRAR|TOTAL|$)", bloco)
        if m_s: dados["saldo"] = sum(normalizar_numero_br(v) for v in re.findall(r"[\d\.]*,\d{2}", m_s.group(0)))

    dados["historico"] = extrair_historico_consumo(texto_norm)
    m_val = re.search(r"TOTAL\s+([\d\.]+,\d{2})", texto_norm)
    dados["valor_fatura"] = normalizar_numero_br(m_val.group(1)) if m_val else 0.0
    
    return dados