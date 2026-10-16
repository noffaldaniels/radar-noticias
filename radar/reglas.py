import unicodedata

SECCIONES = [
    ("mesas", "Mesas de la mañana", "🎙"),
    ("alto", "Alto impacto", "🚨"),
    ("politica", "Política nacional", "🏛"),
    ("tolima", "Ibagué y Tolima", "📍"),
    ("otras", "Otras noticias", "📰"),
    ("sin", "Sin clasificar", "❔"),
]
IDS_SECCION = [s[0] for s in SECCIONES]

# Programas de las mesas de la mañana (en texto plano: sin tildes, minúsculas)
PROGRAMAS = ["mananas blu", "nestor morales", "julio sanchez", "juan lozano"]

# Respaldo cuando la IA no está disponible (texto plano)
PALABRAS = {
    "alto": ["sismo", "temblor", "terremoto", "atentado", "explosion", "masacre", "avalancha",
             "inundacion", "emergencia", "murio", "fallecio", "asesinado", "asesinato", "secuestro",
             "paro armado", "toque de queda", "estado de conmocion"],
    "politica": ["petro", "presidente", "gobierno", "ministro", "ministra", "ministerio", "congreso",
                 "senado", "senador", "camara de representantes", "representante a la camara",
                 "reforma", "procurador", "fiscal general", "contralor", "registraduria", "elecciones",
                 "candidato", "partido politico", "partido liberal", "partido conservador", "corte constitucional", "consejo de estado", "centro democratico",
                 "pacto historico", "uribe", "gobernador", "alcalde"],
    "tolima": ["ibague", "tolima", "tolimense", "espinal", "melgar", "honda", "mariquita", "chaparral",
               "libano", "flandes", "guamo", "purificacion", "planadas", "rioblanco", "ataco", "fresno",
               "natagaima", "coyaima", "ortega", "cajamarca", "deportes tolima"],
}

def texto_plano(s: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", s)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()
