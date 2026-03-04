"""Gerador de relatório Excel e CSV para consulta on-demand.

Portado de monitor-rodovias/report/excel_generator.py (versão simplificada
para uma única rota consultada por vez).

Colunas:
  Rota | Status | Atraso (min) | Confiança | Incidente Principal |
  Velocidade Atual (km/h) | Jam Factor | Fontes | Atualizado em |
  Link Waze | Link Google Maps
"""
import csv
import io
import unicodedata
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# ===== Paleta de cores (portado de excel_generator.py) =====

CORES = {
    "header_bg": "0F4C81",
    "header_font": "FFFFFF",
    "title_bg": "EAF2FA",
    "subtitle_font": "4F5D6B",
    "normal_bg": "D5F5E3",
    "normal_font": "1E8449",
    "moderado_bg": "FEF9E7",
    "moderado_font": "9A7D0A",
    "intenso_bg": "FDEDEC",
    "intenso_font": "B03A2E",
    "interdicao_bg": "F4ECF7",
    "interdicao_font": "6C3483",
    "bloqueio_bg": "FEF5E7",
    "bloqueio_font": "AF601A",
    "acidente_bg": "FADBD8",
    "acidente_font": "922B21",
    "erro_bg": "E5E7E9",
    "erro_font": "5D6D7E",
    "zebra_bg": "F8FAFC",
    "link_font": "1F5A99",
    "alta_bg": "D4EFDF",
    "alta_font": "145A32",
    "media_bg": "FCF3CF",
    "media_font": "7D6608",
    "baixa_bg": "FADBD8",
    "baixa_font": "922B21",
}

HEADER_FILL = PatternFill("solid", fgColor=CORES["header_bg"])
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color=CORES["header_font"])
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color=CORES["header_bg"])
TITLE_FILL = PatternFill("solid", fgColor=CORES["title_bg"])
DEFAULT_FONT = Font(name="Calibri", size=10)
LINK_FONT = Font(name="Calibri", size=10, color=CORES["link_font"], underline="single")
THIN_BORDER = Border(
    left=Side(style="thin", color="D5D8DC"),
    right=Side(style="thin", color="D5D8DC"),
    top=Side(style="thin", color="D5D8DC"),
    bottom=Side(style="thin", color="D5D8DC"),
)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
ZEBRA_FILL = PatternFill("solid", fgColor=CORES["zebra_bg"])

# ===== Style map (portado de excel_generator.py) =====

_STYLE_MAP = {
    "status": {
        "normal":   ("normal_bg",    "normal_font"),
        "moderado": ("moderado_bg",  "moderado_font"),
        "intenso":  ("intenso_bg",   "intenso_font"),
        "parado":   ("intenso_bg",   "intenso_font"),
    },
    "ocorrencia": {
        "colisao":         ("acidente_bg",    "acidente_font"),
        "acidente":        ("acidente_bg",    "acidente_font"),
        "bloqueio parcial": ("bloqueio_bg",   "bloqueio_font"),
        "interdicao":      ("interdicao_bg",  "interdicao_font"),
        "obras na pista":  ("moderado_bg",    "moderado_font"),
        "engarrafamento":  ("intenso_bg",     "intenso_font"),
    },
    "confianca": {
        "alta":  ("alta_bg",   "alta_font"),
        "media": ("media_bg",  "media_font"),
        "média": ("media_bg",  "media_font"),
        "baixa": ("baixa_bg",  "baixa_font"),
    },
}


def _norm(txt: str) -> str:
    base = unicodedata.normalize("NFKD", str(txt or ""))
    return "".join(ch for ch in base if not unicodedata.combining(ch)).strip().lower()


