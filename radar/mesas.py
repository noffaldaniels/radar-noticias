"""Mesas de la mañana al aire: graba las 3 radios de 5:30 a 9:00 en tramos de 10 minutos,
Gemini saca lo clave de cada tramo y se publica en docs/mesas-AAAA-MM-DD.json (la página lo lee sola)."""
import json
import re
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

from radar.reglas import PALABRAS, texto_plano

EMISORAS = {
    "Blu Radio": ("Mañanas Blu", "https://playerservices.streamtheworld.com/api/livestream-redirect/BLURADIO_ADP.aac"),
    "Caracol Radio": ("6AM con Julio Sánchez Cristo", "https://playerservices.streamtheworld.com/api/livestream-redirect/CARACOL_RADIOAAC.aac"),
    "La FM": ("Noticias La FM con Juan Lozano", "https://us-b4-p-e-qg12-audio.cdn.mdstrm.com/live-audio-aw/632c9b23d1dcd7027f32f7fe?aid=6271a4d5d206c3172f3c9a9c"),
}
INICIO, FIN = (5, 30), (9, 0)
TRAMO = 600  # segundos
MAX_PUNTOS = 3  # por tramo y radio: solo lo más relevante (pedido de Noffal)
API = "https://generativelanguage.googleapis.com"
UA = "Mozilla/5.0 (RadarNoticias; Oficina del Diputado Felipe Ferro)"
RESALTAR = PALABRAS["tolima"] + ["ferro", "felipe ferro", "centro democratico"]

PROMPT = """Fragmento de {minutos} minutos de "{programa}" ({medio}, Colombia), en vivo desde las {hora}.
Eres el monitor de medios de la Oficina del Diputado Felipe Ferro (Tolima, Centro Democrático).
Saca SOLO lo más relevante para un asesor político: anuncios del Gobierno, declaraciones de políticos
y funcionarios, cifras nuevas, denuncias, primicias, y todo lo que toque a Ibagué o al Tolima.
Deja por fuera opiniones sueltas de los periodistas, chistes, comentarios de relleno, deportes y farándula.
Ignora música, publicidad, saludos, tráfico y clima (salvo emergencias).
Por cada punto: minuto (desde el inicio del fragmento), quien (nombre y cargo; si no lo dicen, "Periodista de {programa}")
y que (una o dos frases, con las cifras exactas que dijeron). Máximo 3 puntos, los más importantes.
Si en el fragmento no pasó nada de peso, responde la lista vacía: es mejor nada que relleno.
No inventes: si no entiendes un nombre, no lo pongas."""

ESQUEMA = {"type": "OBJECT", "properties": {"puntos": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "minuto": {"type": "INTEGER"}, "quien": {"type": "STRING"}, "que": {"type": "STRING"}},
    "required": ["minuto", "quien", "que"]}}}, "required": ["puntos"]}

def resaltar(texto: str) -> bool:
    t = texto_plano(texto)
    return any(re.search(rf"\b{re.escape(p)}\b", t) for p in RESALTAR)

