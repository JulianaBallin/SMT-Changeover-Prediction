"""Build the detailed A4 technical report for the SMT final project."""

# pylint: disable=line-too-long,too-many-lines,too-many-arguments
# pylint: disable=too-many-positional-arguments,too-many-locals
# pylint: disable=unused-argument,non-ascii-name,no-member,import-error

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from analise import (
    CORAL,
    CREAM,
    FEATURES,
    GRAY,
    INK,
    LIGHT_BLUE,
    LIGHT_GRAY,
    MINT,
    NUMERIC_FEATURES,
    TEAL,
    YELLOW,
    clean_data,
    read_raw_data,
    temporal_split,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_DIR / "assets"
CHART_DIR = PROJECT_DIR / "graficos"
OUTPUT_DIR = PROJECT_DIR / "outputs"
OUTPUT = PROJECT_DIR / "docs" / "relatorio" / "relatorio_tecnico_smt_em_tempo.pdf"
FONT_DIR = Path("/usr/share/fonts/truetype/noto")
CONTENT_WIDTH = A4[0] - 3.3 * cm


pdfmetrics.registerFont(TTFont("NotoSans", FONT_DIR / "NotoSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSans-Bold", FONT_DIR / "NotoSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("NotoSans-Italic", FONT_DIR / "NotoSans-Italic.ttf"))
pdfmetrics.registerFontFamily(
    "NotoSans",
    normal="NotoSans",
    bold="NotoSans-Bold",
    italic="NotoSans-Italic",
)


class ReportDocTemplate(SimpleDocTemplate):
    """Collect headings while ReportLab builds the table of contents."""

    def afterFlowable(self, flowable):
        """Register first and second level headings."""
        if not isinstance(flowable, Paragraph):
            return
        if flowable.style.name not in {"Heading1", "Heading2"}:
            return
        level = 0 if flowable.style.name == "Heading1" else 1
        text = flowable.getPlainText()
        key = f"section-{level}-{self.page}-{abs(hash(text))}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, key))


def hex_color(value: str):
    """Convert hexadecimal colors into ReportLab colors."""
    return colors.HexColor(value)


def draw_image_contain(canvas, path: Path, x, y, width, height) -> None:
    """Draw an image inside a fixed box without distortion."""
    with PILImage.open(path) as image:
        ratio = image.width / image.height
    box_ratio = width / height
    if ratio >= box_ratio:
        draw_width = width
        draw_height = width / ratio
        draw_x = x
        draw_y = y + (height - draw_height) / 2
    else:
        draw_height = height
        draw_width = height * ratio
        draw_x = x + (width - draw_width) / 2
        draw_y = y
    canvas.drawImage(
        str(path),
        draw_x,
        draw_y,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask="auto",
    )


def cover_page(canvas, _doc) -> None:
    """Draw the full report cover."""
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(hex_color(CREAM))
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(hex_color(TEAL))
    canvas.rect(0, 170, width, 485, fill=1, stroke=0)
    canvas.setFillColor(hex_color(MINT))
    canvas.rect(0, 0, width, 170, fill=1, stroke=0)
    canvas.setFillColor(hex_color(YELLOW))
    canvas.circle(25, height - 28, 42, fill=1, stroke=0)
    canvas.setFillColor(hex_color(CORAL))
    canvas.circle(width - 26, 184, 34, fill=1, stroke=0)

    draw_image_contain(canvas, ASSET_DIR / "logo-uea.png", 45, height - 105, 150, 62)
    draw_image_contain(canvas, ASSET_DIR / "logo-sialabs.png", width - 115, height - 115, 70, 80)
    draw_image_contain(canvas, ASSET_DIR / "logo-smt-em-tempo.png", width - 280, 500, 220, 170)

    canvas.setFont("NotoSans-Bold", 10)
    canvas.setFillColor(hex_color(YELLOW))
    canvas.drawString(54, 548, "RELATÓRIO TÉCNICO · TRABALHO FINAL")
    canvas.setFont("NotoSans-Bold", 34)
    canvas.setFillColor(colors.white)
    canvas.drawString(54, 492, "SMT em Tempo")
    canvas.setFont("NotoSans", 16)
    canvas.drawString(54, 457, "Previsão da duração da troca de produto")
    canvas.setStrokeColor(hex_color(YELLOW))
    canvas.setLineWidth(3)
    canvas.line(54, 432, 170, 432)
    canvas.setFont("NotoSans", 10.5)
    canvas.drawString(54, 402, "Machine Learning · Projeto 4")
    canvas.drawString(54, 384, "Dados de janeiro a agosto de 2026")

    canvas.setFillColor(hex_color(INK))
    canvas.setFont("NotoSans-Bold", 8)
    canvas.drawString(54, 135, "EQUIPE")
    canvas.setFont("NotoSans", 8.5)
    canvas.drawString(54, 118, "Juliana Ballin Lima")
    canvas.drawString(54, 103, "Fernanda de Oliveira da Costa")
    canvas.drawString(54, 88, "Pedro Henrique Oliveira Dias")
    canvas.setFont("NotoSans-Bold", 8)
    canvas.drawString(300, 135, "INSTITUIÇÃO")
    canvas.setFont("NotoSans", 8.5)
    canvas.drawString(300, 118, "Universidade do Estado do Amazonas")
    canvas.drawString(300, 103, "SiaLabs")
    canvas.setFont("NotoSans-Bold", 8)
    canvas.drawString(300, 77, "DATA")
    canvas.setFont("NotoSans", 8.5)
    canvas.drawString(300, 60, "26 de outubro de 2026 · Manaus, AM")
    canvas.restoreState()


def later_pages(canvas, doc) -> None:
    """Draw the header and footer used after the cover."""
    width, height = A4
    canvas.saveState()
    canvas.setStrokeColor(hex_color(MINT))
    canvas.setLineWidth(0.8)
    canvas.line(doc.leftMargin, height - 44, width - doc.rightMargin, height - 44)
    canvas.setFillColor(hex_color(TEAL))
    canvas.setFont("NotoSans-Bold", 7.5)
    canvas.drawString(doc.leftMargin, height - 36, "SMT em Tempo | Relatório técnico")
    canvas.setFillColor(hex_color(GRAY))
    canvas.setFont("NotoSans", 7)
    canvas.drawRightString(width - doc.rightMargin, height - 36, "Machine Learning · Projeto 4")
    canvas.setStrokeColor(hex_color(LIGHT_GRAY))
    canvas.line(doc.leftMargin, 37, width - doc.rightMargin, 37)
    canvas.setFillColor(hex_color(GRAY))
    canvas.drawString(doc.leftMargin, 25, "Universidade do Estado do Amazonas · SiaLabs")
    canvas.drawRightString(width - doc.rightMargin, 25, f"Página {doc.page}")
    canvas.restoreState()


def build_styles() -> dict[str, ParagraphStyle]:
    """Create report typography and paragraph styles."""
    sample = getSampleStyleSheet()
    return {
        "Body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName="NotoSans",
            fontSize=9,
            leading=13.3,
            textColor=hex_color(INK),
            alignment=TA_JUSTIFY,
            spaceAfter=7,
        ),
        "BodySmall": ParagraphStyle(
            "BodySmall",
            parent=sample["BodyText"],
            fontName="NotoSans",
            fontSize=7.5,
            leading=10.3,
            textColor=hex_color(INK),
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            parent=sample["Heading1"],
            fontName="NotoSans-Bold",
            fontSize=17,
            leading=21,
            textColor=hex_color(TEAL),
            spaceBefore=4,
            spaceAfter=10,
            keepWithNext=True,
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            parent=sample["Heading2"],
            fontName="NotoSans-Bold",
            fontSize=12.5,
            leading=16,
            textColor=hex_color(TEAL),
            spaceBefore=9,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "TOCTitle": ParagraphStyle(
            "TOCTitle",
            parent=sample["Heading1"],
            fontName="NotoSans-Bold",
            fontSize=20,
            textColor=hex_color(TEAL),
            spaceAfter=14,
        ),
        "FigureTitle": ParagraphStyle(
            "FigureTitle",
            parent=sample["BodyText"],
            fontName="NotoSans-Bold",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=hex_color(TEAL),
            spaceBefore=5,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "Caption": ParagraphStyle(
            "Caption",
            parent=sample["BodyText"],
            fontName="NotoSans-Italic",
            fontSize=7,
            leading=9.5,
            alignment=TA_CENTER,
            textColor=hex_color(GRAY),
            spaceBefore=4,
            spaceAfter=9,
        ),
        "Callout": ParagraphStyle(
            "Callout",
            parent=sample["BodyText"],
            fontName="NotoSans-Bold",
            fontSize=11.3,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.white,
        ),
        "CalloutDark": ParagraphStyle(
            "CalloutDark",
            parent=sample["BodyText"],
            fontName="NotoSans-Bold",
            fontSize=10.4,
            leading=15,
            alignment=TA_CENTER,
            textColor=hex_color(INK),
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=sample["BodyText"],
            fontName="NotoSans",
            fontSize=8.7,
            leading=12,
            leftIndent=12,
            firstLineIndent=-8,
            bulletIndent=2,
            alignment=TA_JUSTIFY,
            textColor=hex_color(INK),
            spaceAfter=4,
        ),
        "Table": ParagraphStyle(
            "Table",
            parent=sample["BodyText"],
            fontName="NotoSans",
            fontSize=7.2,
            leading=9.2,
            textColor=hex_color(INK),
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=sample["BodyText"],
            fontName="NotoSans-Bold",
            fontSize=7.1,
            leading=9,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
    }


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    """Create one escaped body paragraph."""
    return Paragraph(escape(text), style)


def rich_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    """Create one paragraph that may contain trusted inline markup."""
    return Paragraph(text, style)


def bullet(text: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    """Create one bullet item."""
    return Paragraph(f"• {escape(text)}", styles["Bullet"])


def callout(text: str, styles: dict[str, ParagraphStyle], color: str = TEAL, dark=False):
    """Create a colored statement card."""
    style = styles["CalloutDark"] if dark else styles["Callout"]
    table = Table([[Paragraph(escape(text), style)]], colWidths=[CONTENT_WIDTH])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), hex_color(color)),
                ("BOX", (0, 0), (-1, -1), 0, hex_color(color)),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def styled_table(
    rows: list[list[object]],
    styles: dict[str, ParagraphStyle],
    widths: list[float] | None = None,
    *,
    header: bool = True,
    font_size: float = 7.2,
) -> Table:
    """Create a table with wrapped paragraphs and alternating rows."""
    formatted = []
    for row_index, row in enumerate(rows):
        formatted_row = []
        for value in row:
            cell_style = styles["TableHeader"] if header and row_index == 0 else styles["Table"]
            if cell_style.fontSize != font_size and not (header and row_index == 0):
                cell_style = ParagraphStyle(
                    f"Table-{font_size}-{row_index}",
                    parent=styles["Table"],
                    fontSize=font_size,
                    leading=font_size + 2,
                )
            formatted_row.append(Paragraph(escape(str(value)), cell_style))
        formatted.append(formatted_row)
    table = Table(formatted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), hex_color(TEAL)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, hex_color(LIGHT_GRAY)),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_index in range(1 if header else 0, len(formatted)):
        background = CREAM if row_index % 2 else "#FFFFFF"
        commands.append(("BACKGROUND", (0, row_index), (-1, row_index), hex_color(background)))
    table.setStyle(TableStyle(commands))
    return table


def figure_block(
    title: str,
    path: Path,
    caption: str,
    styles: dict[str, ParagraphStyle],
    width: float,
    height: float,
):
    """Create a titled figure with a centered caption."""
    image = Image(str(path), width=width, height=height, kind="proportional")
    image.hAlign = "CENTER"
    return KeepTogether(
        [
            Paragraph(escape(title), styles["FigureTitle"]),
            image,
            Paragraph(escape(caption), styles["Caption"]),
        ]
    )


def metric_cards(summary: dict, styles: dict[str, ParagraphStyle]) -> Table:
    """Build the executive summary metric row."""
    data = [
        [
            rich_paragraph("<b>2.043</b><br/><font size='7'>trocas limpas</font>", styles["CalloutDark"]),
            rich_paragraph("<b>2,66 min</b><br/><font size='7'>MAE no teste</font>", styles["CalloutDark"]),
            rich_paragraph("<b>87,3%</b><br/><font size='7'>recall</font>", styles["CalloutDark"]),
            rich_paragraph("<b>89 de 102</b><br/><font size='7'>riscos encontrados</font>", styles["CalloutDark"]),
        ]
    ]
    table = Table(data, colWidths=[CONTENT_WIDTH / 4] * 4)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), hex_color(MINT)),
                ("BACKGROUND", (1, 0), (1, 0), hex_color(LIGHT_BLUE)),
                ("BACKGROUND", (2, 0), (2, 0), hex_color("#F8D2C8")),
                ("BACKGROUND", (3, 0), (3, 0), hex_color("#FBE8AD")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.white),
                ("INNERGRID", (0, 0), (-1, -1), 3, colors.white),
                ("TOPPADDING", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
            ]
        )
    )
    return table


