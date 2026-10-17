import json
from datetime import datetime, timedelta

from radar.fuentes import COT
from radar import mesas
from radar.mesas import anotar, correr, grabar, podar, puntos_de_respuesta, resaltar, ruta_dia

INICIO = datetime(2026, 10, 19, 6, 40, tzinfo=COT)

def test_puntos_con_hora_y_resaltado():
    texto = json.dumps({"puntos": [
        {"minuto": 2, "quien": "Ministro de Hacienda", "que": "Anunció recorte de $12 billones"},
        {"minuto": 7, "quien": "Gobernadora", "que": "Habló de las vías del Tolima"},
        {"minuto": 3, "quien": "Nadie", "que": "  "}]})
    p = puntos_de_respuesta(texto, "Caracol Radio", INICIO)
    assert [x["hora"] for x in p] == ["06:42", "06:47"]
    assert p[0]["medio"] == "Caracol Radio" and not p[0]["resaltar"] and p[1]["resaltar"]

def test_minuto_fuera_de_rango_no_se_sale_del_tramo():
    p = puntos_de_respuesta(json.dumps({"puntos": [{"minuto": 99, "quien": "X", "que": "Y"}]}), "La FM", INICIO)
    assert p[0]["hora"] == "06:50"

def test_resalta_ferro_y_centro_democratico():
    assert resaltar("El diputado Felipe Ferro pidió un debate")
    assert resaltar("Bancada del Centro Democrático")
    assert not resaltar("Feria en Medellín")

def test_anotar_acumula_y_podar_borra_lo_viejo(tmp_path):
    anotar(tmp_path, "2026-10-19", [{"que": "a"}])
    anotar(tmp_path, "2026-10-19", [], "La FM: sin audio de 6:00 a 6:10")
    d = json.loads(ruta_dia(tmp_path, "2026-10-19").read_text(encoding="utf-8"))
    assert d == {"puntos": [{"que": "a"}], "avisos": ["La FM: sin audio de 6:00 a 6:10"]}
    anotar(tmp_path, "2026-10-01", [])
    podar(tmp_path, "2026-10-19")
    assert not ruta_dia(tmp_path, "2026-10-01").exists() and ruta_dia(tmp_path, "2026-10-19").exists()

def test_grabar_se_reconecta_si_se_corta(monkeypatch):
    reloj = [0.0]
    monkeypatch.setattr(mesas.time, "monotonic", lambda: reloj[0])
    monkeypatch.setattr(mesas.time, "sleep", lambda s: None)
    class Senal:
        def __init__(self): self.n = 0
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self, _):
            reloj[0] += 1
            self.n += 1
            return b"x" if self.n <= 2 else b""  # se corta tras 2 trozos
    assert grabar("https://x.co/vivo", 5, abrir=lambda *a, **k: Senal()) == b"xxxx"  # 2 trozos, se corta, se reconecta y lee 2 más

def test_correr_graba_las_3_radios_y_avisa_fallas(tmp_path):
    reloj = [datetime(2026, 10, 19, 5, 20, tzinfo=COT)]
    def dormir(s): reloj[0] += timedelta(seconds=s)
    def grabar_fn(url, segundos):
        reloj[0] += timedelta(seconds=segundos / 3)  # las 3 radios graban a la vez
        return b"" if "mdstrm" in url else b"a" * 60_000  # La FM sin señal
    def resumir(audio, prompt):
        return json.dumps({"puntos": [{"minuto": 1, "quien": "Ministro", "que": "Dijo algo"}]})
    publicadas = []
    correr(tmp_path, lambda: reloj[0], grabar_fn, resumir, publicar_fn=publicadas.append, dormir=dormir)
    d = json.loads(ruta_dia(tmp_path, "2026-10-19").read_text(encoding="utf-8"))
    assert {p["medio"] for p in d["puntos"]} == {"Blu Radio", "Caracol Radio"}
    assert min(p["hora"] for p in d["puntos"]) == "05:31"
    assert any(a.startswith("La FM: sin audio de ") for a in d["avisos"])
    assert publicadas  # se publica después de cada tramo

def test_maximo_3_puntos_por_tramo():
    texto = json.dumps({"puntos": [{"minuto": i, "quien": "X", "que": f"Dato {i}"} for i in range(6)]})
    assert len(puntos_de_respuesta(texto, "Blu Radio", INICIO)) == 3
