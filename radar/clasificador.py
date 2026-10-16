import json
import urllib.request

from radar.modelo import Noticia
from radar.reglas import IDS_SECCION, PALABRAS, PROGRAMAS, texto_plano

URL_MODELOS = "https://models.github.ai/inference/chat/completions"
TAMANO_LOTE = 30

def seccion_por_palabras(n: Noticia) -> str:
    texto = texto_plano(f"{n.titulo} {n.palabras} {n.lead}")
    if any(p in texto for p in PROGRAMAS):
        return "mesas"
    for seccion in ("alto", "politica", "tolima"):
        if any(p in texto for p in PALABRAS[seccion]):
            return seccion
    return "otras"

INSTRUCCIONES = """Eres el clasificador de noticias de la Oficina del Diputado Felipe Ferro (Tolima, Colombia).
Pon cada noticia NUEVA en UNA sección, con esta prioridad (gana la primera que aplique):
- mesas: viene de un programa de la mañana: Mañanas Blu (Néstor Morales, Blu Radio), Julio Sánchez Cristo (Caracol Radio) o Juan Lozano (La FM); entrevistas a ministros, al presidente o a políticos.
- alto: alto impacto nacional: sismos, atentados, catástrofes, muerte de figuras públicas, orden público grave, decisiones que afectan a todo el país.
- politica: política nacional (Gobierno, Congreso, partidos, cortes, organismos de control, elecciones).
- tolima: Ibagué o municipios del Tolima.
- otras: todo lo demás.
Si una noticia nueva cuenta el MISMO hecho que una RECIENTE (rK) o que otra NUEVA anterior (nK), pon igual_a con ese código; si no, null.
Responde SOLO JSON: {"noticias": [{"i": <índice de la nueva>, "seccion": "<mesas|alto|politica|tolima|otras>", "igual_a": "<rK|nK|null>"}]} con una entrada por cada noticia nueva."""

def armar_mensajes(nuevas: list[Noticia], recientes: list[Noticia]) -> list[dict]:
    lineas = ["RECIENTES:"] + [f"r{k}: [{r.medio}] {r.titulo}" for k, r in enumerate(recientes)]
    lineas += ["NUEVAS:"] + [f"n{k}: [{x.medio}] {x.titulo} | {x.palabras} | {x.lead[:200]}" for k, x in enumerate(nuevas)]
    return [{"role": "system", "content": INSTRUCCIONES}, {"role": "user", "content": "\n".join(lineas)}]

def interpretar_respuesta(texto: str, n_nuevas: int, n_recientes: int) -> list[dict]:
    try:
        filas = json.loads(texto)["noticias"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise ValueError(f"respuesta no es JSON válido: {e}")
    salida, vistos = [], set()
    for f in filas:
        i, seccion, igual = f.get("i"), f.get("seccion"), f.get("igual_a")
        if not isinstance(i, int) or not 0 <= i < n_nuevas or i in vistos:
            raise ValueError(f"índice inválido: {i}")
        if seccion not in IDS_SECCION[:5]:
            raise ValueError(f"sección inválida: {seccion}")
        if igual is not None:
            tipo, num = str(igual)[:1], str(igual)[1:]
            limite = n_recientes if tipo == "r" else i
            if tipo not in ("r", "n") or not num.isdigit() or int(num) >= limite:
                raise ValueError(f"igual_a inválido: {igual}")
        vistos.add(i)
        salida.append({"i": i, "seccion": seccion, "igual_a": igual})
    if len(vistos) != n_nuevas:
        raise ValueError("faltan noticias en la respuesta")
    return salida

def llamar_github_models(mensajes: list[dict], token: str, modelo: str = "openai/gpt-4o-mini") -> str:
    cuerpo = json.dumps({"model": modelo, "messages": mensajes, "temperature": 0,
                         "response_format": {"type": "json_object"}}).encode("utf-8")
    pedido = urllib.request.Request(URL_MODELOS, data=cuerpo, method="POST", headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(pedido, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]

def _pegar(base: Noticia, repetida: Noticia) -> None:
    base.tambien.append({"medio": repetida.medio, "enlace": repetida.enlace})

def clasificar(nuevas: list[Noticia], recientes: list[Noticia], llamar) -> tuple[list[Noticia], str]:
    agregar, modos = [], set()
    for inicio in range(0, len(nuevas), TAMANO_LOTE):
        lote = nuevas[inicio:inicio + TAMANO_LOTE]
        try:
            if llamar is None:
                raise RuntimeError("sin IA")
            filas = interpretar_respuesta(llamar(armar_mensajes(lote, recientes)), len(lote), len(recientes))
            modos.add("ia")
            for f in filas:
                x = lote[f["i"]]
                x.seccion = f["seccion"]
                igual = f["igual_a"]
                if igual and igual[0] == "r":
                    _pegar(recientes[int(igual[1:])], x)
                elif igual and igual[0] == "n" and lote[int(igual[1:])] in agregar:
                    _pegar(lote[int(igual[1:])], x)
                else:
                    agregar.append(x)
        except Exception:
            modos.add("palabras")
            for x in lote:
                x.seccion = seccion_por_palabras(x)
                agregar.append(x)
    if not modos:  # no había noticias nuevas
        modos.add("ia" if llamar is not None else "palabras")
    modo = "mixto" if len(modos) > 1 else modos.pop()
    return agregar, modo
