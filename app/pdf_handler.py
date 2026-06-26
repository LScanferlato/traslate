"""
Gestione avanzata PDF: estrazione testo strutturato con PyMuPDF + fallback OCR.
Supporta PDF con layer di testo e PDF scansionati.
"""

import fitz
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def rileva_tipo_pdf(pdf_path):
    """Rileva se un PDF ha layer di testo o è scansionato.
    Restituisce 'testo', 'scansionato', 'misto'."""
    doc = fitz.open(pdf_path)
    pagine_con_testo = 0
    totale = len(doc)

    for pagina in doc:
        testo = pagina.get_text().strip()
        if len(testo) > 50:
            pagine_con_testo += 1

    doc.close()

    if pagine_con_testo == 0:
        return "scansionato"
    elif pagine_con_testo < totale:
        return "misto"
    return "testo"


def estrai_blocchi_testuali(pdf_path, lingua_ocr="ita+eng", dpi=200):
    """Estrae blocchi di testo con posizione dal PDF.
    Per PDF con layer di testo usa PyMuPDF.
    Per PDF scansionati usa OCR Tesseract.

    Restituisce: lista di pagine, ognuna con lista di dict:
        {testo, bbox (x0,y0,x1,y1), font, size, tipo}
    """
    doc = fitz.open(pdf_path)
    pagine = []

    for num_pag in range(len(doc)):
        pagina = doc[num_pag]
        blocchi_raw = pagina.get_text("dict")["blocks"]
        blocchi_testo = []

        ha_testo_layer = any(
            b["type"] == 0 and
            any(span["text"].strip() for linea in b["lines"] for span in linea["spans"])
            for b in blocchi_raw
        )

        if ha_testo_layer:
            for blocco in blocchi_raw:
                if blocco["type"] != 0:
                    continue
                for linea in blocco["lines"]:
                    testo = "".join(span["text"] for span in linea["spans"]).strip()
                    if not testo:
                        continue
                    span0 = linea["spans"][0]
                    blocchi_testo.append({
                        "testo": testo,
                        "bbox": tuple(linea["bbox"]),
                        "font": span0["font"],
                        "size": span0["size"],
                        "tipo": "testo",
                    })
        else:
            immagini = convert_from_path(
                pdf_path,
                first_page=num_pag + 1,
                last_page=num_pag + 1,
                dpi=dpi,
            )
            if not immagini:
                continue

            img = immagini[0]
            w_px, h_px = img.size
            w_pt = pagina.rect.width
            h_pt = pagina.rect.height

            dati = pytesseract.image_to_data(
                img, lang=lingua_ocr, output_type=pytesseract.Output.DICT
            )

            prev_blocco = None
            for i in range(len(dati["text"])):
                testo = dati["text"][i].strip()
                if not testo:
                    prev_blocco = None
                    continue
                conf = int(dati["conf"][i]) if dati["conf"][i] != "-1" else 0
                if conf < 30:
                    continue

                x = dati["left"][i] * w_pt / w_px
                y = dati["top"][i] * h_pt / h_px
                w = dati["width"][i] * w_pt / w_px
                h = dati["height"][i] * h_pt / h_px

                block_num = dati["block_num"][i]
                par_num = dati["par_num"][i]

                if (prev_blocco and
                        prev_blocco["_block"] == block_num and
                        prev_blocco["_par"] == par_num):
                    prev_blocco["testo"] += " " + testo
                    vecchio = prev_blocco["bbox"]
                    prev_blocco["bbox"] = (
                        min(vecchio[0], x),
                        min(vecchio[1], y),
                        max(vecchio[2], x + w),
                        max(vecchio[3], y + h),
                    )
                else:
                    nuovo = {
                        "testo": testo,
                        "bbox": (x, y, x + w, y + h),
                        "font": "",
                        "size": h,
                        "tipo": "ocr",
                        "_block": block_num,
                        "_par": par_num,
                    }
                    blocchi_testo.append(nuovo)
                    prev_blocco = nuovo

        pagine.append(blocchi_testo)

    doc.close()
    return pagine


def estrai_testo_piatto(pdf_path, lingua_ocr="ita+eng", con_posizioni=False):
    """Estrae tutto il testo dal PDF come stringa unica.
    Se con_posizioni=True, restituisce anche i bounding box."""
    pagine = estrai_blocchi_testuali(pdf_path, lingua_ocr)

    if con_posizioni:
        return pagine

    return "\n".join(
        blocco["testo"]
        for pagina in pagine
        for blocco in pagina
    )


def pagina_ha_testo(pdf_path, num_pag):
    """Verifica se una pagina specifica ha layer di testo."""
    doc = fitz.open(pdf_path)
    if num_pag >= len(doc):
        doc.close()
        return False
    testo = doc[num_pag].get_text().strip()
    doc.close()
    return len(testo) > 50
