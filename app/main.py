import os
import gradio as gr
from utils import leggi_file, scrivi_traduzione, LINGUE_SUPPORTATE, LINGUE_OCR, FORMATI_SUPPORTATI
from translator import OllamaTranslator, modelli_per_vram, modelli_senza_filtro, OPZIONI_VRAM, MODELLI_DISPONIBILI
from pdf_handler import rileva_tipo_pdf, estrai_blocchi_testuali

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
traduttore = OllamaTranslator(host=OLLAMA_HOST)

CSS = """
.app-header { display:flex; align-items:center; gap:14px; padding:16px 0 12px; border-bottom:2px solid #e5e7eb; margin-bottom:20px }
.app-header .icon { background:linear-gradient(135deg,#2563eb,#7c3aed); border-radius:14px; width:52px; height:52px; display:flex; align-items:center; justify-content:center; font-size:26px; color:white; flex-shrink:0 }
.app-header .title { font-size:22px; font-weight:700; color:#1e293b; letter-spacing:-0.5px; line-height:1.2 }
.app-header .subtitle { font-size:13px; color:#64748b }
.label-section { font-size:12px; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin:16px 0 8px }
.badge-pdf { display:inline-block; background:#dbeafe; color:#1d4ed8; font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px; margin-left:6px }
"""

def aggiorna_modelli_lista():
    return gr.Dropdown(choices=modelli_senza_filtro() or [], value=None)

def filtra_modelli(vram_gb):
    return gr.Dropdown(choices=modelli_per_vram(vram_gb), value=None)

def traduci_file(file, codice_src, codice_tgt, codice_ocr, modello_selezionato,
                  modalita_pdf, mostra_bilingue):
    if file is None:
        return None, "Nessun file caricato.", "", None
    if not modello_selezionato:
        return None, "Seleziona un modello.", "", None
    try:
        lingua_ocr_full = f"{codice_ocr}+eng" if codice_ocr else "ita+eng"

        testo = leggi_file(file.name, lingua_ocr=lingua_ocr_full)
        if not testo.strip():
            return None, "Nessun testo estratto. Verifica che il file non sia vuoto.", "", None

        traduzione = traduttore.traduci(
            testo,
            LINGUE_SUPPORTATE[codice_src],
            LINGUE_SUPPORTATE[codice_tgt],
            modello=modello_selezionato,
        )

        if mostra_bilingue and file.name.lower().endswith(".pdf"):
            percorso_out = scrivi_traduzione(
                traduzione, file.name, "/app/output", codice_tgt,
                modalita_pdf=modalita_pdf,
            )
        else:
            from utils import _scrivi_testo
            percorso_out = _scrivi_testo(
                traduzione, file.name, "/app/output", f"tradotto_{codice_tgt}"
            )

        return percorso_out, "Traduzione completata con successo!", f"{percorso_out}", traduzione
    except Exception as e:
        return None, f"Errore: {e}", "", ""

def ottieni_info_modello(modello_nome):
    if modello_nome and modello_nome in MODELLI_DISPONIBILI:
        info = MODELLI_DISPONIBILI[modello_nome]
        return f"**{modello_nome}**  \n{info['desc']}  \nVRAM richiesta: ~{info['vram_gb']} GB"
    return "Seleziona un modello per vedere i dettagli."

def info_file(file):
    if file is None:
        return "", "", gr.update(visible=False)
    nome = file.name.lower()
    if nome.endswith(".pdf"):
        tipo = rileva_tipo_pdf(file.name)
        tipo_label = {"testo": "PDF con layer di testo", "scansionato": "PDF scansionato (OCR)", "misto": "PDF misto"}.get(tipo, tipo)
        pagine = estrai_blocchi_testuali(file.name)
        tot_caratteri = sum(len(b["testo"]) for p in pagine for b in p)
        return f"**{os.path.basename(file.name)}**  \n{tipo_label} | {len(pagine)} pagine | ~{tot_caratteri} caratteri", "", gr.update(visible=True)
    else:
        return f"**{os.path.basename(file.name)}**", "", gr.update(visible=False)

with gr.Blocks(
    title="Traduttore Intelligente con IA Locale",
    theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
    css=CSS,
) as demo:
    gr.HTML("""
    <div class="app-header">
      <div class="icon">🌐</div>
      <div>
        <div class="title">Traduttore Intelligente</div>
        <div class="subtitle">Traduzione locale con IA — Ollama + OCR + layout PDF preservato</div>
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
                        container=True,
                    )
                modello_dropdown = gr.Dropdown(
                    choices=modelli_per_vram(8),
                    label="Modello di traduzione",
                    interactive=True,
                    value=None,
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

            gr.HTML("<div class='label-section'>Lingue e formati</div>")
            with gr.Group():
                src_lang = gr.Dropdown(
                    choices=[(v, k) for k, v in LINGUE_SUPPORTATE.items()],
                    label="Lingua originale",
                    value="ita",
                )
                tgt_lang = gr.Dropdown(
                    choices=[(v, k) for k, v in LINGUE_SUPPORTATE.items()],
                    label="Lingua target",
                    value="eng",
                )
                ocr_lang = gr.Dropdown(
                    choices=[(v, k) for k, v in LINGUE_OCR.items()],
                    label="Lingua OCR (per PDF scansionati)",
                    value="ita",
                )
                gr.Markdown(
                    "Formati supportati: "
                    + ", ".join(f"`{k.upper()}`" for k in sorted(FORMATI_SUPPORTATI.keys()))
                )

            gr.HTML("<div class='label-section'>Output PDF</div>")
            with gr.Group():
                mostra_bilingue = gr.Checkbox(
                    label="Crea PDF bilingue con layout preservato",
                    value=True,
                )
                modalita_pdf = gr.Radio(
                    choices=[("Affiancato (originale + traduzione)", "bilingue"),
                             ("Solo traduzione (monolingue)", "mono")],
                    label="Modalità PDF bilingue",
                    value="bilingue",
                    visible=True,
                )
                mostra_bilingue.change(
                    fn=lambda v: gr.update(visible=v),
                    inputs=[mostra_bilingue],
                    outputs=[modalita_pdf],
                )

        with gr.Column(scale=2):
            gr.HTML("<div class='label-section'>Carica e traduci</div>")
            with gr.Group():
                file_input = gr.File(
                    label="Carica file",
                    file_types=list(FORMATI_SUPPORTATI.keys()),
                )
                file_info = gr.Markdown(value="")
                translate_btn = gr.Button("🚀 Traduci", variant="primary", size="lg")
                with gr.Row():
                    output_file = gr.File(label="Scarica traduzione")
                    output_path = gr.Textbox(label="Percorso file", interactive=False)
                status_box = gr.Textbox(label="Stato", interactive=False)

            gr.HTML("<div class='label-section'>Anteprima testo</div>")
            with gr.Row():
                with gr.Column():
                    preview_src = gr.Textbox(label="Originale (prime righe)", lines=6, interactive=False)
                with gr.Column():
                    preview_tgt = gr.Textbox(label="Tradotto (prime righe)", lines=6, interactive=False)

    file_input.change(
        fn=info_file,
        inputs=[file_input],
        outputs=[file_info, preview_src, mostra_bilingue],
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
                modalita_pdf, mostra_bilingue],
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

    refresh_btn.click(
        fn=aggiorna_modelli_lista,
        outputs=[modello_dropdown],
    )

    pull_btn.click(
        fn=lambda nome: f"Scarica '{nome}' con: docker exec -it ollama-translator ollama pull {nome}",
        inputs=[pull_name],
        outputs=[status_box],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
