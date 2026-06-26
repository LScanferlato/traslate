#!/bin/bash
# Setup modelli per Traduttore Ollama

set -e

echo "=== Setup Modelli per Traduttore Ollama ==="

# Modelli consigliati
RECOMMENDED=("llama3.2:3b" "gemma2:2b" "qwen2.5:3b")

echo ""
echo "Modelli consigliati da scaricare:"
for m in "${RECOMMENDED[@]}"; do
  echo "  - $m"
done

read -p "Scaricare i modelli consigliati? (s/N): " choice
if [ "$choice" = "s" ]; then
  for m in "${RECOMMENDED[@]}"; do
    echo "Scaricamento di $m in corso..."
    docker exec -it ollama-translator ollama pull "$m"
  done
fi

# Importa modello GGUF da HuggingFace
echo ""
echo "--- Importa modello GGUF da HuggingFace ---"
echo "Esempio: mradermacher/translategemma-4b-it-GGUF"
read -p "Importare il modello? (s/N): " import_choice

if [ "$import_choice" = "s" ]; then
  read -p "Nome repo HuggingFace (default: mradermacher/translategemma-4b-it-GGUF): " hf_repo
  hf_repo=${hf_repo:-mradermacher/translategemma-4b-it-GGUF}

  read -p "Nome per Ollama (default: translategemma:4b): " ollama_name
  ollama_name=${ollama_name:-translategemma:4b}

  echo "Importazione del modello tramite 'ollama pull hf.co/$hf_repo'..."
  docker exec -it ollama-translator ollama pull "hf.co/$hf_repo"

  if [ $? -eq 0 ]; then
    echo "Modello $ollama_name importato con successo!"
  else
    echo "Errore. Scarica manualmente il GGUF e usa:"
    echo "  docker exec -it ollama-translator ollama create $ollama_name -f /models/Modelfile"
  fi
fi

echo ""
echo "=== Setup completato! ==="
echo "Avvia il traduttore con: docker-compose up -d"
echo "Apri il browser su: http://localhost:7860"
