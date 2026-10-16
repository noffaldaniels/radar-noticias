from radar.fuentes import leer_rss, leer_sitemap, lead_de, a_cot

RSS = """<?xml version="1.0"?><rss><channel>
<item><title><![CDATA[Petro & el Congreso]]></title><link>https://caracol.com.co/2026/10/16/a/</link>
<description></description><pubDate>Fri, 16 Oct 2026 11:48:00 +0000</pubDate></item>
<item><title>Repetida</title><link>https://caracol.com.co/2026/10/16/a/?utm=x</link><pubDate>Fri, 16 Oct 2026 11:49:00 +0000</pubDate></item>
</channel></rss>"""

SITEMAP = """<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
 xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"><url><loc>https://www.lafm.com.co/politica/x-1</loc>
<news:news><news:publication_date>2026-10-16T11:06+00:00</news:publication_date><news:title>Ministro en La FM</news:title>
<news:keywords>Política,Juan Lozano</news:keywords></news:news></url></urlset>"""

def test_leer_rss_titulo_fecha_y_sin_repetidos():
    ns = leer_rss(RSS, "Caracol Radio")
    assert len(ns) == 1
    assert ns[0].titulo == "Petro & el Congreso"
    assert ns[0].fecha == "2026-10-16T06:48:00-05:00"

def test_leer_sitemap_con_palabras():
    ns = leer_sitemap(SITEMAP, "La FM")
    assert ns[0].titulo == "Ministro en La FM"
    assert ns[0].palabras == "Política,Juan Lozano"
    assert ns[0].fecha == "2026-10-16T06:06:00-05:00"

def test_lead_de_desescapa_entidades():
    html = '<meta property="og:description" content="Al menos tres ni&#xF1;os &amp; una docente">'
    assert lead_de(html) == "Al menos tres niños & una docente"

def test_lead_de_sin_meta_es_vacio():
    assert lead_de("<html></html>") == ""

def test_xml_roto_lanza_error():
    import pytest, xml.etree.ElementTree as ET
    with pytest.raises(ET.ParseError):
        leer_rss("<html>Error 500", "Caracol Radio")

def test_a_cot_acepta_iso_y_rfc():
    assert a_cot("2026-10-14T13:06:08-05:00") == "2026-10-14T13:06:08-05:00"
    assert a_cot("Fri, 16 Oct 2026 04:01:34 +0000") == "2026-10-15T23:01:34-05:00"

def test_lead_de_quita_etiquetas_html():
    html = '<meta property="og:description" content="Mire &lt;a href=&quot;https://caracol.com.co/x&quot;&gt;aquí&lt;/a&gt; la nota">'
    assert lead_de(html) == "Mire aquí la nota"
