import unicodedata

SECCIONES = [
    ("mesas", "Mesas de la mañana", "🎙"),
    ("alto", "Alto impacto", "🚨"),
    ("politica", "Política nacional", "🏛"),
    ("tolima", "Ibagué y Tolima", "📍"),
    ("otras", "Otras noticias", "📰"),
    ("deportes", "Deportes", "⚽"),
    ("internacional", "Internacional", "🌎"),
    ("sin", "Sin clasificar", "❔"),
]
IDS_SECCION = [s[0] for s in SECCIONES]

# Programas de las mesas de la mañana (en texto plano: sin tildes, minúsculas)
PROGRAMAS = ["mananas blu", "nestor morales", "julio sanchez", "juan lozano"]

# Respaldo cuando la IA no está disponible (texto plano)
PALABRAS = {
    "alto": ["sismo", "temblor", "terremoto", "atentado", "explosion", "masacre", "avalancha",
             "inundacion", "murio", "fallecio", "mueren", "muertos", "asesinado", "asesinato", "asesinan",
             "secuestro", "tiroteo", "dron", "drones", "granada", "ataque terrorista",
             "paro armado", "toque de queda", "estado de conmocion"],
    "politica": ["petro", "presidente", "gobierno", "ministro", "ministra", "ministerio", "congreso",
                 "senado", "senador", "camara de representantes", "representante a la camara",
                 "reforma", "procurador", "fiscal general", "contralor", "registraduria", "elecciones",
                 "candidato", "partido politico", "partido liberal", "partido conservador", "corte constitucional", "consejo de estado", "centro democratico",
                 "pacto historico", "uribe", "gobernador", "alcalde", "de la espriella", "primera dama",
                 "ungrd", "fmi", "dnp", "minhacienda", "ministerio de hacienda", "dian", "procuraduria",
                 "contraloria", "consejo nacional electoral", "cne", "congresista", "corrupcion", "anticorrupcion",
                 "petrismo", "petrista", "vicepresidente", "vicepresidenta", "canciller", "cancilleria",
                 "embajada", "concejo", "concejal", "cabildo", "ministros", "senadores", "senadora", "alcaldesa",
                 "alcaldes", "gobernadora", "gobernadores", "candidata", "candidatos", "congresistas",
                 "presidenta", "presidencial", "presidenciales", "reformas", "concejales"],
    "tolima": ["ibague", "tolima", "tolimense", "tolimenses", "espinal", "melgar", "honda", "mariquita", "chaparral",
               "libano", "flandes", "guamo", "purificacion", "planadas", "rioblanco", "ataco", "fresno",
               "natagaima", "coyaima", "ortega", "cajamarca", "deportes tolima"],
}

# Internacional (pedido de Noffal, 19-oct): Blu y La FM lo marcan en el enlace; Caracol no, por eso la lista
# de países y líderes (solo en el título). Si el título también habla de Colombia, no es internacional.
# Deportes (pedido de Noffal, 19-oct): igual que Internacional, enlace en Blu y La FM y palabras (solo el título) en Caracol.
RUTAS_DEPORTES = ["/deportes/", "/blog-deportivo/"]
DEPORTES = ["futbol", "gol", "goles", "liga betplay", "liga colombiana", "liga el dorado", "dimayor", "champions",
            "sudamericana", "libertadores", "conmebol", "seleccion colombia", "millonarios fc", "a millonarios", "con millonarios", "contra millonarios",
            "millonarios vs", "junior", "america de cali",
            "atletico nacional", "deportivo cali", "once caldas", "tabla de posiciones", "empate", "empatar", "invicto",
            "clasico rcn", "tour de francia", "ciclismo", "ciclista", "tenis", "formula 1", "nba", "voleibol",
            "baloncesto", "medallas", "cucho hernandez", "james rodriguez", "luis diaz", "cristiano ronaldo", "messi"]

RUTAS_INTERNACIONAL = ["/mundo/", "/internacional/"]
EXTRANJERO = ["francia", "frances", "francesa", "macron", "lecornu", "brasil", "lula", "bolsonaro", "rusia", "ruso", "rusa",
              "putin", "ucrania", "zelenski", "china", "estados unidos", "trump", "casa blanca", "venezuela", "maduro",
              "ecuador", "noboa", "peru", "mexico", "sheinbaum", "argentina", "milei", "chile", "espana", "israel",
              "gaza", "iran", "teheran", "japon", "australia", "australiana", "reino unido", "europa"]
COLOMBIA = ["colombia", "colombiano", "colombianos", "colombiana", "colombianas", "al pais", "del pais", "en el pais",
            "petro", "uribe", "de la espriella", "benedetti", "cancilleria", "bogota", "medellin", "cali",
            "barranquilla", "cartagena", "pereira", "bucaramanga", "cucuta", "santa marta", "manizales",
            "villavicencio", "neiva", "pasto", "san andres"]

def texto_plano(s: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", s)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()
