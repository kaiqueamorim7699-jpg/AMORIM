# tools/__init__.py
import os
from datetime import datetime

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _nome_unico(prefixo: str, ext: str) -> str:
    """Gera nome único com timestamp pra não sobrescrever arquivos."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUTPUT_DIR, f"{prefixo}_{ts}.{ext}")


# ─────────────────────────────────────────────────────────
# EXCEL
# ─────────────────────────────────────────────────────────
def gerar_excel(dados: list[dict], nome_arquivo: str | None = None, titulo_aba: str = "Dados") -> str:
    """
    Gera um .xlsx formatado a partir de uma lista de dicionários.
    Cada dict vira uma linha. As chaves do primeiro dict viram cabeçalhos.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    caminho = os.path.join(OUTPUT_DIR, nome_arquivo) if nome_arquivo else _nome_unico("amorim_planilha", "xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = titulo_aba[:31]  # Excel limita a 31 chars

    if not dados:
        ws["A1"] = "Sem dados para exibir"
        wb.save(caminho)
        return caminho

    headers = list(dados[0].keys())

    # Estilo do cabeçalho
    header_fill = PatternFill(start_color="1A56DB", end_color="1A56DB", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    header_align = Alignment(horizontal="center", vertical="center")

    # Borda fina
    thin = Side(border_style="thin", color="D1D5DB")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Escreve cabeçalho
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=str(header))
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align
        cell.border = border

    # Escreve linhas (com zebra striping)
    zebra_fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
    for row_idx, item in enumerate(dados, start=2):
        for col_idx, header in enumerate(headers, start=1):
            value = item.get(header, "")
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = border
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if row_idx % 2 == 0:
                cell.fill = zebra_fill

    # Ajusta largura das colunas
    for col_idx, header in enumerate(headers, start=1):
        max_len = len(str(header))
        for row_idx in range(2, len(dados) + 2):
            v = ws.cell(row=row_idx, column=col_idx).value
            if v is not None:
                max_len = max(max_len, len(str(v)))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 3, 50)

    # Congela cabeçalho
    ws.freeze_panes = "A2"

    # Auto-filtro
    ws.auto_filter.ref = ws.dimensions

    wb.save(caminho)
    return caminho


# ─────────────────────────────────────────────────────────
# POWERPOINT
# ─────────────────────────────────────────────────────────
def gerar_pptx(titulo: str, slides: list[dict], nome_arquivo: str | None = None) -> str:
    """
    Gera um .pptx.
    slides: lista de {"titulo": str, "conteudo": list[str]}
    """
    from pptx import Presentation
    from pptx.util import Pt

    caminho = os.path.join(OUTPUT_DIR, nome_arquivo) if nome_arquivo else _nome_unico("amorim_apresentacao", "pptx")

    prs = Presentation()

    # Slide de capa
    slide_capa = prs.slides.add_slide(prs.slide_layouts[0])
    slide_capa.shapes.title.text = titulo
    if len(slide_capa.placeholders) > 1:
        slide_capa.placeholders[1].text = "Gerado por AMORIM A.I"

    # Slides de conteúdo
    for s in slides:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = s.get("titulo", "")
        conteudo = s.get("conteudo", [])

        body = slide.placeholders[1].text_frame
        body.clear()
        if conteudo:
            body.text = str(conteudo[0])
            for bullet in conteudo[1:]:
                p = body.add_paragraph()
                p.text = str(bullet)
                p.level = 0
                p.font.size = Pt(18)

    prs.save(caminho)
    return caminho


# ─────────────────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────────────────
def gerar_pdf(titulo: str, paragrafos: list[str], nome_arquivo: str | None = None) -> str:
    """
    Gera um PDF simples e limpo a partir de título + lista de parágrafos.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    caminho = os.path.join(OUTPUT_DIR, nome_arquivo) if nome_arquivo else _nome_unico("amorim_relatorio", "pdf")

    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=titulo,
        author="AMORIM A.I",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="AmorimTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=20,
        textColor="#1A56DB",
    ))
    styles.add(ParagraphStyle(
        name="AmorimBody",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
        spaceAfter=10,
    ))

    story = [Paragraph(titulo, styles["AmorimTitle"]), Spacer(1, 12)]

    for p in paragrafos:
        texto = str(p).replace("\n", "<br/>")
        story.append(Paragraph(texto, styles["AmorimBody"]))
        story.append(Spacer(1, 6))

    doc.build(story)
    return caminho


# ─────────────────────────────────────────────────────────
# IMAGEM (via Pollinations — grátis, sem chave)
# ─────────────────────────────────────────────────────────
def gerar_imagem(prompt: str, nome_arquivo: str | None = None, width: int = 1024, height: int = 1024) -> str:
    """
    Gera imagem a partir de descrição textual usando a API pública gratuita da Pollinations.
    """
    import requests
    from urllib.parse import quote

    caminho = os.path.join(OUTPUT_DIR, nome_arquivo) if nome_arquivo else _nome_unico("amorim_imagem", "png")

    # Prompt em inglês funciona melhor — mas a Pollinations aceita PT também
    prompt_encoded = quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width={width}&height={height}&nologo=true&model=flux"

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    with open(caminho, "wb") as f:
        f.write(response.content)

    return caminho


# ─────────────────────────────────────────────────────────
# Utilitário: lista os arquivos gerados
# ─────────────────────────────────────────────────────────
def listar_arquivos_gerados() -> list[str]:
    if not os.path.exists(OUTPUT_DIR):
        return []
    return [
        os.path.join(OUTPUT_DIR, f)
        for f in os.listdir(OUTPUT_DIR)
        if os.path.isfile(os.path.join(OUTPUT_DIR, f))
    ]