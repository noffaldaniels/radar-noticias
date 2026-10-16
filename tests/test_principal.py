import json
from datetime import datetime
from radar.fuentes import COT
from radar.modelo import Noticia
from radar.almacen import guardar_dia, cargar_dia
from radar.principal import ejecutar

def leer_falso(medio):
    if medio == "La FM":
        raise OSError("timeout")
    return [Noticia(medio, f"Ministro en {medio}", f"https://{medio[:3]}.co/hoy", "2026-10-16T05:30:00-05:00"),
            Noticia(medio, "Nota de ayer", f"https://{medio[:3]}.co/ayer", "2026-10-15T22:00:00-05:00")]

def test_primera_corrida_del_dia(tmp_path):
    datos, web = tmp_path / "data", tmp_path / "docs"
    guardar_dia(datos, "2026-10-15", [Noticia("Blu Radio", "Vieja", "https://b.co/v", "2026-10-15T10:00:00-05:00", seccion="otras")])
    r = ejecutar(datetime(2026, 10, 16, 5, 47, tzinfo=COT), datos, web, leer_falso, lambda url: "Lead", None)
    hoy = cargar_dia(datos, "2026-10-16")
    assert r["nuevas"] == 2 and r["modo"] == "palabras"
    assert {x.titulo for x in hoy} == {"Ministro en Blu Radio", "Ministro en Caracol Radio"}
    assert all(x.nueva and x.lead == "Lead" for x in hoy)
    assert r["avisos"] == ["La FM no respondió en esta actualización"]
    assert (web / "index.html").exists() and (web / "2026-10-15.html").exists()

def test_segunda_corrida_no_repite_y_apaga_nueva(tmp_path):
    datos, web = tmp_path / "data", tmp_path / "docs"
    ejecutar(datetime(2026, 10, 16, 5, 47, tzinfo=COT), datos, web, leer_falso, lambda url: "", None)
    r = ejecutar(datetime(2026, 10, 16, 6, 16, tzinfo=COT), datos, web, leer_falso, lambda url: "", None)
    assert r["nuevas"] == 0
    assert not any(x.nueva for x in cargar_dia(datos, "2026-10-16"))

def test_lead_que_falla_no_rompe(tmp_path):
    def lead_roto(url):
        raise OSError("404")
    r = ejecutar(datetime(2026, 10, 16, 5, 47, tzinfo=COT), tmp_path / "d", tmp_path / "w", leer_falso, lead_roto, None)
    assert r["nuevas"] == 2
