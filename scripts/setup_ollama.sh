#!/bin/bash
# Rilevamento e avvio di Ollama per il Traduttore Intelligente
# Priorita': 1) Ollama locale  2) Container Docker

set -e

OLLAMA_HOST="http://localhost:11434"
CONTAINER_NAME="ollama-translator"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}==========================================="
echo "  Traduttore Intelligente - Setup Ollama"
echo -e "===========================================${NC}"

# --- 1. Controlla Ollama locale ---
echo -e "\n${CYAN}>>> 1. Rilevamento Ollama sul sistema${NC}"
OLLAMA_LOCAL=false
if command -v ollama &>/dev/null; then
    echo -e "  ${GREEN}[OK]${NC} Ollama trovato: $(ollama --version)"
    OLLAMA_LOCAL=true
fi

if $OLLAMA_LOCAL; then
    echo -e "\n${CYAN}>>> 2. Verifica server Ollama${NC}"
    if curl -sf "$OLLAMA_HOST/api/tags" &>/dev/null; then
        echo -e "  ${GREEN}[OK]${NC} Ollama server attivo su $OLLAMA_HOST"
        export OLLAMA_HOST="$OLLAMA_HOST"
        exit 0
    else
        echo -e "  ${YELLOW}[!]${NC} Ollama installato ma server non attivo. Avvio..."
        ollama serve &
        sleep 3
        if curl -sf "$OLLAMA_HOST/api/tags" &>/dev/null; then
            echo -e "  ${GREEN}[OK]${NC} Ollama server avviato"
            export OLLAMA_HOST="$OLLAMA_HOST"
            exit 0
        else
            echo -e "  ${RED}[ERR]${NC} Impossibile avviare Ollama"
        fi
    fi
fi

# --- 3. Fallback Docker ---
echo -e "\n${CYAN}>>> 3. Fallback: ricerca Docker${NC}"
DOCKER_AVAILABLE=false
if command -v docker &>/dev/null; then
    echo -e "  ${GREEN}[OK]${NC} Docker trovato: $(docker --version)"
    DOCKER_AVAILABLE=true
fi

if ! $DOCKER_AVAILABLE; then
    echo -e "  ${RED}[ERR]${NC} Nessuna installazione di Ollama o Docker rilevata."
    echo -e "\n${YELLOW}Installa Ollama: https://ollama.com${NC}"
    echo -e "${YELLOW}Oppure Docker: https://docker.com${NC}"
    exit 1
fi

# --- 4. Avvia container Ollama ---
echo -e "\n${CYAN}>>> 4. Avvio container Ollama via Docker${NC}"
if docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" 2>/dev/null | grep -q "$CONTAINER_NAME"; then
    echo -e "  ${GREEN}[OK]${NC} Container Ollama gia' in esecuzione"
elif docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Names}}" 2>/dev/null | grep -q "$CONTAINER_NAME"; then
    echo -e "  ${YELLOW}[!]${NC} Container fermo. Avvio..."
    docker start "$CONTAINER_NAME"
else
    echo -e "  ${YELLOW}[!]${NC} Creazione container..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        -v ollama_data:/root/.ollama \
        -v "$(pwd)/models:/models" \
        -p 11434:11434 \
        ollama/ollama:latest
fi

# --- 5. Attesa ready ---
echo -e "\n${CYAN}>>> 5. Attesa che Ollama sia pronto...${NC}"
for i in $(seq 1 30); do
    if curl -sf "http://localhost:11434/api/tags" &>/dev/null; then
        echo -e "  ${GREEN}[OK]${NC} Ollama pronto (http://localhost:11434)"
        export OLLAMA_HOST="http://localhost:11434"
        exit 0
    fi
    sleep 2
done

echo -e "  ${RED}[ERR]${NC} Timeout dopo 60 secondi"
echo "Verifica: docker logs $CONTAINER_NAME"
export OLLAMA_HOST="http://localhost:11434"
