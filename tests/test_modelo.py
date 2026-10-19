from radar.modelo import Noticia, normalizar_enlace
from radar.reglas import texto_plano, IDS_SECCION

def test_normalizar_quita_query_fragmento_y_barra():
    assert normalizar_enlace("https://WWW.Caracol.com.co/2026/10/16/nota/?utm_source=x#top") == "https://www.caracol.com.co/2026/10/16/nota"

def test_noticia_ida_y_vuelta_dict():
    n = Noticia("La FM", "Título", "https://www.lafm.com.co/a-1", "2026-10-16T06:48:00-05:00", lead="Lead")
    assert Noticia.de_dict(n.a_dict()) == n
    assert n.id == "https://www.lafm.com.co/a-1"

def test_texto_plano_quita_tildes_y_mayusculas():
    assert texto_plano("Ibagué, TOLIMA: Néstor") == "ibague, tolima: nestor"

def test_orden_de_secciones():
    assert IDS_SECCION == ["mesas", "alto", "politica", "tolima", "otras", "internacional", "sin"]
