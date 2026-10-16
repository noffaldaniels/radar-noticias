from datetime import datetime
from radar.fuentes import COT
from radar.horario import reporte_y_proximo

def t(h, m):
    return datetime(2026, 10, 16, h, m, tzinfo=COT)

def test_corrida_de_las_545_es_reporte_de_las_6():
    assert reporte_y_proximo(t(5, 47)) == ("6:00", "6:30")

def test_corrida_de_las_745():
    assert reporte_y_proximo(t(7, 46)) == ("8:00", "9:00")

def test_ultima_corrida_del_dia():
    assert reporte_y_proximo(t(21, 50)) == ("22:00", "mañana 6:00")

def test_corrida_manual_tarde():
    assert reporte_y_proximo(t(23, 10)) == ("22:00", "mañana 6:00")
