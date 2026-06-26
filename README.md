# Traduttore Intelligente con IA Locale

[![Licenza: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Ollama](https://img.shields.io/badge/Ollama-0.30%2B-green)

Piattaforma di traduzione automatica locale che opera interamente su hardware consumer, senza dipendenze da servizi cloud. Supporta oltre 15 lingue e molteplici formati documentali con preservazione del layout.

---

## Architettura

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────┐
│   Input      │────▶│  Estrattore      │────▶│  Ollama (LLM) │
│  (PDF/DOCX/  │     │  Testo           │     │  locale       │
│   TXT/...)   │     │  (OCR + parser)  │     │  (HTTP API)   │
└──────────────┘     └──────────────────┘     └───────┬───────┘
                                                      │
                                                      ▼
┌──────────────┐     ┌──────────────────┐     ┌───────────────┐
│   Output     │◀────│  Renderer        │◀────│  Traduzione   │
│  (PDF/HTML/  │     │  (layout +       │     │  +           │
│   TXT/...)   │     │   preservazione) │     │  Ricostruzione│
└──────────────┘     └──────────────────┘     └───────────────┘
```

### Componenti

| Modulo | Descrizione |
|---|---|
| `app/main.py` | Interfaccia Gradio (web UI) |
| `app/translator.py` | Client API Ollama e catalogo modelli |
| `app/utils.py` | Lettura/scrittura multiformato (16 formati) |
| `app/pdf_handler.py` | Estrazione testo strutturato da PDF (PyMuPDF + Tesseract OCR) |
| `app/pdf_renderer.py` | Ricostruzione PDF bilingue con layout preservato |

---

## Requisiti

- **Sistema**: Linux, macOS o WSL2 su Windows
- **Python**: 3.11 o superiore
- **Ollama**: v0.30+ ([installazione](https://ollama.com/download))
- **Tesseract**: per OCR su PDF scansionati
- **GPU** (opzionale, ma raccomandata): NVIDIA con driver CUDA per accelerazione

### Dipendenze Python

```
gradio==4.44.1          Web UI interattiva
PyMuPDF>=1.24.0         Elaborazione PDF
pytesseract>=0.3.13     OCR (riconoscimento testo)
pdf2image>=1.17.0       Conversione PDF → immagini
python-docx>=1.1.2      Lettura/scrittura DOCX
openpyxl>=3.1.5         Lettura/scrittura XLSX
python-pptx>=0.6.23     Lettura PPTX
odfpy>=1.4.1            Lettura ODT
```

---

## Installazione

### 1. Clona e configura

```bash
git clone <repo-url>
cd traslate-main
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
```

### 2. Verifica Ollama

```bash
ollama serve &                  # avvia il servizio (se non è in esecuzione)
ollama --version                # deve restituire v0.30+
```

### 3. Scarica i modelli di traduzione (consigliati)

```bash
chmod +x scripts/setup_models.sh
./scripts/setup_models.sh       # menu interattivo → opzione 1
```

I modelli consigliati per traduzione sono:

| Modello | Parametri | VRAM | Qualità |
|---|---|---|---|
| `llama3.2:3b` | 3B | ~2.5 GB | Ottima |
| `gemma2:2b` | 2B | ~1.6 GB | Buona |
| `qwen2.5:3b` | 3B | ~2.5 GB | Ottima |

### 4. Avvia l'applicazione

```bash
python app/main.py
```

Apri il browser su [http://localhost:7860](http://localhost:7860).

---

## Formati supportati

| Formato | Lettura | Scrittura | OCR | Layout preservato |
|---|---|---|---|---|
| `.txt` | ✅ | ✅ | — | — |
| `.pdf` | ✅ | ✅ | ✅ | ✅ |
| `.docx` | ✅ | ✅ | — | — |
| `.xlsx` / `.xls` | ✅ | ✅ | — | — |
| `.csv` | ✅ | ✅ | — | — |
| `.pptx` | ✅ | — | — | — |
| `.odt` | ✅ | — | — | — |
| `.srt` / `.vtt` | ✅ | ✅ | — | — |
| `.html` / `.htm` | ✅ | — | — | — |
| `.md` | ✅ | — | — | — |
| `.json` / `.xml` | ✅ | — | — | — |

---

## Modelli disponibili

Il sistema supporta oltre 20 modelli Ollama, selezionabili in base alla VRAM disponibile:

| VRAM | Modelli consigliati |
|---|---|
| 1-2 GB | `llama3.2:1b`, `qwen2.5:0.5b` |
| 2-4 GB | `gemma2:2b`, `phi3:mini`, `llama3.2:3b`, `qwen2.5:3b` |
| 4-8 GB | `llama3.1:8b`, `gemma2:9b`, `mistral:7b`, `qwen2.5:7b` |
| 8-16 GB | `qwen2.5:14b`, `deepseek-r1:14b` |
| 16-32 GB | `qwen2.5:32b`, `deepseek-r1:32b`, `llama3.3:70b` |
| 32+ GB | `command-r:35b`, `mixtral:8x7b`, `command-r:104b` |

---

## OCR (Riconoscimento ottico dei caratteri)

Per PDF scansionati (immagini), il sistema utilizza **Tesseract OCR** con supporto per 8 lingue:

Italiano, Inglese, Francese, Spagnolo, Tedesco, Portoghese, Russo, Olandese

Il rilevamento automatico distingue tra:
- **PDF con testo**: estrazione diretta del layer testuale
- **PDF scansionati**: OCR su ogni pagina
- **PDF misti**: OCR solo sulle pagine senza testo

---

## Output PDF bilingue

Il renderer supporta tre modalità:

1. **Affiancato** — originale a sinistra, traduzione a destra (default)
2. **Sovrapposto** — traduzione sovrapposta all'originale
3. **Monolingue** — solo traduzione

Viene generato anche un file HTML bilingue per anteprima nel browser.

---

## Struttura del progetto

```
traslate-main/
├── app/
│   ├── main.py             # Interfaccia web (Gradio)
│   ├── translator.py       # Client Ollama + catalogo modelli
│   ├── utils.py            # Lettura/scrittura multiformato
│   ├── pdf_handler.py      # Estrazione testo da PDF
│   ├── pdf_renderer.py     # Renderer PDF bilingue
│   └── requirements.txt    # Dipendenze Python
├── scripts/
│   ├── setup_models.sh     # Script setup modelli (Linux/macOS)
│   └── setup_models.ps1    # Script setup modelli (Windows)
├── input/                  # Directory input (montata nel container)
├── output/                 # Directory output
├── models/                 # Modelli GGUF personalizzati
├── docker-compose.yml      # Deployment Docker
├── Dockerfile              # Immagine Docker
├── .env                    # Configurazione
└── .env.example            # Esempio configurazione
```

---

## Licenza

Distribuito sotto licenza MIT. Vedi [LICENSE](LICENSE) per maggiori dettagli.
