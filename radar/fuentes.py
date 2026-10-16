import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from radar.modelo import Noticia

COT = timezone(timedelta(hours=-5))
FUENTES = {
    "Blu Radio": ("sitemap", "https://www.bluradio.com/content-sitemap-latest.xml"),
    "Caracol Radio": ("rss", "https://caracol.com.co/arc/outboundfeeds/rss/?outputType=xml"),
    "La FM": ("sitemap", "https://www.lafm.com.co/sitemapnews"),
}
UA = "Mozilla/5.0 (RadarNoticias; Oficina del Diputado Felipe Ferro)"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "n": "http://www.google.com/schemas/sitemap-news/0.9"}

def descargar(url: str, timeout: int = 20) -> str:
    pedido = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(pedido, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def a_cot(texto: str) -> str:
    texto = texto.strip()
    try:
        fecha = datetime.fromisoformat(texto)
    except ValueError:
        fecha = parsedate_to_datetime(texto)
    return fecha.astimezone(COT).isoformat(timespec="seconds")

def _sin_repetidos(noticias: list[Noticia]) -> list[Noticia]:
    vistos, salida = set(), []
    for n in noticias:
        if n.id not in vistos:
            vistos.add(n.id)
            salida.append(n)
    return salida

def leer_rss(xml_texto: str, medio: str) -> list[Noticia]:
    raiz = ET.fromstring(xml_texto)
    noticias = []
    for item in raiz.iter("item"):
        titulo = html.unescape((item.findtext("title") or "").strip())
        enlace = (item.findtext("link") or "").strip()
        fecha = item.findtext("pubDate")
        if titulo and enlace and fecha:
            noticias.append(Noticia(medio, titulo, enlace, a_cot(fecha)))
    return _sin_repetidos(noticias)

def leer_sitemap(xml_texto: str, medio: str) -> list[Noticia]:
    raiz = ET.fromstring(xml_texto)
    noticias = []
    for url in raiz.findall("s:url", NS):
        enlace = (url.findtext("s:loc", "", NS)).strip()
        titulo = html.unescape((url.findtext("n:news/n:title", "", NS)).strip())
        fecha = url.findtext("n:news/n:publication_date", "", NS)
        palabras = (url.findtext("n:news/n:keywords", "", NS)).strip()
        if titulo and enlace and fecha:
            noticias.append(Noticia(medio, titulo, enlace, a_cot(fecha), palabras=palabras))
    return _sin_repetidos(noticias)

_META = [r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"',
         r'<meta[^>]+name="description"[^>]+content="([^"]*)"']

def lead_de(html_texto: str) -> str:
    for patron in _META:
        m = re.search(patron, html_texto)
        if m:
            texto = re.sub(r"<[^>]+>", "", html.unescape(m.group(1)))
            return re.sub(r"\s+", " ", texto).strip()
    return ""

def leer_medio(medio: str) -> list[Noticia]:
    tipo, url = FUENTES[medio]
    texto = descargar(url)
    return leer_rss(texto, medio) if tipo == "rss" else leer_sitemap(texto, medio)
