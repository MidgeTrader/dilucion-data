"""Pista de caja (meses de quema) derivada de los estados financieros de EDGAR.

Por que existe: la pata de dilucion de un pump-and-dump se lee mejor sabiendo
cuanto le queda a la empresa antes de tener que ampliar otra vez. Si le quedan
seis meses, la proxima oferta no es un riesgo — es un hecho con fecha.

De donde sale el dato: del endpoint companyfacts de EDGAR (XBRL), no del
proveedor de market data. Medido sobre 8 tickers, el campo `freeCashflow` de
Yahoo incumplia `FCF <= OCF` en 6 de ellos — imposible salvo venta de activos —
y en dos hasta cambiaba de signo. El flujo de operaciones de EDGAR, en cambio,
coincidia con el de Yahoo alli donde Yahoo estaba bien.

Dos trampas que maneja este modulo:

    1. El periodo. El mismo concepto llega como año completo (364 dias) o como
       semestre (180). Anualizar sin mirar `start`/`end` multiplica el error por
       dos. Medido: GPUS y CPHI reportan semestres.
    2. El flujo positivo. Una empresa que genera caja en operaciones no tiene
       runway finito. Devolver `months_of_cash=None` es correcto; devolver un
       numero enorme seria inventarselo.

Este modulo es puro: no hace red ni toca cache. Recibe los hechos ya descargados
por CompanyFactsClient.get_facts, asi que se puede probar sin conexion.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from models import CashBurn

logger = logging.getLogger(__name__)

# Conceptos XBRL en orden de preferencia. Los primeros son los especificos; los
# siguientes son el mismo dato bajo otra etiqueta en emisores que no separan la
# caja restringida del efectivo.
CASH_TAGS: Tuple[str, ...] = (
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
)
OCF_TAGS: Tuple[str, ...] = (
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
)

DAYS_PER_YEAR = 365.0


def _facts_for(facts: Dict[str, Any], tags: Tuple[str, ...]) -> List[dict]:
    """Entradas XBRL en USD de la primera etiqueta que traiga datos.

    Args:
        facts: Respuesta cruda de companyfacts.
        tags: Etiquetas us-gaap por orden de preferencia.

    Returns:
        Lista de entradas, vacia si ninguna etiqueta tiene datos.
    """
    us_gaap = (facts.get("facts") or {}).get("us-gaap") or {}
    for tag in tags:
        entries = ((us_gaap.get(tag) or {}).get("units") or {}).get("USD") or []
        if entries:
            return list(entries)
    return []


def _period_days(entry: dict) -> Optional[int]:
    """Duracion en dias de una entrada XBRL.

    Args:
        entry: Entrada XBRL.

    Returns:
        Los dias del periodo, o None si es un dato instantaneo (sin `start`) o
        si las fechas vienen mal formadas.
    """
    start, end = entry.get("start"), entry.get("end")
    if not start or not end:
        return None
    try:
        return (date.fromisoformat(end) - date.fromisoformat(start)).days
    except (ValueError, TypeError):
        return None


def _latest(entries: List[dict]) -> Optional[dict]:
    """La entrada mas reciente; a igual fecha, la de periodo mas largo.

    A igual `end`, XBRL trae el trimestre y el acumulado del año. Se prefiere el
    periodo largo porque promedia mas y da una quema menos ruidosa.

    Args:
        entries: Entradas XBRL.

    Returns:
        La entrada elegida, o None si la lista esta vacia.
    """
    if not entries:
        return None
    return max(entries, key=lambda e: (e.get("end") or "", _period_days(e) or 0))


def extract_cash_burn(facts: Dict[str, Any]) -> CashBurn:
    """Deriva caja disponible y meses de pista desde los hechos XBRL.

    Args:
        facts: Respuesta cruda de /api/xbrl/companyfacts/CIK##########.json.

    Returns:
        CashBurn con lo que se haya podido derivar. Si falta la caja o el flujo,
        devuelve un CashBurn vacio: nunca inventa una cifra.
    """
    if not facts:
        return CashBurn()

    cash_entry = _latest(_facts_for(facts, CASH_TAGS))
    ocf_entry = _latest(_facts_for(facts, OCF_TAGS))
    if not cash_entry or not ocf_entry:
        return CashBurn()

    cash = cash_entry.get("val")
    cash_as_of = cash_entry.get("end")
    raw_ocf = ocf_entry.get("val")
    period = _period_days(ocf_entry)
    if cash is None or raw_ocf is None or not period or period <= 0:
        return CashBurn(cash=cash, cash_as_of=cash_as_of)

    ocf_annual = float(raw_ocf) * DAYS_PER_YEAR / period

    if ocf_annual >= 0:
        # Genera caja en operaciones: no hay runway finito que calcular.
        return CashBurn(
            cash=cash,
            cash_as_of=cash_as_of,
            operating_cash_flow_annual=ocf_annual,
            is_burning=False,
        )

    if cash <= 0:
        # Quema y no le queda caja: cero meses. Es un dato, no un hueco.
        months = 0.0
    else:
        months = float(cash) / (abs(ocf_annual) / 12.0)

    return CashBurn(
        cash=cash,
        cash_as_of=cash_as_of,
        operating_cash_flow_annual=ocf_annual,
        months_of_cash=months,
        is_burning=True,
    )
