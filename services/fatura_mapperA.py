import re

def normalizar_numero_br(valor: str) -> float:
    if not valor:
        return 0.0
    # Remove pontos de milhar e substitui vírgula decimal por ponto
    valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return 0.0

def normalizar_texto(texto: str) -> str:
    return " ".join(texto.upper().split())

def extrair_historico_consumo(texto: str) -> list:
    """
    Extrai a tabela de histórico de Grupo A (image_b84cef.png).
    Captura: Mês/Ano, Demandas (P, FP, RE), Consumos (P, FP, RE) e Reservado.
    """
    historico = []
    # Regex para capturar Mês/Ano e a sequência de valores numéricos da tabela 
    # O padrão busca a sigla do mês, o ano e um bloco de 7 a 9 valores decimais
    padrao = r"(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\s*[\/\-]\s*(\d{2})((?:\s+[\d\.,]+){7,9})"
    
    matches = re.findall(padrao, texto)
    
    for mes, ano, valores_str in matches:
        v = valores_str.strip().split()
        if len(v) >= 7:
            historico.append({
                "mes": mes,
                "ano": int(ano),
                # Mapeamento seguindo a ordem da tabela da Equatorial 
                "demanda_p": normalizar_numero_br(v[0]),
                "demanda_fp": normalizar_numero_br(v[1]),
                "demanda_re": normalizar_numero_br(v[2]),
                "consumo_p": normalizar_numero_br(v[3]),
                "consumo_fp": normalizar_numero_br(v[4]),
                "consumo_re": normalizar_numero_br(v[5]),
                "reservado_consumo": normalizar_numero_br(v[6])
            })
    return historico

def extrair_fatura(texto: str) -> dict:
    dados = {}
    texto_bruto = texto # Mantém original para buscas sensíveis a quebra de linha
    texto = normalizar_texto(texto)

    # --- 1. MÊS, ANO E UC ---
    # Busca o padrão "UC MÊS/ANO" (ex: 140753532 DEZ/2025) [cite: 7]
    m = re.search(r"(\d{7,})\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)/(\d{4})", texto)
    dados["uc"] = m.group(1) if m else ""
    dados["mes"] = m.group(2) if m else ""
    dados["ano"] = int(m.group(3)) if m else 0

    # --- 2. DADOS DE CONSUMO E DEMANDA ATUAL (INDIVIDUAL) ---
    # Grupo A separa por postos tarifários (Ponta, Fora Ponta, Reservado) 
    pats = {
        "c_p": r"ENERGIA ATIVA-KWH\s+PONTA\s+\d+\s+\d+\s+[\d,.]+\s+([\d,.]+)",
        "c_fp": r"ENERGIA ATIVA-KWH\s+FORA PONTA\s+\d+\s+\d+\s+[\d,.]+\s+([\d,.]+)",
        "c_hr": r"ENERGIA ATIVA-KWH\s+RESERVADO\s+\d+\s+\d+\s+[\d,.]+\s+([\d,.]+)",
        "d_p": r"DEMANDA KW\s+PONTA\s+\d+\s+\d+\s+[\d,.]+\s+([\d,.]+)",
        "d_fp": r"DEMANDA KW\s+FORA PONTA\s+\d+\s+\d+\s+[\d,.]+\s+([\d,.]+)",
        "d_hr": r"DEMANDA KW\s+RESERVADO\s+\d+\s+\d+\s+[\d,.]+\s+([\d,.]+)"
    }
    
    for chave, pat in pats.items():
        match = re.search(pat, texto)
        dados[chave] = normalizar_numero_br(match.group(1)) if match else 0.0

    # --- 3. SALDO TOTAL SCEE (Soma P + FP + HR) ---
    # Captura a linha de saldo e soma os componentes (P, FP, HR) 
    dados["saldo"] = 0.0
    idx_scee = texto.find("INFORMAÇÕES DO SCEE")
    if idx_scee != -1:
        # Pega um bloco após o título para busca
        bloco = texto[idx_scee : idx_scee + 800]
        m_saldo = re.search(r"SALDO KWH.*?(?=SALDO A EXPIRAR|TOTAL|$)", bloco)
        if m_saldo:
            # Encontra todos os valores numéricos (0,00) no trecho do saldo
            valores = re.findall(r"[\d\.]*,\d{2}", m_saldo.group(0))
            dados["saldo"] = sum(normalizar_numero_br(v) for v in valores)

    # --- 4. VALOR TOTAL ---
    m_val = re.search(r"TOTAL\s+([\d\.]+,\d{2})", texto)
    dados["valor_fatura"] = normalizar_numero_br(m_val.group(1)) if m_val else 0.0

    # --- 5. HISTÓRICO COMPLETO ---
    dados["historico"] = extrair_historico_consumo(texto)

    # DEBUG
    print(f"\n[DEBUG MAPPER A] UC: {dados.get('uc')} | Mês Ref: {dados.get('mes')}")
    print(f"[DEBUG MAPPER A] Saldo Totalizado: {dados['saldo']}")
    print(f"[DEBUG MAPPER A] Itens Histórico: {len(dados['historico'])}\n")

    return dados