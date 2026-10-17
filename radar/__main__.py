import os
from datetime import timedelta
import sys
from pathlib import Path

from radar.fuentes import descargar, lead_de, leer_medio
from radar.horario import ahora_cot
from radar.principal import ejecutar

def mesas() -> None:
    from radar import mesas as m
    clave = os.environ["GEMINI_API_KEY"]
    raiz = Path(__file__).resolve().parent.parent
    prueba = int(os.environ.get("PRUEBA_MINUTOS") or 0)
    if prueba:  # modo prueba: graba ya, en tramos de 5 minutos, durante `prueba` minutos
        ahora = ahora_cot()
        fin = ahora + timedelta(minutes=prueba)
        m.INICIO, m.FIN, m.TRAMO = (ahora.hour, ahora.minute), (fin.hour, fin.minute), 300
    m.correr(raiz / "docs", ahora_cot, m.grabar, lambda audio, prompt: m.gemini(audio, prompt, clave))
    print("Mesas al aire: listo")

def main() -> None:
    if sys.argv[1:] == ["mesas"]:
        return mesas()
    # GitHub Models se retiró el 30-jul-2026: por ahora se clasifica solo con palabras clave.
    llamar = None
    raiz = Path(__file__).resolve().parent.parent
    r = ejecutar(ahora_cot(), raiz / "data", raiz / "docs", leer_medio, lambda url: lead_de(descargar(url, 15)), llamar)
    print(f"Nuevas: {r['nuevas']} · Clasificación: {r['modo']} · Avisos: {r['avisos'] or 'ninguno'}")

if __name__ == "__main__":
    main()