def puntos_de_respuesta(texto: str, medio: str, inicio: datetime) -> list[dict]:
    salida = []
    for p in json.loads(texto).get("puntos", [])[:MAX_PUNTOS]:
        quien, que = str(p.get("quien", "")).strip(), str(p.get("que", "")).strip()
        if not que:
            continue
        minuto = min(max(int(p.get("minuto", 0)), 0), TRAMO // 60)
        hora = (inicio + timedelta(minutes=minuto)).strftime("%H:%M")
        salida.append({"medio": medio, "hora": hora, "quien": quien, "que": que, "resaltar": resaltar(f"{quien} {que}")})
    return salida

def grabar(url: str, segundos: int, abrir=urllib.request.urlopen) -> bytes:
    """Lee la señal en vivo durante `segundos`; si se corta, se reconecta hasta completar el tiempo."""
    fin, partes = time.monotonic() + segundos, []
    while time.monotonic() < fin:
        try:
            with abrir(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                while time.monotonic() < fin:
                    c = r.read(16384)
                    if not c:
                        break
                    partes.append(c)
        except OSError:
            time.sleep(5)
    return b"".join(partes)

def _pedir(url, clave, datos=None, cabeceras=None, metodo="POST"):
    h = {"x-goog-api-key": clave, **(cabeceras or {})}
    return urllib.request.urlopen(urllib.request.Request(url, data=datos, headers=h, method=metodo), timeout=300)

def gemini(audio: bytes, prompt: str, clave: str, modelo: str = "gemini-flash-latest") -> str:
    # Subir el audio (Files API) y pedir los puntos en JSON
    with _pedir(f"{API}/upload/v1beta/files", clave, json.dumps({"file": {"display_name": "tramo"}}).encode(), {
            "X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(len(audio)), "X-Goog-Upload-Header-Content-Type": "audio/aac",
            "Content-Type": "application/json"}) as r:
        destino = r.headers["x-goog-upload-url"]
    with _pedir(destino, clave, audio, {"X-Goog-Upload-Command": "upload, finalize", "X-Goog-Upload-Offset": "0"}) as r:
        archivo = json.load(r)["file"]
    for _ in range(30):
        if archivo.get("state") == "ACTIVE":
            break
        time.sleep(2)
        with _pedir(f"{API}/v1beta/{archivo['name']}", clave, metodo="GET") as r:
            archivo = json.load(r)
    cuerpo = {"contents": [{"parts": [{"text": prompt}, {"file_data": {"mime_type": "audio/aac", "file_uri": archivo["uri"]}}]}],
              "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": ESQUEMA}}
    try:
        with _pedir(f"{API}/v1beta/models/{modelo}:generateContent", clave, json.dumps(cuerpo).encode(),
                    {"Content-Type": "application/json"}) as r:
            return json.load(r)["candidates"][0]["content"]["parts"][0]["text"]
    finally:
        try:
            _pedir(f"{API}/v1beta/{archivo['name']}", clave, metodo="DELETE").close()
        except OSError:
            pass

def ruta_dia(web: Path, dia: str) -> Path:
    return Path(web) / f"mesas-{dia}.json"

def anotar(web: Path, dia: str, puntos: list[dict], aviso: str | None = None) -> None:
    ruta = ruta_dia(web, dia)
    datos = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {"puntos": [], "avisos": []}
    datos["puntos"] += puntos
    if aviso:
        datos["avisos"].append(aviso)
    Path(web).mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")

def podar(web: Path, hoy: str, dias: int = 7) -> None:
    limite = (date.fromisoformat(hoy) - timedelta(days=dias)).isoformat()
    for f in Path(web).glob("mesas-????-??-??.json"):
        if f.stem[6:] < limite:
            f.unlink()

def publicar(web: Path) -> None:
    for c in (["git", "add", str(web)], ["git", "commit", "-q", "-m", "Mesas al aire"],
              ["git", "pull", "-q", "--rebase"], ["git", "push", "-q"]):
        subprocess.run(c, check=False)

def procesar_tramo(medio, audio, inicio, web, resumir, cerrojo, publicar_fn) -> None:
    programa = EMISORAS[medio][0]
    dia, de, a = inicio.date().isoformat(), inicio.strftime("%H:%M"), (inicio + timedelta(seconds=TRAMO)).strftime("%H:%M")
    try:
        if len(audio) < 50_000:
            raise ValueError("casi sin audio")
        texto = resumir(audio, PROMPT.format(minutos=TRAMO // 60, programa=programa, medio=medio, hora=de))
        puntos, aviso = puntos_de_respuesta(texto, medio, inicio), None
    except Exception as e:
        print(f"{medio} {de}: {type(e).__name__}: {e}"[:300], file=sys.stderr)
        puntos, aviso = [], f"{medio}: sin audio de {de} a {a}"
    with cerrojo:
        anotar(web, dia, puntos, aviso)
        publicar_fn(web)

def correr(web: Path, ahora, grabar_fn, resumir, publicar_fn=publicar, dormir=time.sleep) -> None:
    inicio = ahora().replace(hour=INICIO[0], minute=INICIO[1], second=0, microsecond=0)
    fin = inicio.replace(hour=FIN[0], minute=FIN[1])
    if ahora() < inicio:
        dormir((inicio - ahora()).total_seconds())
    podar(web, inicio.date().isoformat())
    cerrojo, hilos = threading.Lock(), []

    def radio(medio):
        while (fin - ahora()).total_seconds() >= 60:  # con menos de un minuto no vale la pena otro tramo
            t0 = ahora()
            audio = grabar_fn(EMISORAS[medio][1], min(TRAMO, (fin - t0).total_seconds()))
            h = threading.Thread(target=procesar_tramo, args=(medio, audio, t0, web, resumir, cerrojo, publicar_fn))
            h.start()
            hilos.append(h)

    radios = [threading.Thread(target=radio, args=(m,)) for m in EMISORAS]
    for h in radios:
        h.start()
    for h in radios:
        h.join()
    for h in hilos:
        h.join()
