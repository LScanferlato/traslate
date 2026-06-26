"""
Renderer PDF bilingue: crea output PDF/HTML preservando layout originale.
Supporta overlay testo tradotto e layout affiancato.
"""

import os
import fitz
from pdf_handler import estrai_blocchi_testuali


def crea_pdf_bilingue(pdf_path, testo_tradotto, output_dir, lingua_target,
                       modalita="overlay"):
    """Crea PDF bilingue preservando immagini, formule e layout.

    modalita:
      - 'overlay':  testo tradotto sovrapposto all'originale
      - 'affiancato': originale a sinistra, traduzione a destra
      - 'mono':      solo traduzione
    """
    pagine = estrai_blocchi_testuali(pdf_path)
    righe_tradotte = [r for r in testo_tradotto.split("\n") if r.strip()]

    doc = fitz.open(pdf_path)
    nuovo_doc = fitz.open()
    idx_riga = 0

    for num_pag in range(len(doc)):
        pagina_orig = doc[num_pag]
        rect = pagina_orig.rect

        if modalita == "affiancato":
            larghezza = rect.width * 2 + 20
            nuova_pag = nuovo_doc.new_page(width=larghezza, height=rect.height)
            nuova_pag.show_pdf_page(
                fitz.Rect(0, 0, rect.width, rect.height), doc, num_pag
            )
            offset_x = rect.width + 20
            linea_div = fitz.Rect(rect.width + 9, 0, rect.width + 11, rect.height)
            nuova_pag.draw_rect(linea_div, color=(0.8, 0.8, 0.8), fill=(0.8, 0.8, 0.8))
        elif modalita == "overlay":
            nuova_pag = nuovo_doc.new_page(width=rect.width, height=rect.height)
            nuova_pag.show_pdf_page(rect, doc, num_pag)
            offset_x = 0
        else:
            nuova_pag = nuovo_doc.new_page(width=rect.width, height=rect.height)
            offset_x = 0

        if num_pag < len(pagine):
            for blocco in pagine[num_pag]:
                if idx_riga >= len(righe_tradotte):
                    break
                testo_trad = righe_tradotte[idx_riga]
                idx_riga += 1

                bbox = blocco["bbox"]
                fontsize = max(blocco["size"] * 0.85, 6)
                x = bbox[0] + offset_x
                y = bbox[1] + fontsize

                if modalita == "mono" and blocco["tipo"] != "ocr":
                    nuova_pag.add_redact_annot(bbox, fill=(1, 1, 1))
                    nuova_pag.apply_redactions()

                nuova_pag.insert_text(
                    point=(x, y),
                    text=testo_trad,
                    fontsize=fontsize,
                    fontname="helv",
                    color=(0, 0, 0.6) if modalita in ("overlay", "affiancato") else (0, 0, 0),
                )

                if modalita in ("overlay", "affiancato"):
                    if modalita == "affiancato":
                        pass
                    elif blocco["tipo"] == "testo":
                        nuova_pag.add_redact_annot(bbox, fill=(1, 1, 1))
                        nuova_pag.apply_redactions()

        if not pagine or num_pag >= len(pagine):
            nuova_pag.show_pdf_page(
                fitz.Rect(offset_x, 0, offset_x + rect.width, rect.height),
                doc, num_pag,
            )

    doc.close()

    suffisso = {"overlay": "bilingue", "affiancato": "affiancato", "mono": "tradotto"}.get(
        modalita, "bilingue"
    )
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    out_path = os.path.join(output_dir, f"{base}_{suffisso}_{lingua_target}.pdf")
    nuovo_doc.save(out_path, garbage=4, deflate=True)
    nuovo_doc.close()
    return out_path


def crea_html_bilingue(pdf_path, testo_tradotto, output_dir, lingua_target):
    """Crea HTML bilingue per anteprima e download."""
    pagine = estrai_blocchi_testuali(pdf_path)
    righe_tradotte = [r for r in testo_tradotto.split("\n") if r.strip()]

    html_parti = [
        "<!DOCTYPE html><html lang='it'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Traduzione Bilingue</title>",
        "<style>",
        "body{font-family:'Segoe UI',system-ui,sans-serif;max-width:1000px;margin:0 auto;padding:20px;background:#f8f9fa}",
        ".page{margin:30px 0;background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1);padding:24px}",
        ".page-num{font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}",
        ".block{display:flex;gap:20px;margin:6px 0;padding:4px 0;border-bottom:1px solid #f1f5f9}",
        ".original{flex:1;color:#1e293b}",
        ".translated{flex:1;color:#2563eb}",
        "h3{color:#1e293b;font-size:14px;text-transform:uppercase;letter-spacing:.5px;margin:0 0 4px}",
        "</style></head><body>",
        "<h1>Traduzione Bilingue</h1>",
        f"<p style='color:#64748b'>Documento: {os.path.basename(pdf_path)}</p>",
    ]

    idx_riga = 0
    for num_pag, pagina in enumerate(pagine):
        html_parti.append(f"<div class='page'><div class='page-num'>Pagina {num_pag+1}</div>")
        for blocco in pagina:
            if idx_riga >= len(righe_tradotte):
                break
            originale = blocco["testo"]
            tradotto = righe_tradotte[idx_riga]
            idx_riga += 1
            html_parti.append(
                f"<div class='block'>"
                f"<div class='original'><h3>Originale</h3>{originale}</div>"
                f"<div class='translated'><h3>Traduzione</h3>{tradotto}</div>"
                f"</div>"
            )
        html_parti.append("</div>")

    html_parti.append("</body></html>")

    base = os.path.splitext(os.path.basename(pdf_path))[0]
    out_path = os.path.join(output_dir, f"{base}_bilingue_{lingua_target}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parti))
    return out_path
