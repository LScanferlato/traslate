param(
    [string]$OllamaHost = "http://localhost:11434",
    [string]$ContainerName = "ollama-translator"
)

function Write-Step($msg) { Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-OK($msg)    { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "  [ERR] $msg" -ForegroundColor Red }

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  Traduttore Intelligente - Setup Ollama" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# --- 1. Controlla se Ollama e' gia' installato localmente ---
Write-Step "1. Rilevamento Ollama sul sistema"

$ollamaLocal = $false
try {
    $v = & ollama --version 2>$null
    if ($LASTEXITCODE -eq 0 -and $v) {
        Write-OK "Ollama trovato: $v"
        $ollamaLocal = $true
    }
} catch {}

if (-not $ollamaLocal) {
    Write-Warn "Ollama non trovato nel PATH"
    $ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $ollamaPath) {
        Write-OK "Ollama trovato in: $ollamaPath"
        $env:Path += ";$env:LOCALAPPDATA\Programs\Ollama"
        $ollamaLocal = $true
    }
}

# --- 2. Se Ollama e' locale, verifica che sia in esecuzione ---
if ($ollamaLocal) {
    Write-Step "2. Verifica che Ollama sia in esecuzione"
    try {
        $r = Invoke-WebRequest -Uri "$OllamaHost/api/tags" -TimeoutSec 5 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            Write-OK "Ollama server attivo su $OllamaHost"
            $env:OLLAMA_HOST = $OllamaHost
            return
        }
    } catch {
        Write-Warn "Ollama installato ma server non attivo. Avvio Ollama..."
        try {
            $ollamaExe = if (Test-Path "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe") {
                "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
            } else { "ollama" }
            Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
            Write-OK "Ollama server avviato in background"
            Start-Sleep -Seconds 3
            $env:OLLAMA_HOST = $OllamaHost
            return
        } catch {
            Write-Err "Impossibile avviare Ollama: $_"
        }
    }
}

# --- 3. Fallback: prova con Docker ---
Write-Step "3. Fallback: ricerca Docker"

$dockerAvailable = $false
try {
    $dv = & docker --version 2>$null
    if ($LASTEXITCODE -eq 0 -and $dv) {
        Write-OK "Docker trovato: $dv"
        $dockerAvailable = $true
    }
} catch {}

if (-not $dockerAvailable) {
    Write-Err "Nessuna installazione di Ollama o Docker rilevata."
    Write-Host ""
    Write-Host "Per utilizzare questo traduttore, installa:" -ForegroundColor Yellow
    Write-Host "  Opzione A (consigliata): Installa Ollama da https://ollama.com" -ForegroundColor Green
    Write-Host "  Opzione B: Installa Docker Desktop da https://docker.com" -ForegroundColor Green
    Write-Host ""
    Write-Host "Dopo aver installato Ollama, esegui:" -ForegroundColor White
    Write-Host "  ollama serve" -ForegroundColor Gray
    Write-Host "  ollama pull llama3.2:3b" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Poi avvia il traduttore con: python app/main.py" -ForegroundColor Gray
    exit 1
}

# --- 4. Avvia container Ollama ---
Write-Step "4. Avvio container Ollama via Docker"

$containerExists = & docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
if ($containerExists) {
    $containerRunning = & docker ps --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
    if ($containerRunning) {
        Write-OK "Container Ollama gia' in esecuzione"
    } else {
        Write-Warn "Container fermo. Avvio..."
        & docker start $ContainerName
        Write-OK "Container avviato"
    }
} else {
    Write-Warn "Container non trovato. Creazione in corso..."
    & docker run -d `
        --name $ContainerName `
        -v ollama_data:/root/.ollama `
        -v "${PSScriptRoot}\..\models:/models" `
        -p 11434:11434 `
        ollama/ollama:latest
    Write-OK "Container creato e avviato"
}

# Attesa che Ollama sia pronto
Write-Step "5. Attesa che Ollama sia pronto..."
$maxRetry = 30
for ($i = 0; $i -lt $maxRetry; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            Write-OK "Ollama pronto (http://localhost:11434)"
            $env:OLLAMA_HOST = "http://localhost:11434"
            return
        }
    } catch {}
    Start-Sleep -Seconds 2
}
Write-Err "Timeout: Ollama non risponde dopo 60 secondi"
Write-Host "Verifica manuale: docker logs $ContainerName"

# Esporta host per l'app
$env:OLLAMA_HOST = "http://localhost:11434"
