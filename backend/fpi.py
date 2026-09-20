"""Clasificacion de Foreign Private Issuer (FPI) a partir de formularios SEC.

Un emisor es FPI si presenta formularios de la serie F (registro) o
20-F / 40-F / 6-K (periodicos). Esos formularios son exclusivos de emisores
incorporados fuera de EE.UU., asi que su presencia es prueba suficiente:
EDGAR no expone ningun campo booleano equivalente.

Por que importa en Dilucion Data: los FPI estan exentos de la Section 16
(Rule 3a12-3), asi que sus insiders NO presentan Form 3 ni Form 4. La pata
de distribucion del mecanismo pump-and-dump es invisible para ellos, y la
ausencia de esos formularios no debe leerse como "no hay venta de insiders".

Referencia: Rule 3b-4 (Exchange Act) / Rule 405 (Securities Act).
"""

from __future__ import annotations

from typing import Iterable

# Formularios que SOLO puede presentar un Foreign Private Issuer.
# 20-F / 40-F: informe anual (40-F es el MJDS canadiense)
# 6-K:         informe intermedio (equivalente al 8-K, pero no obligatorio)
# F-1..F-10:   registro de valores (el domestico usa S-1..S-11)
FPI_FORMS = frozenset({
    "20-F", "40-F", "6-K",
    "F-1", "F-3", "F-4", "F-6", "F-7", "F-8", "F-9", "F-10",
})


def _base_form(form_type: str) -> str:
    """Normaliza un formulario de EDGAR quitando el sufijo de enmienda.

    Args:
        form_type: Formulario tal cual lo devuelve EDGAR (p. ej. "F-3/A").

    Returns:
        El formulario sin sufijo de enmienda ("F-3"), en mayusculas.
    """
    return form_type.strip().upper().split("/", 1)[0]


def is_foreign_private_issuer(form_types: Iterable[str]) -> bool:
    """Determina si un emisor es Foreign Private Issuer segun sus formularios.

    Args:
        form_types: Formularios presentados por el emisor en cualquier fecha.
            Los valores vacios o None se ignoran.

    Returns:
        True si al menos un formulario es exclusivo de FPI.

    Raises:
        TypeError: Si form_types es None. Devolver False seria un resultado
            erroneo: "desconocido" no es lo mismo que "no es FPI".
    """
    if form_types is None:
        raise TypeError("form_types no puede ser None")

    for form_type in form_types:
        if not isinstance(form_type, str) or not form_type:
            continue
        if _base_form(form_type) in FPI_FORMS:
            return True
    return False
