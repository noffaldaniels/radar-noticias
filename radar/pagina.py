from datetime import date
from html import escape

from radar.modelo import Noticia
from radar.reglas import SECCIONES

DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
# Orden en pantalla (distinto de la prioridad para clasificar, que sigue en reglas.SECCIONES)
ORDEN_PAGINA = ["mesas", "politica", "alto", "tolima", "otras", "sin"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

def nombre_archivo(fecha: str, hoy: str) -> str:
    return "index.html" if fecha == hoy else f"{fecha}.html"

def _fecha_corta(fecha: str) -> str:
    d = date.fromisoformat(fecha)
    return f"{DIAS_SEMANA[d.weekday()]} {d.day} {MESES[d.month - 1]}"

def _tarjeta(x: Noticia) -> str:
    hora = x.fecha[11:16]
    nueva = '<span class="nueva">NUEVA</span> ' if x.nueva else ""
    tambien = ""
    if x.tambien:
        enlaces = " · ".join(f'<a href="{escape(t["enlace"])}" target="_blank" rel="noopener">{escape(t["medio"])}</a>' for t in x.tambien)
        tambien = f'<div class="tambien">También en: {enlaces}</div>'
    lead = f'<p class="lead">{escape(x.lead)}</p>' if x.lead else ""
    return (f'<article data-medio="{escape(x.medio)}"><div class="meta">{nueva}{escape(x.medio)} · {hora}</div>'
            f'<h3>{escape(x.titulo)}</h3>{lead}'
            f'<a class="ver" href="{escape(x.enlace)}" target="_blank" rel="noopener">Ver noticia →</a>{tambien}</article>')

CSS = """:root{--fondo:#f4f6fa;--tarjeta:#fff;--texto:#1b2333;--suave:#5b6577;--azul:#1f3864;--nueva:#c0392b}
@media (prefers-color-scheme:dark){:root{--fondo:#11151c;--tarjeta:#1b212b;--texto:#e8ecf2;--suave:#9aa4b5;--azul:#8fb3ff;--nueva:#ff6b5b}}
*{box-sizing:border-box}body{margin:0;background:var(--fondo);color:var(--texto);font:16px/1.45 system-ui,sans-serif}
header{background:var(--azul);color:#fff;padding:14px 16px}header h1{margin:0;font-size:20px}header p{margin:2px 0 0;font-size:14px;opacity:.9}
nav{display:flex;gap:6px;overflow-x:auto;padding:10px 16px}nav a,nav button{white-space:nowrap;border:1px solid var(--suave);border-radius:16px;padding:4px 10px;color:var(--texto);background:none;font-size:14px;text-decoration:none}
nav .activo{background:var(--azul);color:#fff;border-color:var(--azul)}main{padding:0 16px 32px;max-width:760px;margin:auto}
.aviso{background:#fff3cd;color:#664d03;padding:8px 12px;border-radius:8px;margin:8px 0}h2{font-size:17px;margin:20px 0 8px}
article{background:var(--tarjeta);border-radius:10px;padding:12px;margin:8px 0;overflow-wrap:anywhere}article h3{font-size:16px;margin:4px 0}
.meta,.tambien{font-size:13px;color:var(--suave)}.lead{margin:4px 0;font-size:14px}.ver{font-size:14px;color:var(--azul)}
.nueva{background:var(--nueva);color:#fff;border-radius:4px;padding:1px 5px;font-size:11px;font-weight:700}
details{background:var(--tarjeta);border-radius:10px;margin:10px 0;padding:0 12px}details[open]{background:none;padding:0}
summary{cursor:pointer;padding:12px 0;list-style:none;display:flex;justify-content:space-between;align-items:center}
summary::-webkit-details-marker{display:none}summary h2{display:inline;margin:0}
summary::after{content:"▾";color:var(--suave);font-size:18px}details[open]>summary::after{content:"▴"}"""

JS = """document.querySelectorAll('[data-filtro]').forEach(b=>b.onclick=()=>{
document.querySelectorAll('[data-filtro]').forEach(o=>o.classList.toggle('activo',o===b));
const m=b.dataset.filtro;document.querySelectorAll('article').forEach(a=>a.hidden=m!=='todos'&&a.dataset.medio!==m);});"""

def render_dia(fecha, noticias, dias, hoy, actualizado, reporte, proximo, avisos) -> str:
    pestanas = "".join(
        f'<a href="{nombre_archivo(d, hoy)}" class="{"activo" if d == fecha else ""}">{"Hoy" if d == hoy else _fecha_corta(d)}</a>' for d in dias)
    medios = sorted({x.medio for x in noticias})
    filtros = '<button data-filtro="todos" class="activo">Todos</button>' + "".join(
        f'<button data-filtro="{escape(m)}">{escape(m)}</button>' for m in medios)
    cuerpo = "".join(f'<div class="aviso">⚠ {escape(a)}</div>' for a in avisos)
    for sid, nombre, icono in sorted(SECCIONES, key=lambda s: ORDEN_PAGINA.index(s[0])):
        grupo = sorted((x for x in noticias if x.seccion == sid), key=lambda x: x.fecha, reverse=True)
        if not grupo:
            continue
        tarjetas = "".join(_tarjeta(x) for x in grupo)
        titulo = f"{icono} {nombre} ({len(grupo)})"
        cuerpo += f"<details><summary><h2>{titulo}</h2></summary>{tarjetas}</details>"
    if not noticias:
        cuerpo += "<p>Todavía no hay noticias para este día.</p>"
    estado = f"Actualizado {actualizado} (reporte de las {reporte}) · Próxima: {proximo}" if fecha == hoy else "Archivo"
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow">
<title>Radar Noticias</title><style>{CSS}</style></head><body>
<header><h1>Radar Noticias</h1><p>Oficina del Diputado Felipe Ferro · {_fecha_corta(fecha)}</p><p>{estado}</p></header>
<nav>{pestanas}</nav><nav>{filtros}</nav><main>{cuerpo}</main><script>{JS}</script></body></html>"""
