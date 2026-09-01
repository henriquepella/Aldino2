"""Gerador do relatório técnico em PDF (seções 26, 27, 44).

Layout profissional com ReportLab: capa, sumário, cabeçalho/rodapé com numeração
de páginas, tabelas formatadas, figuras/mapas em alta resolução, interpretação
automática (determinística) e anexo de reprodutibilidade.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from app.analysis.interpret import num

PRIMARY = colors.HexColor("#1f3b5c")
ACCENT = colors.HexColor("#3b6ea5")
LIGHT = colors.HexColor("#eef2f7")
GREY = colors.HexColor("#666666")

CONTENT_W = A4[0] - 4 * cm


def _styles() -> dict[str, ParagraphStyle]:
    ss = getSampleStyleSheet()
    out = {
        "title": ParagraphStyle("t", parent=ss["Title"], fontSize=26, textColor=PRIMARY,
                                leading=30, spaceAfter=6),
        "subtitle": ParagraphStyle("st", parent=ss["Normal"], fontSize=13, textColor=GREY,
                                   alignment=TA_CENTER, leading=18),
        "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=16, textColor=PRIMARY,
                             spaceBefore=16, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12.5, textColor=ACCENT,
                             spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("b", parent=ss["Normal"], fontSize=9.5, leading=14,
                               alignment=TA_JUSTIFY, spaceAfter=6),
        "note": ParagraphStyle("n", parent=ss["Normal"], fontSize=8.5, leading=12,
                               textColor=GREY, spaceAfter=4),
        "cap": ParagraphStyle("c", parent=ss["Normal"], fontSize=8, leading=10,
                              textColor=GREY, alignment=TA_CENTER, spaceAfter=10),
        "cell": ParagraphStyle("cell", parent=ss["Normal"], fontSize=7.5, leading=9),
        "cellh": ParagraphStyle("cellh", parent=ss["Normal"], fontSize=7.5, leading=9,
                                textColor=colors.white, fontName="Helvetica-Bold"),
    }
    return out


S = _styles()

# key do passo -> (número da seção, título)
SECTIONS: list[tuple[str, str]] = [
    ("descriptive", "Estatística Descritiva"),
    ("esda_univariate", "ESDA Univariada"),
    ("__tests__", "Testes Estatísticos"),
    ("moran_scatter", "Moran Scatter Plot"),
    ("esda_bivariate", "ESDA Bivariada"),
    ("idw", "IDW — Inverse Distance Weighting"),
    ("kriging", "Krigagem Ordinária"),
    ("external_drift", "Krigagem com Deriva Externa"),
    ("gwr", "GWR / GWM"),
    ("cokriging", "Co-Krigagem"),
    ("method_comparison", "Comparação Geral dos Métodos"),
]


class _Doc(BaseDocTemplate):
    def __init__(self, path: str, meta: dict[str, Any], **kw):
        super().__init__(path, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                         topMargin=2.2 * cm, bottomMargin=2 * cm, **kw)
        self._meta = meta
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="n")
        cover = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="c")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover]),
            PageTemplate(id="body", frames=[frame], onPage=self._decorate),
        ])
        self._toc_entries: list[tuple[int, str, int]] = []

    def _decorate(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, A4[1] - 1.6 * cm, A4[0] - 2 * cm, A4[1] - 1.6 * cm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GREY)
        canvas.drawString(2 * cm, A4[1] - 1.4 * cm, self._meta.get("project_name", ""))
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.4 * cm,
                               "Relatório de Análise Geoestatística")
        canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
        canvas.drawString(2 * cm, 1.1 * cm, self._meta.get("generated", ""))
        canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Página {doc.page}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("h1",):
            text = flowable.getPlainText()
            self.notify("TOCEntry", (0, text, self.page))


def _df_table(df, max_rows: int = 40, max_cols: int = 12, highlight: list[int] | None = None):
    import pandas as pd  # noqa: F401

    cols = list(df.columns)[:max_cols]
    trimmed_cols = len(df.columns) > max_cols
    rows = df.head(max_rows)
    trimmed_rows = len(df) > max_rows

    data = [[Paragraph(str(c), S["cellh"]) for c in cols]]
    for _, r in rows.iterrows():
        line = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                v = num(v, 4) if v == v else "—"
            line.append(Paragraph(str(v), S["cell"]))
        data.append(line)

    w = CONTENT_W / max(len(cols), 1)
    t = Table(data, colWidths=[w] * len(cols), repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d2de")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for hr in (highlight or []):
        if 0 <= hr < len(rows):
            style.append(("BACKGROUND", (0, hr + 1), (-1, hr + 1), colors.HexColor("#d6ebd6")))
            style.append(("FONTNAME", (0, hr + 1), (-1, hr + 1), "Helvetica-Bold"))
    t.setStyle(TableStyle(style))
    flow = [t]
    if trimmed_rows or trimmed_cols:
        msg = []
        if trimmed_rows:
            msg.append(f"{len(df) - max_rows} linhas adicionais omitidas")
        if trimmed_cols:
            msg.append(f"{len(df.columns) - max_cols} colunas omitidas")
        flow.append(Paragraph("Tabela truncada: " + "; ".join(msg) + " (ver anexo/CSV).", S["note"]))
    return flow


import tempfile

_EMBED_DIR = Path(tempfile.gettempdir()) / "geo_pdf_embed"


def _downscaled(p: Path, max_px: int = 1400) -> Path:
    """Reduz a resolução do PNG para embutir no PDF (fora das pastas de artefatos,
    para não inflar o pacote ZIP)."""
    try:
        from PIL import Image as PILImage

        with PILImage.open(p) as im:
            if max(im.size) <= max_px and p.stat().st_size < 400_000:
                return p
            im = im.convert("RGB")
            im.thumbnail((max_px, max_px), PILImage.LANCZOS)
            _EMBED_DIR.mkdir(parents=True, exist_ok=True)
            out = _EMBED_DIR / f"{abs(hash(str(p)))}_{p.stem}.jpg"
            im.save(out, "JPEG", quality=80, optimize=True)
            return out
    except Exception:  # noqa: BLE001
        return p


def _image(path: str, caption: str = "") -> list:
    p = Path(path)
    if not p.exists():
        return []
    try:
        from PIL import Image as PILImage

        embed = _downscaled(p)
        with PILImage.open(embed) as im:
            iw, ih = im.size
        max_w = CONTENT_W
        max_h = 11 * cm
        ratio = min(max_w / iw, max_h / ih)
        img = Image(str(embed), width=iw * ratio, height=ih * ratio)
    except Exception:  # noqa: BLE001
        img = Image(str(p), width=CONTENT_W, height=8 * cm)
    out = [Spacer(1, 4), img]
    if caption:
        out.append(Paragraph(caption, S["cap"]))
    out.append(Spacer(1, 4))
    return out


def _step_flow(step, figures_limit: int = 4) -> list:
    flow: list = []
    if step is None:
        flow.append(Paragraph("Análise não disponível para este conjunto de dados.", S["note"]))
        return flow
    if step.status == "skipped":
        flow.append(Paragraph(f"<b>Não executada.</b> {step.reason}", S["body"]))
        return flow
    if step.status == "failed":
        flow.append(Paragraph(f"<b>Falha na execução.</b> {step.reason}", S["body"]))
        return flow
    if step.interpretation:
        flow.append(Paragraph(step.interpretation, S["body"]))
    for t in step.tables:
        if t.title:
            flow.append(Paragraph(t.title, S["h2"]))
        flow += _df_table(t.df, highlight=t.highlight_rows)
        if t.caption:
            flow.append(Paragraph(t.caption, S["note"]))
        flow.append(Spacer(1, 6))
    for fig in step.figures[:figures_limit]:
        png = fig.paths.get("png")
        if png:
            flow += _image(png, fig.caption or fig.title)
    return flow


def _params_used(step) -> dict:
    return {k: v for k, v in (getattr(step, "params_used", {}) or {}).items() if k != "traceback"}


def build_report(
    *,
    out_path: str | Path,
    project: dict[str, Any],
    dataset: dict[str, Any],
    run_meta: dict[str, Any],
    pipeline_output,
    validation: dict[str, Any] | None,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    steps = {s.key: s for s in pipeline_output.steps}
    now = dt.datetime.now().strftime("%d/%m/%Y %H:%M")

    doc = _Doc(str(out_path), meta={
        "project_name": project.get("name", "Projeto"),
        "generated": f"Gerado em {now}",
    })

    story: list = []

    # ---------------- CAPA ----------------
    story += [
        Spacer(1, 3 * cm),
        Paragraph("Relatório de Análise Geoestatística", S["title"]),
        Spacer(1, 0.4 * cm),
        Paragraph(project.get("name", "Projeto sem nome"), S["subtitle"]),
        Spacer(1, 2.5 * cm),
    ]
    cover_rows = [
        ["Cliente", project.get("client") or "—"],
        ["Responsável técnico", project.get("technical_lead") or "—"],
        ["Data da análise", project.get("analysis_date") or now],
        ["Sistema de coordenadas", (project.get("crs_label") or project.get("crs") or "—")],
        ["Unidade das variáveis", project.get("variable_units") or "—"],
        ["Arquivo de dados", dataset.get("original_filename") or "—"],
        ["Registros analisados", str(pipeline_output.metrics_summary.get("n_points", "—"))],
        ["Identificador da execução", run_meta.get("id", "—")],
    ]
    ct = Table(cover_rows, colWidths=[5 * cm, CONTENT_W - 5 * cm])
    ct.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d2de")),
    ]))
    story += [ct, Spacer(1, 3 * cm),
              Paragraph("Documento gerado automaticamente. As interpretações baseiam-se "
                        "exclusivamente nos resultados numéricos calculados.", S["note"])]
    story += [NextPageTemplate("body"), PageBreak()]

    # ---------------- SUMÁRIO ----------------
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("toc1", fontSize=10, leading=16, leftIndent=6)]
    story += [Paragraph("Sumário", S["h1"]), toc, PageBreak()]

    # ---------------- 1. INTRODUÇÃO ----------------
    story.append(Paragraph("1. Introdução", S["h1"]))
    story.append(Paragraph(
        "Este relatório apresenta a análise geoestatística completa do conjunto de dados "
        f"espaciais informado. O objetivo é caracterizar a variável de interesse "
        f"(<b>{dataset.get('config', {}).get('primary', '—')}</b>), avaliar sua estrutura de "
        "dependência espacial, comparar métodos de interpolação por validação cruzada e "
        "disponibilizar mapas e métricas para tomada de decisão. "
        + (project.get("description") or ""), S["body"]))

    # ---------------- 2. DADOS UTILIZADOS ----------------
    story.append(Paragraph("2. Dados Utilizados", S["h1"]))
    cfg = dataset.get("config", {})
    data_rows = [
        ["Origem", dataset.get("original_filename") or "arquivo enviado pelo usuário"],
        ["Registros", str(dataset.get("row_count", "—"))],
        ["Colunas", str(dataset.get("col_count", "—"))],
        ["Coordenadas", f"X = {cfg.get('x_col','—')} · Y = {cfg.get('y_col','—')}"],
        ["CRS", project.get("crs_label") or project.get("crs") or cfg.get("crs", "—")],
        ["Variável principal", cfg.get("primary", "—")],
        ["Variáveis secundárias", ", ".join(cfg.get("secondary", []) or []) or "—"],
        ["Variáveis explicativas (GWR)", ", ".join(cfg.get("explanatory", []) or []) or "—"],
        ["Variável auxiliar (deriva/co-krigagem)", cfg.get("aux_drift") or "—"],
    ]
    dt_tbl = Table(data_rows, colWidths=[6 * cm, CONTENT_W - 6 * cm])
    dt_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d2de")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(dt_tbl)

    # ---------------- 3. CONTROLE DE QUALIDADE ----------------
    story.append(Paragraph("3. Controle de Qualidade", S["h1"]))
    if validation and validation.get("summary"):
        qrows = [[Paragraph("Item", S["cellh"]), Paragraph("Resultado", S["cellh"]),
                  Paragraph("Status", S["cellh"]), Paragraph("Observação", S["cellh"])]]
        for it in validation["summary"]:
            qrows.append([
                Paragraph(str(it.get("item", "")), S["cell"]),
                Paragraph(str(it.get("value", "")), S["cell"]),
                Paragraph({"ok": "OK", "warn": "Atenção", "error": "Erro"}.get(it.get("status"), ""), S["cell"]),
                Paragraph(str(it.get("detail", "")), S["cell"]),
            ])
        qt = Table(qrows, colWidths=[5 * cm, 3 * cm, 2.5 * cm, CONTENT_W - 10.5 * cm], repeatRows=1)
        qt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d2de")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ]))
        story.append(qt)
        from app.analysis.interpret import interpret_data_quality

        story.append(Spacer(1, 6))
        story.append(Paragraph(interpret_data_quality(validation.get("counts", {})), S["body"]))
        if validation.get("notes"):
            story.append(Paragraph("Tratamento aplicado: " + "; ".join(validation["notes"]), S["note"]))
    else:
        story.append(Paragraph("Diagnóstico de qualidade não disponível.", S["note"]))

    # ---------------- 4..14 SEÇÕES DE ANÁLISE ----------------
    n = 4
    for key, title in SECTIONS:
        story.append(PageBreak())
        story.append(Paragraph(f"{n}. {title}", S["h1"]))
        if key == "__tests__":
            story.append(Paragraph(
                "Consolidação dos testes de significância (autocorrelação e distribuição). "
                f"Nível de significância adotado: α = {num(run_meta.get('alpha', 0.05), 2)}. "
                f"Permutações: {run_meta.get('n_perm', 999)}.", S["body"]))
            found = False
            for sk in ("esda_univariate", "esda_bivariate"):
                st = steps.get(sk)
                if not st:
                    continue
                for t in st.tables:
                    if "test" in t.name.lower() or "Teste" in (t.title or ""):
                        found = True
                        story.append(Paragraph(f"{st.title}: {t.title or t.name}", S["h2"]))
                        story += _df_table(t.df, highlight=t.highlight_rows)
            if not found:
                story.append(Paragraph("Nenhuma tabela de testes foi produzida.", S["note"]))
        else:
            story += _step_flow(steps.get(key))
        n += 1

    # ---------------- 15. CONCLUSÃO ----------------
    story.append(PageBreak())
    story.append(Paragraph(f"{n}. Conclusão", S["h1"]))
    story.append(Paragraph(pipeline_output.conclusion or "—", S["body"]))
    n += 1

    # ---------------- 16. ANEXOS ----------------
    story.append(PageBreak())
    story.append(Paragraph(f"{n}. Anexos", S["h1"]))
    story.append(Paragraph("16.1 Configuração da Análise (reprodutibilidade)", S["h2"]))
    ctx_snap = (pipeline_output.manifest or {}).get("context", {})
    adv = ctx_snap.get("advanced", {})
    cfg_rows = [["Parâmetro", "Valor"]]
    for k, v in {**{kk: vv for kk, vv in ctx_snap.items() if kk != "advanced"}, **adv}.items():
        cfg_rows.append([str(k), str(v)])
    story += _df_table(_as_df(cfg_rows))

    story.append(Paragraph("16.2 Versões das bibliotecas", S["h2"]))
    libs = run_meta.get("lib_versions", {}) or (pipeline_output.manifest or {}).get("library_versions", {})
    story += _df_table(_as_df([["Biblioteca", "Versão"]] + [[k, v] for k, v in libs.items()]))

    skipped = [s for s in pipeline_output.steps if s.status in ("skipped", "failed")]
    if skipped:
        story.append(Paragraph("16.3 Análises não executadas", S["h2"]))
        story += _df_table(_as_df(
            [["Análise", "Situação", "Motivo"]]
            + [[s.title, "ignorada" if s.status == "skipped" else "falha", s.reason or ""] for s in skipped]
        ))

    doc.multiBuild(story)
    return out_path


def _as_df(rows: list[list]):
    import pandas as pd

    return pd.DataFrame(rows[1:], columns=rows[0])