def load_context():
    """Load saved results and recreate compact descriptive tables."""
    summary = json.loads((OUTPUT_DIR / "resumo_resultados.json").read_text(encoding="utf-8"))
    raw = read_raw_data()
    data, audit, suspicious, quality = clean_data(raw)
    split, _, _ = temporal_split(data)
    train = data.loc[split.eq("treino")].copy()
    regression_validation = pd.read_csv(OUTPUT_DIR / "N4_regressao_validacao.csv")
    regression_test = pd.read_csv(OUTPUT_DIR / "N4_regressao_teste.csv")
    classification_validation = pd.read_csv(OUTPUT_DIR / "N4_classificacao_validacao.csv")
    classification_test = pd.read_csv(OUTPUT_DIR / "N4_classificacao_teste.csv")

    group_summary = (
        train.groupby("muda_familia")["tempo_troca_min"]
        .agg(Registros="size", Média="mean", Mediana="median")
        .join(100 * train.groupby("muda_familia")["troca_demorada"].mean().rename("Acima de 42 (%)"))
        .reset_index()
    )
    correlations = (
        train[NUMERIC_FEATURES + ["tempo_troca_min"]]
        .corr(method="spearman")["tempo_troca_min"]
        .drop("tempo_troca_min")
        .sort_values(key=abs, ascending=False)
        .rename("Correlação de Spearman")
        .reset_index(name="Correlação de Spearman")
        .rename(columns={"index": "Entrada"})
    )
    return {
        "summary": summary,
        "raw": raw,
        "data": data,
        "audit": audit,
        "suspicious": suspicious,
        "quality": quality,
        "split": split,
        "train": train,
        "regression_validation": regression_validation,
        "regression_test": regression_test,
        "classification_validation": classification_validation,
        "classification_test": classification_test,
        "group_summary": group_summary,
        "correlations": correlations,
    }


