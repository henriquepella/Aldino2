"""Empacotamento do projeto completo em ZIP (seção 35).

Estrutura:
    Projeto_Geoestatistico.zip
      dados/           dataset limpo + arquivo original
      tabelas/         todas as tabelas (.csv)
      graficos/        histogramas, boxplots, scatter, variograma...
      mapas/           mapas (.png/.svg/.pdf/.tif)
      relatorio/       relatorio.pdf
      configuracoes/   run.json + config.json
"""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


def build_package(
    run_dir: Path,
    *,
    dest: Path,
    original_file: Path | None = None,
    clean_file: Path | None = None,
    config: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> Path:
    run_dir = Path(run_dir)
    dest.parent.mkdir(parents=True, exist_ok=True)

    mapping = {
        "tabelas": run_dir / "tables",
        "graficos": run_dir / "figures",
        "mapas": run_dir / "maps",
        "relatorio": run_dir / "report",
    }

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, folder in mapping.items():
            if folder.is_dir():
                for f in sorted(folder.rglob("*")):
                    if f.is_file():
                        zf.write(f, f"{arc}/{f.relative_to(folder)}")

        if clean_file and Path(clean_file).is_file():
            zf.write(clean_file, f"dados/{Path(clean_file).name}")
        if original_file and Path(original_file).is_file():
            zf.write(original_file, f"dados/original_{Path(original_file).name}")

        if manifest is not None:
            zf.writestr("configuracoes/run.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        if config is not None:
            zf.writestr("configuracoes/config.json", json.dumps(config, ensure_ascii=False, indent=2))

        readme = (
            "Pacote gerado pela Plataforma de Análise Geoestatística.\n\n"
            "dados/         dados utilizados (versão limpa e arquivo original)\n"
            "tabelas/       todas as tabelas em CSV\n"
            "graficos/      gráficos estatísticos\n"
            "mapas/         mapas (PNG/SVG/PDF/GeoTIFF quando aplicável)\n"
            "relatorio/     relatório técnico em PDF\n"
            "configuracoes/ parâmetros e manifesto de reprodutibilidade (run.json)\n"
        )
        zf.writestr("LEIA-ME.txt", readme)

    return dest


def copy_into(src: Path, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / Path(src).name
    shutil.copy2(src, out)
    return out
