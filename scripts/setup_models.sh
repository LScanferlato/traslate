#!/bin/bash
# Setup Modelli per Traduttore Ollama
# Utilizza Ollama installato localmente (senza Docker)

set -e

echo "=== Setup Modelli per Traduttore Ollama ==="
echo ""

# Modelli consigliati per traduzione
MODELLI_TRADUZIONE=("llama3.2:3b" "gemma2:2b" "qwen2.5:3b")
MODELLI_OTTICI=("llama3.2-vision:latest" "minicpm-v:latest")

# Verifica che Ollama sia raggiungibile
if ! ollama --version >/dev/null 2>&1; then
    echo "ERRORE: Ollama non trovato. Installalo da https://ollama.com"
    exit 1
fi

if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "ERRORE: Il servizio Ollama non è in esecuzione su localhost:11434."
    echo "Avvia Ollama con: ollama serve &"
    exit 1
fi

mostra_menu() {
    clear
    echo "╔══════════════════════════════════════════════════╗"
    echo "║       Setup Modelli - Traduttore IA Locale      ║"
    echo "╠══════════════════════════════════════════════════╣"
    echo "║ Ollama: $(ollama --version 2>/dev/null || echo '?')"
    echo "╠══════════════════════════════════════════════════╣"
    echo "║  1) Scarica modelli consigliati per traduzione  ║"
    echo "║     (llama3.2:3b, gemma2:2b, qwen2.5:3b)       ║"
    echo "║  2) Scarica modello singolo                     ║"
    echo "║  3) Elenca modelli già disponibili              ║"
    echo "║  4) Importa GGUF da HuggingFace                 ║"
    echo "║  5) Elimina un modello                          ║"
    echo "║  0) Esci                                        ║"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""
}

scarica_modello() {
    local nome=$1
    echo ""
    echo "📥 Scaricamento di $nome in corso..."
    ollama pull "$nome"
    if [ $? -eq 0 ]; then
        echo "✅ $nome scaricato con successo!"
    else
        echo "❌ Errore durante lo scaricamento di $nome"
    fi
}

scarica_consigliati() {
    echo ""
    echo "=== Modelli Consigliati per Traduzione ==="
    for m in "${MODELLI_TRADUZIONE[@]}"; do
        scarica_modello "$m"
        echo ""
    done
    echo "✅ Modelli consigliati scaricati!"
    echo ""
    echo "ℹ️  Puoi verificare con: ollama list"
}

modello_singolo() {
    echo ""
    read -p "Nome modello da scaricare (es. llama3.2:3b): " nome
    if [ -n "$nome" ]; then
        scarica_modello "$nome"
    fi
}

elenca_modelli() {
    echo ""
    echo "=== Modelli disponibili su Ollama ==="
    ollama list 2>/dev/null || echo "(nessun modello)"
    echo ""
}

importa_gguf() {
    echo ""
    echo "--- Importa modello GGUF da HuggingFace ---"
    echo "Esempio: mradermacher/translategemma-4b-it-GGUF"
    echo ""
    read -p "Repo HuggingFace (default: mradermacher/translategemma-4b-it-GGUF): " hf_repo
    hf_repo=${hf_repo:-mradermacher/translategemma-4b-it-GGUF}
    read -p "Nome per Ollama (default: translategemma:4b): " ollama_name
    ollama_name=${ollama_name:-translategemma:4b}
    echo ""
    echo "Importazione da hf.co/$hf_repo ..."
    ollama pull "hf.co/$hf_repo"
    if [ $? -eq 0 ]; then
        echo "✅ Modello $ollama_name importato con successo!"
    else
        echo "❌ Errore. Scarica manualmente il GGUF e usa:"
        echo "   ollama create $ollama_name -f /path/to/Modelfile"
    fi
}

elimina_modello() {
    echo ""
    echo "--- Modelli disponibili ---"
    ollama list
    echo ""
    read -p "Nome modello da eliminare: " nome
    if [ -n "$nome" ]; then
        ollama rm "$nome"
        echo "🗑️  $nome eliminato."
    fi
}

# Main loop
while true; do
    mostra_menu
    read -p "Scegli un'opzione (0-5): " scelta
    case $scelta in
        1) scarica_consigliati
           read -p "Premi INVIO per continuare..." ;;
        2) modello_singolo
           read -p "Premi INVIO per continuare..." ;;
        3) elenca_modelli
           read -p "Premi INVIO per continuare..." ;;
        4) importa_gguf
           read -p "Premi INVIO per continuare..." ;;
        5) elimina_modello
           read -p "Premi INVIO per continuare..." ;;
        0) echo ""
           echo "=== Setup completato! ==="
           echo "Avvia il traduttore con: python app/main.py"
           echo "Apri il browser su: http://localhost:7860"
           exit 0 ;;
        *) echo "Opzione non valida." ;;
    esac
done
