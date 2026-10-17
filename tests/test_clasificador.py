import json
from radar.clasificador import seccion_por_palabras, interpretar_respuesta, clasificar
from radar.modelo import Noticia
import pytest

def n(titulo, palabras="", medio="Blu Radio", enlace=None, lead=""):
    return Noticia(medio, titulo, enlace or f"https://x.co/{abs(hash(titulo))}", "2026-10-16T06:00:00-05:00", palabras=palabras, lead=lead)

def test_palabras_respeta_prioridad():
    assert seccion_por_palabras(n("Ministro de Hacienda en Mañanas Blu")) == "mesas"
    assert seccion_por_palabras(n("Fuerte sismo en Cali")) == "alto"
    assert seccion_por_palabras(n("Gobernador del Tolima y el Congreso")) == "tolima"
    assert seccion_por_palabras(n("Ministro y el Congreso")) == "politica"
    assert seccion_por_palabras(n("Feria en Ibagué")) == "tolima"
    assert seccion_por_palabras(n("Resultados de la lotería")) == "otras"
    assert seccion_por_palabras(n("Entrevista", palabras="Política,Juan Lozano")) == "mesas"

def test_interpretar_respuesta_valida():
    texto = json.dumps({"noticias": [{"i": 0, "seccion": "politica", "igual_a": None}]})
    assert interpretar_respuesta(texto, 1, 0) == [{"i": 0, "seccion": "politica", "igual_a": None}]

@pytest.mark.parametrize("texto", ["no es json", '{"noticias":[{"i":0,"seccion":"farandula","igual_a":null}]}',
                                   '{"noticias":[{"i":5,"seccion":"otras","igual_a":null}]}',
                                   '{"noticias":[{"i":0,"seccion":"otras","igual_a":"r9"}]}'])
def test_interpretar_respuesta_invalida(texto):
    with pytest.raises(ValueError):
        interpretar_respuesta(texto, 1, 0)

def test_clasificar_con_ia_agrupa_repetidas():
    previa = n("Sismo de 6.1 en Bogotá", medio="Caracol Radio", enlace="https://c.co/s")
    nuevas = [n("Temblor de 6,1 sacude Bogotá", medio="La FM", enlace="https://f.co/t"), n("Nuevo ministro", enlace="https://b.co/m")]
    def falsa(mensajes):
        return json.dumps({"noticias": [{"i": 0, "seccion": "alto", "igual_a": "r0"},
                                        {"i": 1, "seccion": "politica", "igual_a": None}]})
    agregar, modo = clasificar(nuevas, [previa], falsa)
    assert modo == "ia"
    assert [a.titulo for a in agregar] == ["Nuevo ministro"]
    assert agregar[0].seccion == "politica"
    assert previa.tambien == [{"medio": "La FM", "enlace": "https://f.co/t"}]

def test_clasificar_si_ia_falla_usa_palabras():
    def rota(mensajes):
        raise RuntimeError("límite diario")
    agregar, modo = clasificar([n("Atentado en Cali")], [], rota)
    assert modo == "palabras" and agregar[0].seccion == "alto"

def test_clasificar_sin_ia():
    agregar, modo = clasificar([n("Lotería de hoy")], [], None)
    assert modo == "palabras" and agregar[0].seccion == "otras"

def test_clasificar_anota_por_que_fallo_la_ia(capsys):
    def rota(mensajes):
        raise RuntimeError("límite diario")
    clasificar([n("Atentado en Cali")], [], rota)
    assert "límite diario" in capsys.readouterr().err

def test_ibague_gana_sobre_politica():
    assert seccion_por_palabras(n("Alcaldesa de Ibagué anuncia cierre de vías")) == "tolima"

def test_partido_de_futbol_no_es_politica():
    assert seccion_por_palabras(n("Nacional ganó el partido contra Millonarios")) == "otras"
    assert seccion_por_palabras(n("El Partido Liberal define candidato")) == "politica"

# Casos reales del 16-oct-2026 (semana de prueba)
def test_tolima_gana_sobre_alto_impacto():
    assert seccion_por_palabras(n("Tragedia en Líbano, Tolima: hombre asesinó a su esposa")) == "tolima"

def test_palabra_completa_no_pedazo():
    # "ministra" está dentro de "administración"
    assert seccion_por_palabras(n("Por qué visitar Panamá", lead="la administración reconoce")) == "otras"

def test_alto_impacto_solo_por_el_titulo():
    assert seccion_por_palabras(n("BogotáEats 2026: precios y restaurantes",
                                  lead="regiones afectadas por el terremoto del 10 de agosto")) == "otras"
    assert seccion_por_palabras(n("Laura Bozzo reapareció tras ser operada de emergencia")) == "otras"

def test_tolima_no_por_el_resumen():
    assert seccion_por_palabras(n("Hombre estuvo 19 meses preso por error",
                                  lead="en la cárcel de Picaleña, en Ibagué")) == "otras"
    assert seccion_por_palabras(n("Plan de ajuste", palabras="Actualidad,Ibagué")) == "tolima"

def test_alto_impacto_nuevas_palabras():
    assert seccion_por_palabras(n("Con drones atacan estación de policía de Teruel, Huila")) == "alto"
    assert seccion_por_palabras(n("Tres niños y una maestra mueren en tiroteo de Oregón")) == "alto"

def test_politica_nuevas_palabras():
    assert seccion_por_palabras(n("Caso UNGRD: Iván Name y Andrés Calle salieron de La Picota")) == "politica"
    assert seccion_por_palabras(n("FMI advierte que la situación fiscal de Colombia no es sostenible")) == "politica"
