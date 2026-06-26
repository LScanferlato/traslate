import requests
import json

MODELLI_DISPONIBILI = {
    "llama3.2:1b":     {"vram_gb": 1.3, "vram_max": 2.0, "desc": "Meta Llama 3.2 1B – ultra leggero, ideale per test"},
    "qwen2.5:0.5b":    {"vram_gb": 0.5, "vram_max": 1.0, "desc": "Qwen 2.5 0.5B – modello pi\u00f9 piccolo disponibile"},
    "gemma2:2b":       {"vram_gb": 1.6, "vram_max": 3.0, "desc": "Google Gemma 2 2B – buona qualit\u00e0, dimensioni ridotte"},
    "phi3:mini":       {"vram_gb": 2.3, "vram_max": 4.0, "desc": "Phi-3 Mini 3.8B – eccellente rapporto qualit\u00e0/dimensione"},
    "llama3.2:3b":     {"vram_gb": 2.5, "vram_max": 4.0, "desc": "Meta Llama 3.2 3B – ottimo per traduzione"},
    "qwen2.5:3b":      {"vram_gb": 2.5, "vram_max": 4.0, "desc": "Qwen 2.5 3B – performante e veloce"},
    "translategemma:4b": {"vram_gb": 3.0, "vram_max": 5.0, "desc": "TranslateGemma 4B – specializzato in traduzione"},
    "llama3.1:8b":     {"vram_gb": 5.5, "vram_max": 8.0, "desc": "Meta Llama 3.1 8B – ottimo equilibrio qualit\u00e0/risorse"},
    "gemma2:9b":       {"vram_gb": 6.0, "vram_max": 9.0, "desc": "Google Gemma 2 9B – traduzione di alta qualit\u00e0"},
    "mistral:7b":      {"vram_gb": 5.0, "vram_max": 8.0, "desc": "Mistral 7B – molto popolare per traduzione"},
    "qwen2.5:7b":      {"vram_gb": 5.5, "vram_max": 8.0, "desc": "Qwen 2.5 7B – versatile e potente"},
    "deepseek-r1:8b":  {"vram_gb": 5.5, "vram_max": 8.0, "desc": "DeepSeek R1 8B – ottimo per testi tecnici"},
    "llama3.3:70b":    {"vram_gb": 24.0, "vram_max": 36.0, "desc": "Meta Llama 3.3 70B – qualit\u00e0 professionale"},
    "qwen2.5:14b":     {"vram_gb": 10.0, "vram_max": 14.0, "desc": "Qwen 2.5 14B – alta qualit\u00e0"},
    "qwen2.5:32b":     {"vram_gb": 22.0, "vram_max": 32.0, "desc": "Qwen 2.5 32B – qualit\u00e0 molto elevata"},
    "deepseek-r1:14b": {"vram_gb": 10.0, "vram_max": 14.0, "desc": "DeepSeek R1 14B – buona qualit\u00e0"},
    "deepseek-r1:32b": {"vram_gb": 22.0, "vram_max": 32.0, "desc": "DeepSeek R1 32B – qualit\u00e0 elevata"},
    "mixtral:8x7b":    {"vram_gb": 12.0, "vram_max": 18.0, "desc": "Mixtral 8x7B – modello mistral potente"},
    "command-r:35b":   {"vram_gb": 24.0, "vram_max": 36.0, "desc": "Cohere Command R 35B – eccellente per traduzione"},
    "command-r:104b":  {"vram_gb": 60.0, "vram_max": 999.0, "desc": "Cohere Command R+ 104B – il pi\u00f9 potente"},
}

OPZIONI_VRAM = [("1 GB", 1), ("2 GB", 2), ("4 GB", 4), ("8 GB", 8),
                ("10 GB", 10), ("12 GB", 12), ("16 GB", 16),
                ("24 GB", 24), ("32 GB", 32), ("48 GB", 48)]

class OllamaTranslator:
    def __init__(self, host="http://ollama:11434"):
        self.host = host
        self.api_generate = f"{host}/api/generate"
        self.api_tags = f"{host}/api/tags"
        self.api_pull = f"{host}/api/pull"

    def lista_modelli(self):
        try:
            r = requests.get(self.api_tags, timeout=5)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except:
            pass
        return []

    def scarica_modello(self, nome_modello):
        r = requests.post(self.api_pull, json={"name": nome_modello}, stream=True, timeout=600)
        for linea in r.iter_lines():
            if linea:
                yield json.loads(linea)

    def traduci(self, testo, lingua_sorgente, lingua_target, modello="translategemma:latest"):
        prompt = (
            f"Traduci il seguente testo da {lingua_sorgente} a {lingua_target}.\n"
            f"Restituisci SOLO la traduzione, senza spiegazioni, commenti o prefazioni.\n\n"
            f"Testo:\n{testo}"
        )
        payload = {
            "model": modello,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        r = requests.post(self.api_generate, json=payload, timeout=600)
        if r.status_code == 200:
            return r.json().get("response", "").strip()
        raise Exception(f"Errore Ollama ({r.status_code}): {r.text}")

def modelli_per_vram(vram_gb):
    return [
        (f"{nome}  ~{info['vram_gb']}GB  {info['desc']}", nome)
        for nome, info in sorted(MODELLI_DISPONIBILI.items(), key=lambda x: x[1]["vram_gb"])
        if info["vram_gb"] <= vram_gb
    ]

def modelli_senza_filtro():
    return [
        (f"{nome}  ~{info['vram_gb']}GB  {info['desc']}", nome)
        for nome, info in sorted(MODELLI_DISPONIBILI.items(), key=lambda x: x[1]["vram_gb"])
    ]
