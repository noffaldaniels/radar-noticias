from radar.modelo import Noticia
from radar.pagina import render_dia, nombre_archivo

def test_nombre_archivo():
    assert nombre_archivo("2026-10-16", "2026-10-16") == "index.html"
    assert nombre_archivo("2026-10-15", "2026-10-16") == "2026-10-15.html"

def pagina(noticias, avisos=()):
    return render_dia("2026-10-16", noticias, ["2026-10-16", "2026-10-15"], "2026-10-16", "5:47", "6:00", "6:30", list(avisos))

def test_escapa_html_y_marca_nueva():
    x = Noticia("La FM", 'Petro <b>&</b> "Congreso"', "https://f.co/1", "2026-10-16T06:48:00-05:00",
                lead="Lead", seccion="politica", nueva=True, tambien=[{"medio": "Blu Radio", "enlace": "https://b.co/2"}])
    h = pagina([x])
    assert "Petro &lt;b&gt;&amp;&lt;/b&gt; &quot;Congreso&quot;" in h
    assert "NUEVA" in h and "También en" in h and "https://b.co/2" in h
    assert "Oficina del Diputado Felipe Ferro" in h and "despacho" not in h.lower()
    assert "Actualizado 5:47" in h and "6:30" in h

def test_secciones_en_orden_y_otras_cerrada():
    xs = [Noticia("Blu Radio", "A", "https://b.co/a", "2026-10-16T07:00:00-05:00", seccion="otras"),
          Noticia("Blu Radio", "B", "https://b.co/b", "2026-10-16T06:00:00-05:00", seccion="mesas")]
    h = pagina(xs)
    assert h.index("Mesas de la mañana") < h.index("Otras noticias")
    assert "<details" in h and "Alto impacto" not in h  # secciones vacías no se muestran

def test_aviso_de_medio_caido():
    assert "La FM no respondió en esta actualización" in pagina([], ["La FM no respondió en esta actualización"])

def test_textos_largos_no_desbordan_en_celular():
    assert "overflow-wrap:anywhere" in pagina([])

def test_politica_va_antes_de_alto_impacto_y_todo_plegado():
    xs = [Noticia("Blu Radio", s, f"https://b.co/{s}", "2026-10-16T07:00:00-05:00", seccion=s)
          for s in ("alto", "politica", "mesas", "tolima")]
    h = pagina(xs)
    assert h.index("Mesas de la mañana") < h.index("Política nacional") < h.index("Alto impacto") < h.index("Ibagué y Tolima")
    assert h.count("<details>") == 4 and "<details open" not in h
