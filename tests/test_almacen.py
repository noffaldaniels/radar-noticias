from radar.almacen import cargar_dia, guardar_dia, dias_guardados, podar, separar_nuevas
from radar.modelo import Noticia

def n(enlace, medio="Blu Radio"):
    return Noticia(medio, "T", enlace, "2026-10-16T06:00:00-05:00")

def test_guardar_y_cargar(tmp_path):
    guardar_dia(tmp_path, "2026-10-16", [n("https://a.co/1")])
    assert cargar_dia(tmp_path, "2026-10-16")[0].enlace == "https://a.co/1"
    assert cargar_dia(tmp_path, "2026-10-17") == []

def test_podar_deja_hoy_y_7_dias(tmp_path):
    for d in range(1, 17):
        guardar_dia(tmp_path, f"2026-10-{d:02d}", [])
    borradas = podar(tmp_path, "2026-10-16")
    assert dias_guardados(tmp_path) == [f"2026-10-{d:02d}" for d in range(16, 8, -1)]
    assert "2026-10-08" in borradas

def test_separar_nuevas_ignora_ya_vistas_y_tambien():
    existente = n("https://a.co/1")
    existente.tambien = [{"medio": "La FM", "enlace": "https://b.co/9"}]
    leidas = [n("https://a.co/1?utm=x"), n("https://b.co/9", "La FM"), n("https://c.co/2")]
    assert [x.enlace for x in separar_nuevas(leidas, [existente])] == ["https://c.co/2"]
