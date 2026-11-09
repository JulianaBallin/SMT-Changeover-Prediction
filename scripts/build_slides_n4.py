"""Build the short (5-minute) N4 presentation from the notebook results."""

# pylint: disable=line-too-long,too-many-locals,import-error,wrong-import-position

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_slides as bs  # noqa: E402
from smt_changeover.analysis import (  # noqa: E402
    BLUE,
    CORAL,
    CREAM,
    GREEN,
    INK,
    MINT,
    TEAL,
    YELLOW,
)

PROJECT_DIR = Path(__file__).resolve().parents[1]
DELIVERY_DIR = PROJECT_DIR / "entrega_N4"
RESULTS_DIR = DELIVERY_DIR / "resultados_N4"
OUTPUT = DELIVERY_DIR / "N4_apresentacao.pptx"
TOTAL = 6


def pt(value: float, digits: int = 1) -> str:
    """Format a number with a decimal comma."""
    return f"{value:.{digits}f}".replace(".", ",")


def load_results() -> tuple[dict, dict, pd.DataFrame]:
    """Read the notebook results saved as JSON and the clean base."""
    regression = json.loads((RESULTS_DIR / "N4_regressao.json").read_text(encoding="utf-8"))
    classification = json.loads((RESULTS_DIR / "N4_classificacao.json").read_text(encoding="utf-8"))
    base = pd.read_csv(DELIVERY_DIR / "N4_limpo.csv")
    if not classification.get("teste_aberto"):
        raise RuntimeError("Execute o notebook de classificação até a seção 2.8.")
    return regression, classification, base


