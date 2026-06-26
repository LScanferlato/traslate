import os
import requests
import gradio as gr
from docx import Document
from utils import leggi_file, scrivi_traduzione, LINGUE_SUPPORTATE, LINGUE_OCR, FORMATI_SUPPORTATI
from translator import OllamaTranslator, OpenAITranslator, modelli_per_vram, modelli_senza_filtro, OPZIONI_VRAM, MODELLI_DISPONIBILI
from pdf_handler import rileva_tipo_pdf, estrai_blocchi_testuali

APP_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(APP_DIR, "..", "output"))
INPUT_DIR = os.getenv("INPUT_DIR", os.path.join(APP_DIR, "..", "input"))
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(INPUT_DIR, exist_ok=True)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
traduttore_ollama = OllamaTranslator(host=OLLAMA_HOST)

traduttore_siliconflow = None
try:
    traduttore_siliconflow = OpenAITranslator()
except ValueError:
    pass

CSS = """
.app-header { display:flex; align-items:center; gap:14px; padding:16px 0 12px; border-bottom:2px solid #e5e7eb; margin-bottom:20px }
.app-header .icon { background:linear-gradient(135deg,#2563eb,#7c3aed); border-radius:14px; width:52px; height:52px; display:flex; align-items:center; justify-content:center; font-size:26px; color:white; flex-shrink:0 }
.app-header .title { font-size:22px; font-weight:700; color:#1e293b; letter-spacing:-0.5px; line-height:1.2 }
.app-header .subtitle { font-size:13px; color:#64748b }
.label-section { font-size:12px; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin:16px 0 8px }
"""

FORMATI_OUTPUT = [
    ("Originale (come da input)", "originale"),
    ("PDF", "pdf"),
    ("DOCX (Word)", "docx"),
    ("TXT (testo)", "txt"),
]

def aggiorna_modelli_lista():
    return gr.Dropdown(choices=modelli_senza_filtro() or [], value=None)

def filtra_modelli(vram_gb):
    return gr.Dropdown(choices=modelli_per_vram(vram_gb), value=None)

