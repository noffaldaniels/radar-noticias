import json
from datetime import date, timedelta
from pathlib import Path

from radar.modelo import Noticia, normalizar_enlace

def _ruta(carpeta: Path, fecha: str) -> Path:
    return Path(carpeta) / f"{fecha}.json"

def cargar_dia(carpeta: Path, fecha: str) -> list[Noticia]:
    ruta = _ruta(carpeta, fecha)
    if not ruta.exists():
        return []
    return [Noticia.de_dict(d) for d in json.loads(ruta.read_text(encoding="utf-8"))]

def guardar_dia(carpeta: Path, fecha: str, noticias: list[Noticia]) -> None:
    Path(carpeta).mkdir(parents=True, exist_ok=True)
    datos = [x.a_dict() for x in noticias]
    _ruta(carpeta, fecha).write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")

def dias_guardados(carpeta: Path) -> list[str]:
    return sorted((p.stem for p in Path(carpeta).glob("????-??-??.json")), reverse=True)

def podar(carpeta: Path, hoy: str, dias: int = 7) -> list[str]:
    limite = (date.fromisoformat(hoy) - timedelta(days=dias)).isoformat()
    borradas = [f for f in dias_guardados(carpeta) if f < limite]
    for f in borradas:
        _ruta(carpeta, f).unlink()
    return borradas

def separar_nuevas(leidas: list[Noticia], existentes: list[Noticia]) -> list[Noticia]:
    vistos = set()
    for e in existentes:
        vistos.add(e.id)
        vistos.update(normalizar_enlace(t["enlace"]) for t in e.tambien)
    nuevas = []
    for x in leidas:
        if x.id not in vistos:
            vistos.add(x.id)
            nuevas.append(x)
    return nuevas
