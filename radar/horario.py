from datetime import datetime

from radar.fuentes import COT

REPORTES = ["6:00", "6:30", "7:00", "7:30", "8:00"] + [f"{h}:00" for h in range(9, 23)]

def ahora_cot() -> datetime:
    return datetime.now(COT)

def _minutos(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)

def reporte_y_proximo(ahora: datetime) -> tuple[str, str]:
    actual = ahora.hour * 60 + ahora.minute
    for k, r in enumerate(REPORTES):
        if _minutos(r) >= actual:
            proximo = REPORTES[k + 1] if k + 1 < len(REPORTES) else "mañana 6:00"
            return r, proximo
    return REPORTES[-1], "mañana 6:00"
