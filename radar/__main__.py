import os
from pathlib import Path

from radar.clasificador import llamar_github_models
from radar.fuentes import descargar, lead_de, leer_medio
from radar.horario import ahora_cot
from radar.principal import ejecutar

def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    llamar = (lambda mensajes: llamar_github_models(mensajes, token)) if token else None
    raiz = Path(__file__).resolve().parent.parent
    r = ejecutar(ahora_cot(), raiz / "data", raiz / "docs", leer_medio, lambda url: lead_de(descargar(url, 15)), llamar)
    print(f"Nuevas: {r['nuevas']} · Clasificación: {r['modo']} · Avisos: {r['avisos'] or 'ninguno'}")

if __name__ == "__main__":
    main()
