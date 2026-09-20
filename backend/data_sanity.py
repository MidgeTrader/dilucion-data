"""Comprobaciones de coherencia sobre el perfil enriquecido.

Por que existe: el perfil se construye fusionando cinco proveedores externos
(Polygon, Finnhub, yfinance, Finviz, Stonktracker) y ninguno se valida contra
otro. Medido sobre el universo del scanner, 6 de 61 tickers traian el float
incoherente — y son justo los candidatos a squeeze de float bajo, que es el
dato sobre el que se decide entrar.

Que hace y que NO hace:

    - Anula lo IMPOSIBLE. Un float mayor que las acciones no puede ser cierto,
      asi que se descarta en vez de pintarlo como si fuera un dato.
    - NO anula lo SOSPECHOSO. Un float muy bajo puede ser legitimo (salida a
      bolsa reciente). Se registra en el log y se deja pasar: borrar un dato
      valido es peor que mostrar uno dudoso.

Por que no se contrasta contra EDGAR: los FPI presentan 6-K sin etiquetar en
XBRL, asi que el balance de EDGAR va por detras de la realidad. Un cruce ciego
marcaria como erroneos datos que estan bien (15 de 60 tickers son FPI).
"""

from __future__ import annotations

import logging

from models import TickerProfile

logger = logging.getLogger(__name__)

# Por debajo de esta fraccion de las acciones, un float es raro pero posible:
# una salida a bolsa reciente puede tener muy poco papel libre. Se avisa, no
# se toca.
SUSPICIOUS_FLOAT_RATIO = 0.02


def _clear_impossible_float(profile: TickerProfile) -> None:
    """Anula el float si supera las acciones en circulacion.

    Un float es un subconjunto de las acciones, asi que no puede ser mayor.
    Cuando pasa, uno de los dos datos es basura y no hay forma de saber cual,
    asi que se descarta el float y se conserva el conteo de acciones — que es
    el que sostienen el market cap y el calculo de dilucion.

    Args:
        profile: Perfil a corregir en sitio.
    """
    float_shares = profile.float_shares
    shares = profile.shares_outstanding
    if float_shares is None or shares is None or shares <= 0:
        return
    if float_shares > shares:
        logger.warning(
            "Float imposible en %s: float=%.0f > acciones=%.0f (%.2fx). Se anula el float.",
            profile.ticker,
            float_shares,
            shares,
            float_shares / shares,
        )
        profile.float_shares = None


def _warn_suspicious_float(profile: TickerProfile) -> None:
    """Registra un float anormalmente bajo sin alterarlo.

    Args:
        profile: Perfil a revisar.
    """
    float_shares = profile.float_shares
    shares = profile.shares_outstanding
    if float_shares is None or shares is None or shares <= 0:
        return
    ratio = float_shares / shares
    if 0 < ratio < SUSPICIOUS_FLOAT_RATIO:
        logger.warning(
            "Float sospechoso en %s: %.0f sobre %.0f acciones (%.3f%%). "
            "Puede ser legitimo; no se altera.",
            profile.ticker,
            float_shares,
            shares,
            ratio * 100,
        )


def check_profile(profile: TickerProfile) -> TickerProfile:
    """Aplica las comprobaciones de coherencia a un perfil enriquecido.

    Se llama despues de fusionar todas las fuentes, para que ninguna pueda
    introducir un valor imposible sin pasar por aqui.

    Args:
        profile: Perfil ya construido.

    Returns:
        El mismo perfil, corregido en sitio.
    """
    _clear_impossible_float(profile)
    _warn_suspicious_float(profile)
    return profile
