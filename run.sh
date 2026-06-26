#!/bin/bash
# Avvio Traduttore Intelligente con IA Locale

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"
VENV_DIR="$SCRIPT_DIR/.venv"
ENV_FILE="$SCRIPT_DIR/.env"

# Colori
ROSSO='\033[0;31m'
VERDE='\033[0;32m'
GIALLO='\033[1;33m'
CIANO='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CIANO}╔════════════════════════════════════════════╗${NC}"
echo -e "${CIANO}║    Traduttore Intelligente con IA Locale   ║${NC}"
echo -e "${CIANO}╚════════════════════════════════════════════╝${NC}"
echo ""

# 1. Verifica Python
echo -e "${GIALLO}[1/4]${NC} Verifica Python..."
if ! command -v python3 &>/dev/null; then
    echo -e "${ROSSO}ERRORE: python3 non trovato.${NC}"
    exit 1
fi
echo -e "     Python $(python3 --version)"

# 2. Ambiente virtuale e dipendenze
echo -e "${GIALLO}[2/4]${NC} Ambiente virtuale e dipendenze..."
if [ ! -d "$VENV_DIR" ]; then
    echo "     Creazione ambiente virtuale..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

if [ ! -f "$APP_DIR/requirements.txt" ]; then
    echo -e "${ROSSO}ERRORE: requirements.txt non trovato in $APP_DIR${NC}"
    exit 1
fi

echo "     Installazione dipendenze..."
pip install -q --upgrade pip
pip install -q -r "$APP_DIR/requirements.txt"
echo -e "     ${VERDE}OK${NC}"

# 3. Verifica Ollama
echo -e "${GIALLO}[3/4]${NC} Verifica Ollama..."
if ! command -v ollama &>/dev/null; then
    echo -e "${ROSSO}ERRORE: Ollama non installato.${NC}"
    echo "     Installalo da: https://ollama.com/download"
    exit 1
fi

if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${GIALLO}     Servizio Ollama non attivo. Avvio...${NC}"
    ollama serve >/dev/null 2>&1 &
    sleep 3
    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "${ROSSO}ERRORE: impossibile avviare Ollama.${NC}"
        echo "     Avvia manualmente: ollama serve &"
        exit 1
    fi
fi
echo -e "     $(ollama --version 2>/dev/null) — servizio attivo"

# Controlla modelli disponibili
MODELLI=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
if [ "$MODELLI" -eq 0 ]; then
    echo -e "${GIALLO}     ⚠️  Nessun modello disponibile.${NC}"
    echo "     Esegui: ./scripts/setup_models.sh"
elif ! ollama list 2>/dev/null | grep -qE "llama3\.2:3b|gemma2:2b|qwen2\.5:3b"; then
    echo -e "${GIALLO}     ⚠️  Nessun modello di traduzione trovato.${NC}"
    echo "     Esegui: ./scripts/setup_models.sh  (opzione 1)"
fi

# 4. Carica .env
echo -e "${GIALLO}[4/4]${NC} Carica configurazione..."
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo -e "     OLLAMA_HOST=$OLLAMA_HOST"
else
    export OLLAMA_HOST=${OLLAMA_HOST:-http://localhost:11434}
    echo -e "     ${GIALLO}.env non trovato, default: OLLAMA_HOST=$OLLAMA_HOST${NC}"
fi

echo ""
echo -e "${VERDE}✅ Pronto! Avvio interfaccia web...${NC}"
echo -e "${CIANO}   Apri il browser su: http://localhost:7860${NC}"
echo ""

# Avvia l'app
python3 "$APP_DIR/main.py"
