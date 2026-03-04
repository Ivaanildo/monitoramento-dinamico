import argparse
import json
from datetime import datetime
from pathlib import Path

import openpyxl


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert an input .xlsx file into the mock_painel JSON shape."
    )
    parser.add_argument("input_file", help="Path to the source .xlsx file")
    parser.add_argument(
        "--output",
        default="mock_painel.json",
        help="Path to the generated JSON file (default: mock_painel.json)",
    )
    return parser.parse_args()


def _normalize_status(raw_status: object, atraso: int) -> str:
    status_text = str(raw_status or "").strip()
    if not status_text or "n/a" in status_text.lower() or "none" in status_text.lower():
        status = "N/A"
    else:
        status = status_text.capitalize()
        if status not in {"Normal", "Moderado", "Intenso"}:
            status = "Normal"

    if status == "Moderado" and atraso > 30:
        return "Intenso"
    return status


def _confidence_pct(raw_confidence: object) -> int:
    confidence = str(raw_confidence or "Media").strip()
    if confidence == "Alta":
        return 95
    if confidence in {"Media", "Média"}:
        return 75
    return 50


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    args = _parse_args()
    input_path = Path(args.input_file)
    output_path = Path(args.output)

    workbook = openpyxl.load_workbook(input_path)
    worksheet = workbook.active

    headers = [cell.value for cell in worksheet[4]]
    rows = []
    for row in worksheet.iter_rows(min_row=5, values_only=True):
        if any(row):
            rows.append(dict(zip(headers, row)))

    resultados = []
    for index, row in enumerate(rows, start=1):
        atraso = _safe_int(row.get("Atraso (min)"))
        status = _normalize_status(row.get("Status"), atraso)

        resultados.append(
            {
                "rota_id": f"R{index:02d}",
                "sigla": str(row.get("Rodovia", "N/A")).split("/")[0].strip()
                if row.get("Rodovia")
                else "N/A",
                "nome": str(row.get("Rodovia", "N/A")),
                "trecho": str(row.get("Trecho", "N/A")),
                "status": status,
                "ocorrencia": str(row.get("Ocorrencia", "")).replace("None", ""),
                "relato": str(row.get("Descricao / Observacoes", "")).replace("None", ""),
                "hora_atualizacao": str(
                    row.get("Atualizado em", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                ),
                "atraso_min": atraso,
                "confianca_pct": _confidence_pct(row.get("Confianca")),
            }
        )

    payload = {
        "consultado_em": datetime.now().isoformat(),
        "fonte": "mock_excel",
        "total_rotas": len(resultados),
        "resultados": resultados,
    }

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, indent=2, ensure_ascii=False)

    print(f"Mock gerado com sucesso: {output_path} ({len(resultados)} rotas)")


if __name__ == "__main__":
    main()
