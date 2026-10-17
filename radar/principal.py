from datetime import datetime, timedelta
from pathlib import Path

from radar.almacen import cargar_dia, dias_guardados, guardar_dia, podar, separar_nuevas
from radar.clasificador import clasificar
from radar.fuentes import FUENTES
from radar.horario import reporte_y_proximo
from radar.pagina import nombre_archivo, render_dia

RECIENTES = 40

def dia_radar(fecha: str) -> str:
    # El día del Radar va de 10 pm a 10 pm (pedido de Noffal, 16-oct): lo de la noche entra al reporte de las 6:00
    return (datetime.fromisoformat(fecha) + timedelta(hours=2)).date().isoformat()

def ejecutar(ahora, datos: Path, web: Path, leer, traer_lead, llamar) -> dict:
    datos, web = Path(datos), Path(web)
    hoy = ahora.date().isoformat()
    existentes = cargar_dia(datos, hoy)
    for x in existentes:
        x.nueva = False
    avisos, leidas = [], []
    for medio in FUENTES:
        try:
            leidas += [x for x in leer(medio) if dia_radar(x.fecha) == hoy]
        except Exception:
            avisos.append(f"{medio} no respondió en esta actualización")
    nuevas = separar_nuevas(leidas, existentes)
    for x in nuevas:
        try:
            x.lead = traer_lead(x.enlace)
        except Exception:
            x.lead = ""
    recientes = sorted(existentes, key=lambda x: x.fecha)[-RECIENTES:]
    agregar, modo = clasificar(nuevas, recientes, llamar)
    for x in agregar:
        x.nueva = True
    guardar_dia(datos, hoy, existentes + agregar)
    borradas = podar(datos, hoy)
    web.mkdir(parents=True, exist_ok=True)
    for f in borradas:
        (web / f"{f}.html").unlink(missing_ok=True)
    reporte, proximo = reporte_y_proximo(ahora)
    dias = dias_guardados(datos)
    for d in dias:
        html = render_dia(d, cargar_dia(datos, d), dias, hoy, f"{ahora.hour}:{ahora.minute:02d}", reporte, proximo,
                          avisos if d == hoy else [])
        (web / nombre_archivo(d, hoy)).write_text(html, encoding="utf-8")
    # Copia con fecha, para que mañana la pestaña de este día siga funcionando
    (web / f"{hoy}.html").write_text((web / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
    return {"nuevas": len(agregar), "modo": modo, "avisos": avisos}