def download_da_url(url):
    if not url:
        return None, "Nessun URL fornito."
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        nome = os.path.basename(url.split("?")[0]) or "documento"
        percorso = os.path.join(INPUT_DIR, nome)
        with open(percorso, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return percorso, f"✅ Scaricato: {nome}"
    except Exception as e:
        return None, f"Errore download: {e}"

def esegui_traduzione(testo, codice_src, codice_tgt, modello_selezionato):
    if modello_selezionato.startswith("siliconflow/"):
        if traduttore_siliconflow is None:
            raise ValueError("SILICONFLOW_API_KEY non impostata nel file .env")
        return traduttore_siliconflow.traduci(
            testo, LINGUE_SUPPORTATE[codice_src], LINGUE_SUPPORTATE[codice_tgt],
            modello=modello_selezionato,
        )
    return traduttore_ollama.traduci(
        testo, LINGUE_SUPPORTATE[codice_src], LINGUE_SUPPORTATE[codice_tgt],
        modello=modello_selezionato,
    )

def scrivi_come_formato(testo_tradotto, file_originale, output_dir, formato, lingua_target):
    base = os.path.splitext(os.path.basename(file_originale))[0]
    suffisso = f"tradotto_{lingua_target}"

    if formato == "txt":
        path = os.path.join(output_dir, f"{base}_{suffisso}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(testo_tradotto)
        return path

    if formato == "docx":
        path = os.path.join(output_dir, f"{base}_{suffisso}.docx")
        doc = Document()
        for riga in testo_tradotto.split("\n"):
            if riga.strip():
                doc.add_paragraph(riga)
        doc.save(path)
        return path

    if formato == "pdf":
        path = os.path.join(output_dir, f"{base}_{suffisso}.pdf")
        import fitz
        doc = fitz.open()
        pagina = doc.new_page()
        rect = pagina.rect
        y = 30
        for riga in testo_tradotto.split("\n"):
            if riga.strip():
                pagina.insert_text((30, y), riga, fontsize=10, fontname="helv")
                y += 14
                if y > rect.height - 30:
                    pagina = doc.new_page()
                    y = 30
        doc.save(path, garbage=4, deflate=True)
        doc.close()
        return path

    return scrivi_traduzione(
        testo_tradotto, file_originale, output_dir, lingua_target,
        modalita_pdf="bilingue",
    )

def traduci_file(file, codice_src, codice_tgt, codice_ocr, modello_selezionato,
                  formato_output):
    if file is None:
        return None, "Nessun file caricato.", "", None
    if not modello_selezionato:
        return None, "Seleziona un modello.", "", None
    try:
        lingua_ocr_full = f"{codice_ocr}+eng" if codice_ocr else "ita+eng"
        testo = leggi_file(file.name, lingua_ocr=lingua_ocr_full)
        if not testo.strip():
            return None, "Nessun testo estratto. Verifica che il file non sia vuoto.", "", None

        traduzione = esegui_traduzione(testo, codice_src, codice_tgt, modello_selezionato)

        percorso_out = scrivi_come_formato(
            traduzione, file.name, OUTPUT_DIR, formato_output, codice_tgt
        )
        return percorso_out, "Traduzione completata con successo!", f"{percorso_out}", traduzione
    except Exception as e:
        return None, f"Errore: {e}", "", ""

def ottieni_info_modello(modello_nome):
    if modello_nome and modello_nome in MODELLI_DISPONIBILI:
        info = MODELLI_DISPONIBILI[modello_nome]
        if info["vram_gb"] == 0:
            return f"**{modello_nome}**  \n{info['desc']}  \nRichiede API key SiliconFlow (gratuita)"
        return f"**{modello_nome}**  \n{info['desc']}  \nVRAM richiesta: ~{info['vram_gb']} GB"
    return "Seleziona un modello per vedere i dettagli."

def info_file(file):
    if file is None:
        return "", ""
    nome = file.name.lower()
    if nome.endswith(".pdf"):
        tipo = rileva_tipo_pdf(file.name)
        tipo_label = {"testo": "PDF con layer di testo", "scansionato": "PDF scansionato (OCR)", "misto": "PDF misto"}.get(tipo, tipo)
        pagine = estrai_blocchi_testuali(file.name)
        tot_caratteri = sum(len(b["testo"]) for p in pagine for b in p)
        return f"**{os.path.basename(file.name)}**  \n{tipo_label} | {len(pagine)} pagine | ~{tot_caratteri} caratteri", ""
    return f"**{os.path.basename(file.name)}**", ""

def traduci_testo_diretto(testo_input, codice_src, codice_tgt, modello_selezionato):
    if not testo_input:
        return "", "Nessun testo inserito."
    if not modello_selezionato:
        return "", "Seleziona un modello."
    try:
        traduzione = esegui_traduzione(testo_input, codice_src, codice_tgt, modello_selezionato)
        return traduzione, "✅ Traduzione completata!"
    except Exception as e:
        return "", f"Errore: {e}"

with gr.Blocks(
    title="Traduttore Intelligente con IA Locale",
) as demo:
    gr.HTML("""
    <div class="app-header">
      <div class="icon">🌐</div>
      <div>
        <div class="title">Traduttore Intelligente</div>
        <div class="subtitle">Traduzione locale con IA — Ollama + SiliconFlow + OCR</div>
      </div>
    </div>
    """)

    stato_vram = gr.State(8)
    stato_traduzione = gr.State("")

    with gr.Row(equal_height=False):
        with gr.Column(scale=1, min_width=340):
            gr.HTML("<div class='label-section'>Configurazione</div>")
            with gr.Group():
                with gr.Row():
                    vram_radio = gr.Radio(
                        choices=OPZIONI_VRAM,
                        label="Memoria GPU (VRAM)",
                        value=8,
                    )
                modello_dropdown = gr.Dropdown(
                    choices=modelli_per_vram(8),
                    label="Modello di traduzione",
                    interactive=True,
                    value="qwen2.5:3b",
                )
                info_modello = gr.Markdown(
                    value="Seleziona un modello per vedere i dettagli.",
                )
                with gr.Row():
                    refresh_btn = gr.Button("🔄 Aggiorna modelli", size="sm", scale=1)
                    pull_btn = gr.Button("📥 Scarica modello", size="sm", scale=1)
                pull_name = gr.Textbox(
                    label="Scarica da Ollama (es. llama3.2:3b)",
                    placeholder="llama3.2:3b",
                )

            gr.HTML("<div class='label-section'>Lingue</div>")
            with gr.Group():
                src_lang = gr.Dropdown(
                    choices=[(v, k) for k, v in LINGUE_SUPPORTATE.items()],
                    label="Lingua originale",
                    value="ita",
                )
                tgt_lang = gr.Dropdown(
                    choices=[(v, k) for k, v in LINGUE_SUPPORTATE.items()],
                    label="Lingua target",
                    value="ita",
                )
                ocr_lang = gr.Dropdown(
                    choices=[(v, k) for k, v in LINGUE_OCR.items()],
                    label="Lingua OCR (per PDF scansionati)",
                    value="ita",
                )

            gr.HTML("<div class='label-section'>Formato output</div>")
            with gr.Group():
                formato_output = gr.Radio(
                    choices=FORMATI_OUTPUT,
                    label="Formato di output",
                    value="originale",
                )
                gr.Markdown(
                    "Formati supportati in input: "
                    + ", ".join(f"`{k.upper()}`" for k in sorted(FORMATI_SUPPORTATI.keys()))
                )

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("📄 File / Documento"):
                    with gr.Group():
                        url_input = gr.Textbox(
                            label="Incolla un URL per scaricare un documento",
                            placeholder="https://esempio.com/documento.pdf",
                        )
                        with gr.Row():
                            download_btn = gr.Button("⬇️ Download da URL", size="sm", scale=1)
                            url_status = gr.Textbox(label="", interactive=False, scale=2)
                        file_input = gr.File(
                            label="Carica file",
                            file_types=list(FORMATI_SUPPORTATI.keys()),
                        )
                        file_info = gr.Markdown(value="")
                        translate_btn = gr.Button("🚀 Traduci file", variant="primary", size="lg")
                        with gr.Row():
                            output_file = gr.File(label="Scarica traduzione")
                            output_path = gr.Textbox(label="Percorso file", interactive=False)
                        status_box = gr.Textbox(label="Stato", interactive=False)

                    gr.HTML("<div class='label-section'>Anteprima</div>")
                    with gr.Row():
                        with gr.Column():
                            preview_src = gr.Textbox(label="Originale (prime righe)", lines=6, interactive=False)
                        with gr.Column():
                            preview_tgt = gr.Textbox(label="Tradotto (prime righe)", lines=6, interactive=False)

                with gr.Tab("✏️ Testo diretto"):
                    with gr.Group():
                        testo_input = gr.Textbox(
                            label="Incolla il testo da tradurre",
                            placeholder="Scrivi o incolla qui il testo...",
                            lines=8,
                        )
                        with gr.Row():
                            traduci_testo_btn = gr.Button("📝 Traduci testo", variant="primary", size="lg", scale=1)
                            testo_status = gr.Textbox(label="", interactive=False, scale=2)
                        testo_output = gr.Textbox(label="Traduzione", lines=12, interactive=False)

    download_btn.click(
        fn=download_da_url,
        inputs=[url_input],
        outputs=[file_input, url_status],
    ).then(
        fn=info_file,
        inputs=[file_input],
        outputs=[file_info, preview_src],
    )

    file_input.change(
        fn=info_file,
        inputs=[file_input],
        outputs=[file_info, preview_src],
    )

    vram_radio.change(
        fn=lambda v: (filtra_modelli(v), v),
        inputs=[vram_radio],
        outputs=[modello_dropdown, stato_vram],
    )

    modello_dropdown.change(
        fn=ottieni_info_modello,
        inputs=[modello_dropdown],
        outputs=[info_modello],
    )

    translate_btn.click(
        fn=traduci_file,
        inputs=[file_input, src_lang, tgt_lang, ocr_lang, modello_dropdown,
                formato_output],
        outputs=[output_file, status_box, output_path, stato_traduzione],
    ).then(
        fn=lambda f: leggi_file(f.name)[:2000] if f else "",
        inputs=[file_input],
        outputs=[preview_src],
    ).then(
        fn=lambda t: t[:2000] if t else "",
        inputs=[stato_traduzione],
        outputs=[preview_tgt],
    )

    traduci_testo_btn.click(
        fn=traduci_testo_diretto,
        inputs=[testo_input, src_lang, tgt_lang, modello_dropdown],
        outputs=[testo_output, testo_status],
    )

    refresh_btn.click(
        fn=aggiorna_modelli_lista,
        outputs=[modello_dropdown],
    )

    pull_btn.click(
        fn=lambda nome: f"Scarica: ollama pull {nome}",
        inputs=[pull_name],
        outputs=[status_box],
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
        css=CSS,
    )