def _get_style(categoria: str, valor: str):
    """Retorna (fill, font) ou (None, None)."""
    key = _norm(valor)
    mapping = _STYLE_MAP.get(categoria, {})
    colors = mapping.get(key)
    if colors:
        bg_key, fg_key = colors
        return (
            PatternFill("solid", fgColor=CORES[bg_key]),
            Font(name="Calibri", size=10, bold=True, color=CORES[fg_key]),
        )
    if categoria == "status":
        return (
            PatternFill("solid", fgColor=CORES["erro_bg"]),
            Font(name="Calibri", size=10, bold=True, color=CORES["erro_font"]),
        )
    return None, None


# ===== Headers da planilha =====

_HEADERS_DETALHADO = [
    ("Rota",                   40),
    ("Status",                 12),
    ("Atraso (min)",           13),
    ("Confiança",              12),
    ("Incidente Principal",    22),
    ("Vel. Atual (km/h)",      16),
    ("Jam Factor",             12),
    ("Fontes",                 28),
    ("Atualizado em",          20),
    ("Link Waze",              14),
    ("Link Google Maps",       16),
]

_HEADERS_AGREGADO = [
    ("ID",                     10),
    ("Sigla",                  25),
    ("Nome",                   40),
    ("Trecho",                 35),
    ("Status",                 12),
    ("Ocorrência",             18),
    ("Relato",                 45),
    ("Atualização",            20),
    ("Confiança (%)",          15),
    ("Atraso (min)",           13),
    ("Distância (km)",         15),
]

TOTAL_COLS_DETALHADO = len(_HEADERS_DETALHADO)
TOTAL_COLS_AGREGADO = len(_HEADERS_AGREGADO)


def _aplicar_header(ws, headers: list, row: int = 1) -> None:
    for col, (header, width) in enumerate(headers, 1):
        c = ws.cell(row=row, column=col, value=header)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = THIN_BORDER
        ws.column_dimensions[get_column_letter(col)].width = width


def _aplicar_linha_base(ws, row: int, total_cols: int, zebra: bool = False) -> None:
    for col in range(1, total_cols + 1):
        c = ws.cell(row=row, column=col)
        c.font = DEFAULT_FONT
        c.border = THIN_BORDER
        c.alignment = CENTER
        if zebra:
            c.fill = ZEBRA_FILL