def build_story(context: dict, styles: dict[str, ParagraphStyle]):
    """Create the report content flowables."""
    summary = context["summary"]
    audit = context["audit"]
    suspicious = context["suspicious"]
    quality = context["quality"]
    regression_validation = context["regression_validation"]
    regression_test = context["regression_test"]
    classification_validation = context["classification_validation"]
    classification_test = context["classification_test"]
    group_summary = context["group_summary"]
    correlations = context["correlations"]
    story = [Spacer(1, 700), PageBreak()]

    story.extend(
        [
            Paragraph("Sumário", styles["TOCTitle"]),
            Paragraph(
                "Este sumário é gerado a partir dos títulos do relatório.",
                styles["BodySmall"],
            ),
        ]
    )
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOCLevel1",
            fontName="NotoSans-Bold",
            fontSize=10,
            leading=18,
            leftIndent=0,
            textColor=hex_color(TEAL),
        ),
        ParagraphStyle(
            "TOCLevel2",
            fontName="NotoSans",
            fontSize=8.5,
            leading=15,
            leftIndent=18,
            textColor=hex_color(INK),
        ),
    ]
    story.extend([toc, PageBreak()])

    story.extend(
        [
            Paragraph("Resumo executivo", styles["Heading1"]),
            paragraph(
                "O projeto desenvolve um apoio à decisão para a troca de produto em uma linha SMT. Antes de a linha parar, o supervisor precisa escolher quais trocas devem receber ajuda adicional. A análise usa oito informações já disponíveis nesse momento para estimar a duração em minutos e o risco de ultrapassar 42 minutos.",
                styles["Body"],
            ),
            metric_cards(summary, styles),
            Spacer(1, 9),
            callout(
                "A árvore de regressão reduziu o MAE em 67,4% frente à mediana. O classificador encontrou 89 de 102 trocas demoradas no teste.",
                styles,
            ),
            Spacer(1, 9),
            paragraph(
                "A base didática contém 2.057 linhas de janeiro a agosto de 2026. Após remover 14 duplicatas exatas, permaneceram 2.043 trocas. A divisão respeitou o tempo: 1.236 casos para treino, 404 para validação e 403 para teste. O teste foi usado uma única vez, depois da escolha das profundidades das árvores.",
                styles["Body"],
            ),
            paragraph(
                "A principal recomendação é usar a probabilidade prevista como fila de prioridade, sem automatizar a alocação de apoio. O supervisor continua responsável pela decisão e acompanha trocas perdidas, falsos alarmes e mudanças no processo.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("1. Problema, objetivo e perguntas", styles["Heading1"]),
            Paragraph("1.1 Contexto operacional", styles["Heading2"]),
            paragraph(
                "Uma linha SMT posiciona componentes eletrônicos sobre placas de circuito. Cada produto utiliza um conjunto próprio de alimentadores, que sustentam os rolos de componentes. Quando a fábrica muda de produto, o operador retira parte do conjunto anterior, instala o novo, carrega o programa e confere a primeira placa. Durante esse intervalo, a linha permanece parada.",
                styles["Body"],
            ),
            paragraph(
                "Algumas trocas terminam em cerca de vinte minutos e outras ultrapassam uma hora. Como a ajuda adicional é limitada, o problema não consiste apenas em estimar tempo. Também é necessário priorizar os casos em que o apoio tem maior chance de evitar uma parada longa.",
                styles["Body"],
            ),
            Paragraph("1.2 Objetivo", styles["Heading2"]),
            paragraph(
                "Construir e avaliar modelos capazes de estimar a duração da troca e identificar, antes de seu início, os casos com maior risco de ultrapassar 42 minutos.",
                styles["Body"],
            ),
            Paragraph("1.3 Perguntas", styles["Heading2"]),
            bullet("Quais problemas de registro existem e como cada tratamento pode ser conferido?", styles),
            bullet("Como o tempo varia com preparação do kit, alimentadores e mudança de família?", styles),
            bullet("A regressão erra menos que uma referência simples?", styles),
            bullet("Quantos riscos o classificador encontra, perde e sinaliza incorretamente?", styles),
            bullet("Que decisão os resultados apoiam e quais conclusões permanecem fora do alcance da base?", styles),
            Spacer(1, 7),
            callout(
                "Pergunta central: antes de começar a troca, quais casos precisam de mais atenção?",
                styles,
                color=CORAL,
            ),
            PageBreak(),
        ]
    )

    feature_rows = [["Campo", "Papel", "Disponibilidade"]]
    feature_descriptions = {
        "alimentadores_a_trocar": "quantidade de alimentadores",
        "kit_preparado_pct": "percentual do kit separado",
        "experiencia_operador_meses": "experiência do operador",
        "componentes_novos": "componentes novos para a linha",
        "tamanho_lote_placas": "tamanho do lote seguinte",
        "linha_smt": "linha produtiva",
        "muda_familia": "mudança de família",
        "turno": "turno programado",
    }
    for feature in FEATURES:
        feature_rows.append([feature, feature_descriptions[feature], "antes da troca"])
    feature_rows.extend(
        [
            ["tempo_troca_min", "alvo da regressão", "depois"],
            ["troca_demorada", "alvo da classificação", "depois"],
            ["atraso_no_plano_min", "resultado posterior, excluído", "depois"],
        ]
    )
    story.extend(
        [
            Paragraph("2. Dataset e método", styles["Heading1"]),
            Paragraph("2.1 Escopo e contrato dos dados", styles["Heading2"]),
            paragraph(
                "A base sintética reúne trocas entre 5 de janeiro e 28 de agosto de 2026. Cada linha representa uma troca. O contrato separa informações disponíveis antes do evento das respostas conhecidas somente depois. Essa separação evita vazamento, situação em que o modelo recebe durante o treino uma informação que não existiria no momento real da previsão.",
                styles["Body"],
            ),
            styled_table(
                feature_rows,
                styles,
                widths=[5.0 * cm, 7.2 * cm, 3.0 * cm],
                font_size=6.7,
            ),
            Paragraph("2.2 Sequência analítica", styles["Heading2"]),
            callout(
                "observar  →  corrigir  →  conferir  →  dividir no tempo  →  treinar  →  validar  →  testar",
                styles,
                color=MINT,
                dark=True,
            ),
            Spacer(1, 8),
            paragraph(
                "A exploração utiliza somente o treino. A validação escolhe a profundidade das árvores. O teste mede uma única vez o desempenho final. A preparação fica dentro de um pipeline, o que garante que medianas e categorias sejam aprendidas apenas com a parcela de treinamento de cada etapa.",
                styles["Body"],
            ),
            Paragraph("2.3 Divisão temporal", styles["Heading2"]),
            styled_table(
                [
                    ["Divisão", "Registros", "Período", "Uso"],
                    ["Treino", "1.236", "05/01 a 27/05", "aprender parâmetros"],
                    ["Validação", "404", "28/05 a 15/07", "escolher profundidade"],
                    ["Teste", "403", "16/07 a 28/08", "avaliação final"],
                ],
                styles,
                widths=[3.0 * cm, 2.5 * cm, 4.0 * cm, 5.7 * cm],
            ),
            PageBreak(),
        ]
    )

    audit_summary = (
        audit.query("Quantidade > 0")
        .groupby("Etapa", as_index=False)["Quantidade"]
        .sum()
        .sort_values("Quantidade", ascending=False)
    )
    audit_rows = [["Etapa", "Ocorrências"]] + [
        [row["Etapa"], int(row["Quantidade"])] for _, row in audit_summary.iterrows()
    ]
    quality_rows = [["Entrada", "Ausentes", "Ausentes (%)"]] + [
        [index, int(row["Ausentes"]), f"{row['Ausentes (%)']:.2f}%"]
        for index, row in quality.iterrows()
    ]
    suspect_counts = suspicious.groupby("coluna").size().sort_values(ascending=False)
    suspect_rows = [["Campo", "Medidas fora do critério"]] + [
        [index, int(value)] for index, value in suspect_counts.items()
    ]
    story.extend(
        [
            Paragraph("3. Limpeza, validação e rastreabilidade", styles["Heading1"]),
            paragraph(
                "O tratamento segue o padrão apresentado nas aulas: observar, decidir, corrigir e conferir. Nenhuma troca foi removida apenas por conter uma entrada ausente. Somente cópias exatas foram excluídas. Códigos de ausência e medidas incompatíveis com os critérios didáticos foram marcados como desconhecidos no campo afetado.",
                styles["Body"],
            ),
            styled_table(audit_rows, styles, widths=[10.8 * cm, 4.4 * cm]),
            Paragraph("3.1 Medidas suspeitas", styles["Heading2"]),
            paragraph(
                "As faixas do exercício foram usadas como referência externa. Valores negativos, porcentagens acima de 100 e escalas incompatíveis não foram corrigidos por adivinhação. Eles permaneceram registrados na auditoria e passaram a ausentes para o modelo.",
                styles["Body"],
            ),
            styled_table(suspect_rows, styles, widths=[10.8 * cm, 4.4 * cm]),
            Paragraph("3.2 Ausências após a limpeza", styles["Heading2"]),
            styled_table(quality_rows, styles, widths=[8.7 * cm, 3.0 * cm, 3.5 * cm]),
            figure_block(
                "Figura 1 · Ausências preservadas na base limpa",
                CHART_DIR / "08_qualidade_ausencias.png",
                "As entradas ausentes são preenchidas pela mediana dentro do pipeline. Os alvos permanecem observados.",
                styles,
                width=15.1 * cm,
                height=8.2 * cm,
            ),
            PageBreak(),
        ]
    )

    group_rows = [["Muda de família?", "Registros", "Média", "Mediana", "Acima de 42"]]
    for _, row in group_summary.iterrows():
        group_rows.append(
            [
                row["muda_familia"],
                int(row["Registros"]),
                f"{row['Média']:.1f} min",
                f"{row['Mediana']:.1f} min",
                f"{row['Acima de 42 (%)']:.1f}%",
            ]
        )
    correlation_rows = [["Entrada", "Correlação com o tempo"]] + [
        [row["Entrada"], f"{row['Correlação de Spearman']:.3f}"]
        for _, row in correlations.iterrows()
    ]
    story.extend(
        [
            Paragraph("4. Exploração dos dados de treino", styles["Heading1"]),
            Paragraph("4.1 Distribuição do alvo", styles["Heading2"]),
            paragraph(
                "No conjunto completo, o tempo médio é 35,9 minutos e a mediana é 34,7 minutos. A classe demorada representa 27,2% das trocas. O limiar de 42 minutos define o problema operacional e não foi usado como critério de limpeza.",
                styles["Body"],
            ),
            figure_block(
                "Figura 2 · Distribuição do tempo de troca no treino",
                CHART_DIR / "01_distribuicao_tempo.png",
                "A linha tracejada marca 42 minutos. Os casos acima dela formam a classe positiva.",
                styles,
                width=15.3 * cm,
                height=8.2 * cm,
            ),
            Paragraph("4.2 Relações com a duração", styles["Heading2"]),
            figure_block(
                "Figura 3 · Preparação do kit e alimentadores",
                CHART_DIR / "02_relacoes_principais.png",
                "No treino, maior preparação do kit aparece associada a menor duração. Mais alimentadores aparecem associados a trocas mais longas.",
                styles,
                width=16.0 * cm,
                height=6.6 * cm,
            ),
            styled_table(correlation_rows, styles, widths=[10.8 * cm, 4.4 * cm]),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("4.3 Mudança de família e preparação", styles["Heading2"]),
            styled_table(
                group_rows,
                styles,
                widths=[4.2 * cm, 2.5 * cm, 2.8 * cm, 2.8 * cm, 3.0 * cm],
            ),
            Spacer(1, 8),
            figure_block(
                "Figura 4 · Risco por faixa de preparação do kit",
                CHART_DIR / "03_risco_por_kit_e_familia.png",
                "As porcentagens comparam grupos de tamanhos diferentes. A queda do risco ocorre nos dois tipos de troca, mas não demonstra causalidade.",
                styles,
                width=15.6 * cm,
                height=8.1 * cm,
            ),
            callout(
                "A exploração aponta kit e alimentadores como sinais úteis. A interpretação continua associativa, pois a base não é um experimento controlado.",
                styles,
                color=CORAL,
            ),
            Paragraph("4.4 O que ficou ausente", styles["Heading2"]),
            paragraph(
                "A base não identifica detalhes como número de pessoas apoiando a troca, experiência específica com o produto, falhas de material, distância de movimentação ou interrupções durante o setup. A ausência dessas informações limita a explicação dos erros restantes e impede atribuir causa à preparação do kit.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    regression_validation_rows = [["Modelo", "MAE", "RMSE", "R²"]]
    for _, row in regression_validation.head(7).iterrows():
        regression_validation_rows.append(
            [row["Modelo"], f"{row['MAE']:.3f}", f"{row['RMSE']:.3f}", f"{row['R2']:.3f}"]
        )
    regression_test_rows = [["Modelo", "MAE", "RMSE", "R²"]]
    for _, row in regression_test.iterrows():
        regression_test_rows.append(
            [row["Modelo"], f"{row['MAE']:.3f}", f"{row['RMSE']:.3f}", f"{row['R2']:.3f}"]
        )
    story.extend(
        [
            Paragraph("5. Regressão: previsão da duração", styles["Heading1"]),
            Paragraph("5.1 Modelos comparados", styles["Heading2"]),
            paragraph(
                "A referência simples devolve a mediana do treino para qualquer troca. A regressão linear representa uma relação aditiva. A árvore de regressão divide o espaço em grupos e permite relações não lineares. Profundidades de 2 a 10 foram comparadas na validação, sempre com pelo menos 10 registros por folha.",
                styles["Body"],
            ),
            paragraph(
                "O MAE mede quantos minutos, em média, separam a previsão do valor observado. Ele preserva a unidade do problema e permite uma leitura direta pelo supervisor.",
                styles["Body"],
            ),
            styled_table(
                regression_validation_rows,
                styles,
                widths=[7.2 * cm, 2.6 * cm, 2.7 * cm, 2.7 * cm],
            ),
            Paragraph("5.2 Resultado final no teste", styles["Heading2"]),
            styled_table(
                regression_test_rows,
                styles,
                widths=[7.2 * cm, 2.6 * cm, 2.7 * cm, 2.7 * cm],
            ),
            figure_block(
                "Figura 5 · Comparação do MAE no teste",
                CHART_DIR / "04_comparacao_regressao.png",
                "A árvore de profundidade 7 alcança MAE de 2,66 minutos. A referência apresenta 8,14 minutos.",
                styles,
                width=15.6 * cm,
                height=8.0 * cm,
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("5.3 Discussão do erro", styles["Heading2"]),
            figure_block(
                "Figura 6 · Tempo previsto e observado",
                CHART_DIR / "05_previsto_vs_observado.png",
                "A linha tracejada representa previsão perfeita. A proximidade dos pontos indica bom ajuste, sem eliminar erros individuais.",
                styles,
                width=12.2 * cm,
                height=10.7 * cm,
            ),
            paragraph(
                "O MAE caiu 67,4% em relação à referência. O R² de 0,884 indica que o modelo acompanha grande parte da variação no período de teste. A regressão linear também supera a referência, com MAE de 3,03 minutos, mas a árvore captura relações que a forma linear não representa tão bem.",
                styles["Body"],
            ),
            paragraph(
                "O resultado não garante o mesmo erro em novos produtos, equipes ou regras de preparação. O monitoramento deve comparar continuamente previsão e tempo observado, com atenção a mudanças na distribuição das entradas.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    classification_validation_rows = [["Modelo", "Precisão", "Recall", "F1", "AP"]]
    for _, row in classification_validation.head(7).iterrows():
        classification_validation_rows.append(
            [
                row["Modelo"],
                f"{100 * row['Precisão']:.1f}%",
                f"{100 * row['Recall']:.1f}%",
                f"{100 * row['F1']:.1f}%",
                f"{row['AP']:.3f}",
            ]
        )
    classification_test_rows = [["Modelo", "Precisão", "Recall", "F1", "FP", "FN", "VP"]]
    for _, row in classification_test.iterrows():
        classification_test_rows.append(
            [
                row["Modelo"],
                f"{100 * row['Precisão']:.1f}%",
                f"{100 * row['Recall']:.1f}%",
                f"{100 * row['F1']:.1f}%",
                int(row["FP"]),
                int(row["FN"]),
                int(row["VP"]),
            ]
        )
    story.extend(
        [
            Paragraph("6. Classificação: risco acima de 42 minutos", styles["Heading1"]),
            Paragraph("6.1 Critério de escolha", styles["Heading2"]),
            paragraph(
                "A referência prevê sempre a classe majoritária. A regressão logística e as árvores usam pesos balanceados para reduzir o efeito da diferença entre as classes. A profundidade da árvore foi escolhida pelo maior F1 na validação, com recall como segundo critério. Essa escolha equilibra dois custos: deixar uma troca demorada sem apoio e consumir atenção com um falso alarme.",
                styles["Body"],
            ),
            styled_table(
                classification_validation_rows,
                styles,
                widths=[6.4 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm],
                font_size=6.9,
            ),
            Paragraph("6.2 Resultado final", styles["Heading2"]),
            styled_table(
                classification_test_rows,
                styles,
                widths=[5.4 * cm, 1.9 * cm, 1.9 * cm, 1.9 * cm, 1.4 * cm, 1.4 * cm, 1.4 * cm],
                font_size=6.6,
            ),
            figure_block(
                "Figura 7 · Matriz de confusão no teste",
                CHART_DIR / "06_matriz_confusao.png",
                "O modelo encontra 89 das 102 trocas demoradas. Também sinaliza 31 casos que terminam em até 42 minutos.",
                styles,
                width=12.4 * cm,
                height=10.0 * cm,
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("6.3 Interpretação operacional", styles["Heading2"]),
            callout(
                "Em cada 102 trocas demoradas do teste, 89 foram encontradas, 13 ficaram sem alerta e 31 alertas recaíram sobre trocas não demoradas.",
                styles,
            ),
            Spacer(1, 9),
            paragraph(
                "A precisão de 74,2% significa que aproximadamente três de cada quatro alertas correspondem a uma troca realmente demorada. O recall de 87,3% mostra que a maior parte dos casos críticos é capturada. A referência majoritária obtém 74,7% de acurácia apenas por prever todos os casos como não demorados, mas seu recall é zero. Isso demonstra por que acurácia isolada não responde à pergunta operacional.",
                styles["Body"],
            ),
            figure_block(
                "Figura 8 · Importância das características na regressão",
                CHART_DIR / "07_importancia_caracteristicas.png",
                "Kit preparado e alimentadores concentram a importância da árvore. Importância não equivale a causalidade.",
                styles,
                width=15.0 * cm,
                height=8.7 * cm,
            ),
            paragraph(
                "O classificador produz probabilidades, o que permite ordenar casos mesmo quando o limite de 50% não for adotado. A capacidade disponível pode orientar quantos casos receberão atenção. Qualquer alteração do limiar deve ser avaliada em dados posteriores, pois reduzir perdas costuma aumentar falsos alarmes.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("7. Decisão apoiada", styles["Heading1"]),
            Paragraph("7.1 Proposta de uso", styles["Heading2"]),
            paragraph(
                "Antes de cada troca, o pipeline recebe as oito entradas disponíveis e calcula dois resultados: duração prevista e probabilidade de ultrapassar 42 minutos. A lista do turno pode ser ordenada pela probabilidade. O supervisor utiliza a previsão junto com restrições de equipe, material e sequência produtiva.",
                styles["Body"],
            ),
            styled_table(
                [
                    ["Etapa", "Ação", "Responsável"],
                    ["1", "registrar as entradas antes da troca", "sistema e operação"],
                    ["2", "calcular duração e probabilidade", "pipeline"],
                    ["3", "ordenar os maiores riscos", "painel"],
                    ["4", "alocar apoio considerando o contexto", "supervisor"],
                    ["5", "registrar tempo observado e revisar erros", "equipe de melhoria"],
                ],
                styles,
                widths=[1.6 * cm, 9.2 * cm, 4.4 * cm],
            ),
            Paragraph("7.2 Indicadores de acompanhamento", styles["Heading2"]),
            bullet("MAE mensal da duração prevista, em minutos.", styles),
            bullet("Recall das trocas acima de 42 minutos.", styles),
            bullet("Precisão dos alertas e quantidade de falsos alarmes.", styles),
            bullet("Distribuição das entradas por período, linha e turno.", styles),
            bullet("Tempo economizado e utilização efetiva da equipe de apoio.", styles),
            Paragraph("7.3 Limites da decisão", styles["Heading2"]),
            paragraph(
                "A previsão não determina automaticamente quem recebe apoio e não deve ser interpretada como avaliação de desempenho individual do operador. A experiência é uma característica operacional, mas o modelo não conhece todas as condições que influenciam a troca. O uso responsável mantém revisão humana, transparência dos critérios e registro das decisões.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("8. Limitações e riscos", styles["Heading1"]),
            styled_table(
                [
                    ["Limitação", "Consequência", "Tratamento proposto"],
                    ["dados sintéticos", "desempenho pode não se repetir", "piloto com dados reais"],
                    ["relações observacionais", "não há prova causal", "testes controlados e conhecimento do processo"],
                    ["entradas incompletas", "parte do erro fica sem explicação", "melhorar registro sem preencher por adivinhação"],
                    ["mudança de processo", "modelo pode envelhecer", "monitorar distribuição e métricas"],
                    ["falsos negativos", "troca crítica sem alerta", "revisar limiar e capacidade"],
                    ["falsos positivos", "atenção pode ser desperdiçada", "ordenar por risco e acompanhar precisão"],
                ],
                styles,
                widths=[4.0 * cm, 5.2 * cm, 6.0 * cm],
                font_size=6.8,
            ),
            Paragraph("8.1 O que os dados não permitem concluir", styles["Heading2"]),
            bullet("Que preparar o kit causa sozinho a redução do tempo.", styles),
            bullet("Que a mesma árvore terá o mesmo desempenho em uma linha real.", styles),
            bullet("Que um alerta identifica culpa ou falha individual.", styles),
            bullet("Que o limite de 42 minutos é universal para outros processos.", styles),
            Paragraph("8.2 Validação antes do uso real", styles["Heading2"]),
            paragraph(
                "Um piloto deve manter o processo atual enquanto registra previsões silenciosas. Depois de acumular um período representativo, a equipe compara erros por linha, turno, família de produto e disponibilidade de apoio. Somente então deve decidir se a previsão entra no fluxo operacional.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("9. Pontos de aprendizado", styles["Heading1"]),
            Paragraph("9.1 Dados antes do algoritmo", styles["Heading2"]),
            paragraph(
                "A limpeza não foi uma etapa automática. Duplicatas, códigos de ausência, grafias e medidas impossíveis exigiram decisões diferentes. Preservar a linha e marcar somente o campo problemático conservou informação útil para as demais análises.",
                styles["Body"],
            ),
            Paragraph("9.2 Momento da informação", styles["Heading2"]),
            paragraph(
                "A coluna de atraso no plano parece muito útil, mas só existe depois da troca. Incluí-la produziria vazamento e uma avaliação irreal. Definir quando cada campo se torna disponível foi tão importante quanto escolher o algoritmo.",
                styles["Body"],
            ),
            Paragraph("9.3 Referência simples", styles["Heading2"]),
            paragraph(
                "A mediana e a classe majoritária funcionaram como réguas. A árvore de regressão mostrou valor por reduzir o MAE. Na classificação, a referência revelou a armadilha da acurácia: prever todos os casos como comuns parece razoável no agregado, mas não encontra nenhum problema.",
                styles["Body"],
            ),
            Paragraph("9.4 Métrica ligada à decisão", styles["Heading2"]),
            paragraph(
                "MAE foi escolhido por ser lido em minutos. Na classificação, recall e precisão representam custos operacionais diferentes. O F1 ajudou a selecionar um equilíbrio, mas a decisão final sobre limiar depende da capacidade real de apoio.",
                styles["Body"],
            ),
            Paragraph("9.5 Reprodutibilidade", styles["Heading2"]),
            paragraph(
                "Notebook, script de análise, arquivos de auditoria, previsões e documentos usam o mesmo resultado salvo. Essa estrutura reduz divergências entre o que foi calculado, apresentado e discutido.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("10. Conclusão", styles["Heading1"]),
            paragraph(
                "Os modelos superaram referências simples no período de teste e demonstraram que as informações disponíveis antes da troca podem apoiar a priorização de recursos. A árvore de regressão apresentou MAE de 2,66 minutos, enquanto a mediana registrou 8,14 minutos. A árvore de classificação encontrou 89 das 102 trocas acima de 42 minutos, com 31 falsos alarmes.",
                styles["Body"],
            ),
            paragraph(
                "A recomendação é usar a probabilidade como ordenação de risco, mantendo decisão humana e acompanhamento das métricas. Os resultados não demonstram causalidade e não autorizam uso direto em uma fábrica real sem piloto. O principal ganho do trabalho foi conectar qualidade dos dados, prevenção de vazamento, comparação justa e métrica operacional numa análise reproduzível.",
                styles["Body"],
            ),
            callout("Prever cedo para apoiar melhor.", styles, color=TEAL),
            Spacer(1, 14),
            Paragraph("Referências", styles["Heading1"]),
            paragraph(
                "JAMES, Gareth et al. An Introduction to Statistical Learning: with Applications in R. 2. ed. New York: Springer, 2021.",
                styles["BodySmall"],
            ),
            paragraph(
                "UNIVERSIDADE DO ESTADO DO AMAZONAS. Módulo 8: Machine Learning. Apostilas, slides, notebooks e trabalho final. Manaus: UEA, 2026.",
                styles["BodySmall"],
            ),
            paragraph(
                "SCIKIT-LEARN DEVELOPERS. Scikit-learn User Guide. Versão 1.8.0, 2026.",
                styles["BodySmall"],
            ),
            Spacer(1, 10),
            HRFlowable(width="100%", thickness=0.6, color=hex_color(MINT)),
            Spacer(1, 8),
            Paragraph("Apêndice A · Arquivos reproduzíveis", styles["Heading2"]),
            styled_table(
                [
                    ["Arquivo", "Finalidade"],
                    ["smt_changeover_prediction.ipynb", "análise executada com explicações"],
                    ["fontes/analise.py", "limpeza, treino, avaliação e gráficos"],
                    ["dataset/N4_TrocaSMT_limpo.csv", "base limpa sem imputação dos alvos"],
                    ["outputs/N4_previsoes_teste.csv", "previsões finais e probabilidades"],
                    ["docs/apresentacao", "slides em PPTX e PDF"],
                    ["docs/relatorio", "relatório técnico em PDF"],
                ],
                styles,
                widths=[7.2 * cm, 8.0 * cm],
            ),
        ]
    )
    return story


def build_report() -> None:
    """Create the final multi-page PDF report."""
    context = load_context()
    styles = build_styles()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = ReportDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=1.65 * cm,
        leftMargin=1.65 * cm,
        topMargin=1.75 * cm,
        bottomMargin=1.55 * cm,
        title="SMT em Tempo: relatório técnico",
        author="Juliana Ballin Lima; Fernanda de Oliveira da Costa; Pedro Henrique Oliveira Dias",
        subject="Previsão da duração da troca de produto na linha SMT",
    )
    frame = Frame(
        document.leftMargin,
        document.bottomMargin,
        document.width,
        document.height,
        id="normal",
    )
    document.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[frame], onPage=cover_page),
            PageTemplate(id="body", frames=[frame], onPage=later_pages),
        ]
    )
    document.handle_nextPageTemplate("body")
    document.multiBuild(build_story(context, styles))
    print(f"Relatório criado em: {OUTPUT}")


if __name__ == "__main__":
    build_report()
