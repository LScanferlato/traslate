param(
    [string]$ModelName = "mradermacher/translategemma-4b-it-GGUF",
    [string]$OllamaName = "translategemma:4b"
)

Write-Host "=== Setup Modelli per Traduttore Ollama ===" -ForegroundColor Cyan

# 1. Pull modelli consigliati da Ollama Library
$recommended = @(
    "llama3.2:3b",
    "gemma2:2b",
    "qwen2.5:3b"
)

Write-Host "`nModelli consigliati da scaricare:" -ForegroundColor Yellow
foreach ($m in $recommended) {
    Write-Host "  - $m"
}

$choice = Read-Host "`nScaricare i modelli consigliati? (s/N)"
if ($choice -eq "s") {
    foreach ($m in $recommended) {
        Write-Host "`nScaricamento di $m in corso..." -ForegroundColor Green
        docker exec -it ollama-translator ollama pull $m
    }
}

# 2. Opzione: importa modello GGUF da HuggingFace
Write-Host "`n--- Importa modello GGUF da HuggingFace ---" -ForegroundColor Cyan
Write-Host "Modello di default: $ModelName → $OllamaName"

$importChoice = Read-Host "`nImportare il modello GGUF? (s/N)"
if ($importChoice -eq "s") {
    $ggufFile = "$PSScriptRoot\..\models\$OllamaName.gguf"
    $modelfile = "$PSScriptRoot\..\models\Modelfile"

    Write-Host "Scaricamento del file GGUF..." -ForegroundColor Green
    # Usa ollama per importare direttamente da HuggingFace
    docker exec -it ollama-translator ollama pull hf.co/$ModelName

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Modello $OllamaName importato con successo!" -ForegroundColor Green
    } else {
        Write-Host "Errore nell'importazione. Scarica manualmente il GGUF da:" -ForegroundColor Red
        Write-Host "  https://huggingface.co/$ModelName"
        Write-Host "Poi usa: docker exec -it ollama-translator ollama create $OllamaName -f /models/Modelfile"
    }
}

Write-Host "`n=== Setup completato! ===" -ForegroundColor Cyan
Write-Host "Avvia il traduttore con: docker-compose up -d" -ForegroundColor Green
Write-Host "Apri il browser su: http://localhost:7860" -ForegroundColor Green