def new_slide(prs: Presentation, number: str, title: str, current: int, *, dark: bool = False):
    """Create a slide with the project header and footer."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bs.set_background(slide, TEAL if dark else CREAM)
    bs.add_doodles(slide, current, dark=dark)
    color = CREAM if dark else TEAL
    bs.add_header(slide, number, title, color=color)
    bs.add_footer(slide, current, color=color)
    return slide


def slide_problem(prs: Presentation, base: pd.DataFrame) -> None:
    """Slide 2: what was predicted and which decision it supports."""
    slide = new_slide(prs, "01", "O problema", 2)
    rate = 100 * base["troca_demorada"].mean()
    bs.add_metric(slide, f"{len(base):,}".replace(",", "."), "trocas de produto", 0.66, 1.18, 2.80, CORAL)
    bs.add_metric(slide, "jan a ago", "período de 2026", 3.66, 1.18, 2.80, BLUE)
    bs.add_metric(slide, f"{pt(rate)}%", "acima de 42 min", 6.66, 1.18, 2.80, GREEN)
    bs.add_metric(slide, "8", "entradas conhecidas antes", 9.66, 1.18, 3.0, YELLOW)

    bs.add_card(slide, 0.66, 2.65, 5.95, 2.45, color="#C7E9F8", line="#A9D8E8")
    bs.add_text(slide, "REGRESSÃO · quanto?", 0.90, 2.82, 5.5, 0.32, size=12, color=BLUE, bold=True)
    bs.add_text(slide, "Quantos minutos a troca vai levar?", 0.90, 3.20, 5.5, 0.85, size=21, color=INK, bold=True)
    bs.add_text(slide, "Resposta: tempo_troca_min, em minutos", 0.90, 4.30, 5.5, 0.50, size=13, color=TEAL)

    bs.add_card(slide, 6.72, 2.65, 5.95, 2.45, color="#F8D2C8", line="#F0B7A9")
    bs.add_text(slide, "CLASSIFICAÇÃO · sim ou não?", 6.96, 2.82, 5.5, 0.32, size=12, color=CORAL, bold=True)
    bs.add_text(slide, "A troca vai passar de 42 minutos?", 6.96, 3.20, 5.5, 0.85, size=21, color=INK, bold=True)
    bs.add_text(slide, "Resposta: troca_demorada (1 = sim, 0 = não)", 6.96, 4.30, 5.5, 0.50, size=13, color=TEAL)

    bs.add_card(slide, 0.66, 5.35, 12.01, 1.15, color=TEAL)
    bs.add_text(
        slide,
        "Decisão apoiada: escolher onde colocar a ajuda extra antes de a linha parar.",
        0.90,
        5.55,
        11.5,
        0.75,
        size=19,
        color=CREAM,
        bold=True,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
    )


def slide_regression(prs: Presentation, reg: dict) -> None:
    """Slide 3: regression result against validation, reference and goal."""
    slide = new_slide(prs, "02", "Regressão: quantos minutos?", 3)
    depth = reg["arvore_profundidade_escolhida"]
    bs.add_metric(slide, f"{pt(reg['mae_teste_modelo_escolhido'], 2)} min", "MAE no teste", 0.66, 1.18, 2.85, GREEN)
    bs.add_metric(slide, f"{pt(reg['mae_validacao_modelo_escolhido'], 2)} min", "MAE na validação", 3.66, 1.18, 2.85, BLUE)
    bs.add_metric(slide, f"{pt(reg['mae_regua_validacao'], 2)} min", "média (referência, validação)", 6.66, 1.18, 3.0, CORAL)
    bs.add_metric(slide, "3,5 min", "meta de erro", 9.81, 1.18, 2.86, YELLOW)

    bs.add_card(slide, 0.66, 2.65, 5.95, 3.85, color="#FFFFFF", line=MINT)
    bs.add_text(slide, f"Modelo: árvore de profundidade {depth}", 0.90, 2.85, 5.5, 0.45, size=17, color=TEAL, bold=True)
    bs.add_bullet_list(
        slide,
        [
            "Escolhido pelo menor MAE na validação",
            f"Árvore {pt(reg['arvore_mae_validacao'], 2)} · reta {pt(reg['reta_mae_validacao'], 2)} · média {pt(reg['mae_regua_validacao'], 2)} min",
            "Teste aberto uma única vez",
        ],
        0.95,
        3.55,
        5.4,
        size=14.5,
        dot_color=GREEN,
        gap=0.72,
    )

    bs.add_card(slide, 6.72, 2.65, 5.95, 3.85, color="#FFFFFF", line=MINT)
    bs.add_text(slide, "O que o número significa", 6.96, 2.85, 5.5, 0.45, size=17, color=TEAL, bold=True)
    bs.add_bullet_list(
        slide,
        [
            f"A previsão erra, em média, {pt(reg['mae_teste_modelo_escolhido'], 2)} min",
            "Teste perto da validação: a escolha se sustenta",
            "Atende a meta de 3,5 min",
            "Algumas trocas erram mais que a média",
        ],
        6.99,
        3.55,
        5.4,
        size=14.5,
        dot_color=CORAL,
        gap=0.66,
    )


def draw_cell(slide, x: float, y: float, w: float, h: float, label: str, value: int, color: str, name: str) -> None:
    """Draw one confusion-matrix cell."""
    bs.add_card(slide, x, y, w, h, color=color)
    bs.add_text(slide, name, x + 0.1, y + 0.12, w - 0.2, 0.30, size=11.5, color=INK, bold=True, align=PP_ALIGN.CENTER)
    bs.add_text(slide, str(value), x + 0.1, y + 0.45, w - 0.2, 0.65, size=30, color=INK, bold=True, align=PP_ALIGN.CENTER)
    bs.add_text(slide, label, x + 0.1, y + 1.12, w - 0.2, 0.28, size=10.5, color=INK, align=PP_ALIGN.CENTER)


def slide_classification(prs: Presentation, clf: dict) -> None:
    """Slide 4: confusion matrix and measures, test against validation."""
    slide = new_slide(prs, "03", "Classificação: passa de 42 min?", 4)
    test, val = clf["arvore_teste"], clf["arvore_validacao"]
    bs.add_text(slide, "Matriz de confusão no teste", 0.66, 1.12, 6.2, 0.40, size=16, color=TEAL, bold=True)
    bs.add_text(slide, "previsto: normal", 1.92, 1.62, 2.3, 0.30, size=11, color=INK, bold=True, align=PP_ALIGN.CENTER)
    bs.add_text(slide, "previsto: demorada", 4.32, 1.62, 2.3, 0.30, size=11, color=INK, bold=True, align=PP_ALIGN.CENTER)
    bs.add_text(slide, "real:\nnormal", 0.66, 2.35, 1.2, 0.7, size=11, color=INK, bold=True, align=PP_ALIGN.CENTER)
    bs.add_text(slide, "real:\ndemorada", 0.66, 4.05, 1.2, 0.7, size=11, color=INK, bold=True, align=PP_ALIGN.CENTER)
    draw_cell(slide, 1.92, 1.98, 2.3, 1.55, "acertou: normal", test["VN"], MINT, "VN")
    draw_cell(slide, 4.32, 1.98, 2.3, 1.55, "alarme à toa", test["FP"], "#F8D2C8", "FP")
    draw_cell(slide, 1.92, 3.68, 2.3, 1.55, "demorada que passou", test["FN"], "#F8D2C8", "FN")
    draw_cell(slide, 4.32, 3.68, 2.3, 1.55, "demorada encontrada", test["VP"], MINT, "VP")

    measures = [
        ("Recall", val["VP"] / (val["VP"] + val["FN"]), test["VP"] / (test["VP"] + test["FN"])),
        ("Precisão", val["VP"] / (val["VP"] + val["FP"]), test["VP"] / (test["VP"] + test["FP"])),
    ]
    f1_val = clf["medidas_validacao"]["arvore"]["F1 %"]
    f1_test = clf["medidas_teste"]["F1 %"]
    bs.add_card(slide, 7.05, 1.12, 5.62, 4.11, color="#FFFFFF", line=MINT)
    bs.add_text(slide, "Validação × teste (%)", 7.30, 1.28, 5.1, 0.40, size=16, color=TEAL, bold=True)
    bs.add_text(slide, "validação", 9.35, 1.78, 1.5, 0.30, size=11.5, color=BLUE, bold=True, align=PP_ALIGN.CENTER)
    bs.add_text(slide, "teste", 10.95, 1.78, 1.4, 0.30, size=11.5, color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    rows = [(name, 100 * v, 100 * t) for name, v, t in measures] + [("F1", f1_val, f1_test)]
    for index, (name, v_value, t_value) in enumerate(rows):
        y = 2.28 + index * 0.95
        bs.add_shape(slide, MSO_SHAPE.RECTANGLE, 7.30, y + 0.06, 0.07, 0.55, GREEN)
        bs.add_text(slide, name, 7.50, y, 1.8, 0.65, size=17, color=INK, bold=True, valign=MSO_ANCHOR.MIDDLE)
        bs.add_text(slide, f"{pt(v_value)}%", 9.35, y, 1.5, 0.65, size=21, color=BLUE, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
        bs.add_text(slide, f"{pt(t_value)}%", 10.95, y, 1.4, 0.65, size=21, color=CORAL, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)

    bs.add_card(slide, 0.66, 5.55, 12.01, 0.95, color=TEAL)
    bs.add_text(
        slide,
        f"No teste, a árvore encontrou {test['VP']} de {test['VP'] + test['FN']} trocas demoradas. O teste ficou pior que a validação, e isso é esperado.",
        0.90,
        5.62,
        11.5,
        0.80,
        size=15,
        color=CREAM,
        bold=True,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
    )


def slide_conclusion(prs: Presentation, clf: dict) -> None:
    """Slide 5: dominant error, conclusion and limitation."""
    slide = new_slide(prs, "04", "Conclusão", 5)
    test = clf["arvore_teste"]
    recall = 100 * test["VP"] / (test["VP"] + test["FN"])
    precision = 100 * test["VP"] / (test["VP"] + test["FP"])

    bs.add_card(slide, 0.66, 1.18, 12.01, 1.95, color="#F8D2C8", line="#F0B7A9")
    bs.add_text(slide, "O erro mais comum é o falso positivo", 0.90, 1.32, 11.5, 0.42, size=18, color=CORAL, bold=True)
    bs.add_text(
        slide,
        f"{test['FP']} alarmes à toa contra {test['FN']} trocas demoradas perdidas. "
        f"Isso derruba a precisão ({pt(precision)}%) mais que o recall ({pt(recall)}%).",
        0.90,
        1.82,
        11.5,
        1.15,
        size=16,
        color=INK,
    )

    bs.add_card(slide, 0.66, 3.35, 5.95, 2.95, color="#FFFFFF", line=MINT)
    bs.add_text(slide, "O que os resultados permitem afirmar", 0.90, 3.50, 5.5, 0.42, size=16, color=GREEN, bold=True)
    bs.add_text(
        slide,
        "As informações disponíveis antes da troca bastam para estimar o tempo "
        "dentro da meta e para apontar a maior parte das trocas demoradas. "
        "A ajuda extra pode ser priorizada pelo risco.",
        0.90,
        4.00,
        5.5,
        2.15,
        size=14.5,
        color=INK,
    )

    bs.add_card(slide, 6.72, 3.35, 5.95, 2.95, color="#FFFFFF", line=MINT)
    bs.add_text(slide, "O que não permitem afirmar", 6.96, 3.50, 5.5, 0.42, size=16, color=CORAL, bold=True)
    bs.add_text(
        slide,
        "A base é sintética e a divisão foi por sorteio: o resultado não "
        "garante o mesmo desempenho numa fábrica real, nem mede mudanças ao "
        "longo do tempo. A previsão apoia a decisão do supervisor, não a substitui.",
        6.96,
        4.00,
        5.5,
        2.15,
        size=14.5,
        color=INK,
    )


def slide_thanks(prs: Presentation) -> None:
    """Slide 6: closing."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bs.set_background(slide, TEAL)
    bs.add_picture_contain(slide, bs.ASSET_DIR / "logo-uea.png", 10.45, 0.23, 1.15, 0.62)
    bs.add_picture_contain(slide, bs.ASSET_DIR / "logo-sialabs.png", 11.72, 0.19, 0.92, 0.68)
    bs.add_text(slide, "Agradecemos a atenção", 1.55, 1.02, 10.23, 0.70, size=32, color=CREAM, bold=True, align=PP_ALIGN.CENTER)
    bs.add_shape(slide, MSO_SHAPE.RECTANGLE, 5.23, 1.92, 2.87, 0.055, YELLOW)
    bs.add_picture_contain(slide, bs.ASSET_DIR / "logo-smt-em-tempo.png", 5.13, 2.20, 3.07, 2.70)
    bs.add_text(slide, "Perguntas?", 3.65, 5.08, 6.03, 0.52, size=24, color=CREAM, bold=True, align=PP_ALIGN.CENTER)
    bs.add_text(slide, "SMT em Tempo · Projeto 4 · Machine Learning", 3.13, 5.68, 7.07, 0.30, size=13, color=MINT, align=PP_ALIGN.CENTER)
    bs.add_text(
        slide,
        "Juliana Ballin Lima · Fernanda de Oliveira da Costa · Pedro Henrique Oliveira Dias",
        2.22,
        6.33,
        8.89,
        0.30,
        size=11,
        color=CREAM,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    bs.add_footer(slide, 6, color=CREAM)


def build() -> None:
    """Create and save the short N4 deck."""
    reg, clf, base = load_results()
    bs.TOTAL_SLIDES = TOTAL
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    bs.slide_cover(prs)
    for shape in prs.slides[0].shapes:
        if shape.has_text_frame and "Outubro de 2026" in shape.text_frame.text:
            shape.text_frame.paragraphs[0].runs[0].text = "Projeto 4 · Trabalho final · Novembro de 2026"
    slide_problem(prs, base)
    slide_regression(prs, reg)
    slide_classification(prs, clf)
    slide_conclusion(prs, clf)
    slide_thanks(prs)
    prs.save(OUTPUT)
    print(f"Apresentação criada em: {OUTPUT}")


if __name__ == "__main__":
    build()
