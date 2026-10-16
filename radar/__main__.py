from pathlib import Path

from radar.fuentes import descargar, lead_de, leer_medio
from radar.horario import ahora_cot
from radar.principal import ejecutar

def main() -> None:
    # GitHub Models se retiró el 30-jul-2026: por ahora se clasifica solo con palabras clave.
    llamar = None
    raiz = Path(__file__).resolve().parent.parent
    r = ejecutar(ahora_cot(), raiz / "data", raiz / "docs", leer_medio, lambda url: lead_de(descargar(url, 15)), llamar)
    print(f"Nuevas: {r['nuevas']} · Clasificación: {r['modo']} · Avisos: {r['avisos'] or 'ninguno'}")

if __name__ == "__main__":
    main()
