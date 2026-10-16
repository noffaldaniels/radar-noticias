from dataclasses import dataclass, field, asdict
from urllib.parse import urlsplit, urlunsplit

def normalizar_enlace(url: str) -> str:
    p = urlsplit(url.strip())
    ruta = p.path.rstrip("/")
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), ruta, "", ""))

@dataclass
class Noticia:
    medio: str
    titulo: str
    enlace: str
    fecha: str  # ISO 8601 con -05:00
    palabras: str = ""
    lead: str = ""
    seccion: str = ""
    nueva: bool = False
    tambien: list = field(default_factory=list)  # [{"medio": str, "enlace": str}]

    @property
    def id(self) -> str:
        return normalizar_enlace(self.enlace)

    def a_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def de_dict(d: dict) -> "Noticia":
        return Noticia(**d)