def gerar_excel(resultado: dict) -> bytes:
    """Gera relatório Excel para um ResultadoRota. Retorna bytes do .xlsx."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Consulta"

    # Título
    last_col_letter = get_column_letter(TOTAL_COLS_DETALHADO)
    ws.merge_cells(f"A1:{last_col_letter}1")
    t = ws["A1"]
    t.value = f"Projeto Zero — Consulta de Rota — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    t.font = TITLE_FONT
    t.fill = TITLE_FILL
    t.alignment = CENTER
    ws.row_dimensions[1].height = 26

    _aplicar_header(ws, headers=_HEADERS_DETALHADO, row=2)

    # Dados da rota (Detalhado)
    rota = f"{resultado.get('hub_origem', resultado.get('origem', ''))} → {resultado.get('hub_destino', resultado.get('destino', ''))}"
    status_val = resultado.get("status", "Sem dados")
    atraso = resultado.get("atraso_min", 0)
    confianca = resultado.get("confianca", "")
    inc_prin = resultado.get("incidente_principal", "")
    vel_atual = resultado.get("velocidade_atual_kmh", 0.0)
    jam = resultado.get("jam_factor_avg", 0.0)
    fontes = ", ".join(resultado.get("fontes", []))
    consultado = resultado.get("consultado_em", "")
    link_waze = resultado.get("link_waze", "")
    link_gmaps = resultado.get("link_gmaps", "")

    row = 3
    _aplicar_linha_base(ws, row, total_cols=TOTAL_COLS_DETALHADO, zebra=False)

    valores = [rota, status_val, atraso, confianca, inc_prin,
               vel_atual, jam, fontes, consultado, link_waze, link_gmaps]

    for col, val in enumerate(valores, 1):
        c = ws.cell(row=row, column=col, value=val)
        if col == 1:
            c.alignment = LEFT
        if col == 10 and link_waze:
            c.value = "Abrir Waze"
            c.hyperlink = link_waze
            c.font = LINK_FONT
        if col == 11 and link_gmaps:
            c.value = "Abrir Maps"
            c.hyperlink = link_gmaps
            c.font = LINK_FONT

    # Estilos por valor
    sf, sft = _get_style("status", status_val)
    ws.cell(row=row, column=2).fill = sf
    ws.cell(row=row, column=2).font = sft

    cf, cft = _get_style("confianca", confianca)
    if cf:
        ws.cell(row=row, column=4).fill = cf
        ws.cell(row=row, column=4).font = cft

    of_, oft = _get_style("ocorrencia", inc_prin)
    if of_:
        ws.cell(row=row, column=5).fill = of_
        ws.cell(row=row, column=5).font = oft

    ws.row_dimensions[row].height = 22

    # Aba incidentes HERE
    if resultado.get("incidentes"):
        _gerar_aba_incidentes(wb, resultado["incidentes"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _gerar_aba_incidentes(wb: Workbook, incidentes: list) -> None:
    ws = wb.create_sheet("Incidentes HERE")
    inc_headers = [
        ("#", 5), ("Categoria", 18), ("Severidade", 12), ("Rodovia", 16),
        ("Road Closed", 12), ("Descrição", 56), ("Início", 20), ("Fim", 20),
    ]
    for col, (h, w) in enumerate(inc_headers, 1):
        c = ws.cell(row=1, column=col, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = THIN_BORDER
        ws.column_dimensions[get_column_letter(col)].width = w

    for idx, inc in enumerate(incidentes, 1):
        row = idx + 1
        for col in range(1, len(inc_headers) + 1):
            c = ws.cell(row=row, column=col)
            c.font = DEFAULT_FONT
            c.border = THIN_BORDER
            c.alignment = CENTER
            if idx % 2 == 0:
                c.fill = ZEBRA_FILL

        vals = [
            idx,
            inc.get("categoria", ""),
            inc.get("severidade", ""),
            inc.get("rodovia_afetada", ""),
            "Sim" if inc.get("road_closed") else "Não",
            inc.get("descricao", ""),
            inc.get("inicio", ""),
            inc.get("fim", ""),
        ]
        for col, val in enumerate(vals, 1):
            c = ws.cell(row=row, column=col, value=val)
            if col == 6:
                c.alignment = LEFT

    ws.freeze_panes = "A2"


def gerar_csv(resultado: dict) -> str:
    """Gera relatório CSV simples para um ResultadoRota. Retorna string."""
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow([
        "Rota", "Status", "Atraso (min)", "Confiança", "Incidente Principal",
        "Vel. Atual (km/h)", "Jam Factor Avg", "Jam Factor Max",
        "Distância (km)", "Duração Normal (min)", "Duração Tráfego (min)",
        "Razão", "Fontes", "Atualizado em", "Link Waze", "Link Google Maps",
    ])

    rota = f"{resultado.get('hub_origem', resultado.get('origem', ''))} → {resultado.get('hub_destino', resultado.get('destino', ''))}"
    writer.writerow([
        rota,
        resultado.get("status", ""),
        resultado.get("atraso_min", 0),
        resultado.get("confianca", ""),
        resultado.get("incidente_principal", ""),
        resultado.get("velocidade_atual_kmh", ""),
        resultado.get("jam_factor_avg", ""),
        resultado.get("jam_factor_max", ""),
        resultado.get("distancia_km", ""),
        resultado.get("duracao_normal_min", ""),
        resultado.get("duracao_transito_min", ""),
        resultado.get("razao_transito", ""),
        ", ".join(resultado.get("fontes", [])),
        resultado.get("consultado_em", ""),
        resultado.get("link_waze", ""),
        resultado.get("link_gmaps", ""),
    ])

    if resultado.get("incidentes"):
        writer.writerow([])
        writer.writerow(["=== Incidentes HERE ==="])
        writer.writerow(["Categoria", "Severidade", "Rodovia", "Road Closed", "Descrição", "Início", "Fim"])
        for inc in resultado["incidentes"]:
            writer.writerow([
                inc.get("categoria", ""),
                inc.get("severidade", ""),
                inc.get("rodovia_afetada", ""),
                "Sim" if inc.get("road_closed") else "Não",
                inc.get("descricao", ""),
                inc.get("inicio", ""),
                inc.get("fim", ""),
            ])

    return buf.getvalue()


def gerar_excel_visao_geral(resultados: list) -> bytes:
    """Gera relatório Excel para a Visão Geral (múltiplas rotas). Retorna bytes do .xlsx."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Visão Geral"

    last_col_letter = get_column_letter(TOTAL_COLS_AGREGADO)
    ws.merge_cells(f"A1:{last_col_letter}1")
    t = ws["A1"]
    t.value = f"Projeto Zero — Visão Geral Analítica — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    t.font = TITLE_FONT
    t.fill = TITLE_FILL
    t.alignment = CENTER
    ws.row_dimensions[1].height = 26

    _aplicar_header(ws, headers=_HEADERS_AGREGADO, row=2)

    for idx, r in enumerate(resultados, 1):
        row = idx + 2
        rota_id = r.get("rota_id", "")
        sigla = r.get("sigla", "")
        nome = r.get("nome", "")
        trecho = r.get("trecho", "")
        status_val = r.get("status", "Sem dados")
        ocorrencia = r.get("ocorrencia", "")
        relato = r.get("relato", "")
        atualizado = r.get("hora_atualizacao", "")
        confianca_pct = r.get("confianca_pct", 0)
        atraso = r.get("atraso_min", 0)
        distancia = r.get("distancia_km", 0.0)

        _aplicar_linha_base(ws, row, total_cols=TOTAL_COLS_AGREGADO, zebra=(idx % 2 == 0))

        valores = [rota_id, sigla, nome, trecho, status_val,
                   ocorrencia, relato, atualizado, confianca_pct, atraso, distancia]

        for col, val in enumerate(valores, 1):
            c = ws.cell(row=row, column=col, value=val)
            if col in (3, 4, 7): # nome, trecho, relato
                c.alignment = LEFT

        # Estilos aplicados no status, confianca e ocorrencia igual consulta livre
        sf, sft = _get_style("status", status_val)
        ws.cell(row=row, column=5).fill = sf
        ws.cell(row=row, column=5).font = sft
        
        # Mapear confianca a partir da porcentagem
        if confianca_pct >= 90: str_conf = "alta"
        elif confianca_pct >= 50: str_conf = "media"
        else: str_conf = "baixa"
            
        cf, cft = _get_style("confianca", str_conf)
        if cf:
            ws.cell(row=row, column=9).fill = cf
            ws.cell(row=row, column=9).font = cft

        of_, oft = _get_style("ocorrencia", ocorrencia)
        if of_:
            ws.cell(row=row, column=6).fill = of_
            ws.cell(row=row, column=6).font = oft

        ws.row_dimensions[row].height = 22

    ws.freeze_panes = "A3"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def gerar_csv_visao_geral(resultados: list) -> str:
    """Gera relatório CSV para a Visão Geral (múltiplas rotas). Retorna string."""
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow([
        "ID", "Sigla", "Nome", "Trecho", "Status",
        "Ocorrência", "Relato", "Atualização", "Confiança (%)",
        "Atraso (min)", "Distância (km)"
    ])

    for r in resultados:
        writer.writerow([
            r.get("rota_id", ""),
            r.get("sigla", ""),
            r.get("nome", ""),
            r.get("trecho", ""),
            r.get("status", ""),
            r.get("ocorrencia", ""),
            r.get("relato", ""),
            r.get("hora_atualizacao", ""),
            r.get("confianca_pct", ""),
            r.get("atraso_min", ""),
            r.get("distancia_km", "")
        ])

    return buf.getvalue()
