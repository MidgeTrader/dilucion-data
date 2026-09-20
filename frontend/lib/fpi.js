// FPI (Foreign Private Issuer): sus insiders estan exentos de la Section 16,
// asi que no presentan Form 3/4/144. La pata de distribucion del
// pump-and-dump es invisible en los filings — de ahi el rojo.
//
// El backend deriva el booleano en backend/fpi.py a partir de los form_type
// ya almacenados en filings_history. Aqui solo se decide como pintarlo.

/**
 * Construye la fila "FPI" para las tarjetas de perfil del ticker.
 *
 * @param {boolean|null|undefined} isFpi - Valor derivado por el backend.
 * @returns {{value: string, highlight?: string, title?: string}} Fila para
 *   InfoCard (usa `highlight`/`title`) o para la sidebar (mismos campos).
 *   Si el dato falta devuelve '—' sin color: "desconocido" no es "no".
 */
export function fpiRow(isFpi) {
  if (isFpi == null) return { value: '—' };
  return {
    value: isFpi ? 'YES' : 'NO',
    highlight: isFpi ? 'text-accent-red' : 'text-accent-green',
    title: isFpi
      ? 'Foreign Private Issuer — exento de Section 16: sin Form 3/4/144'
      : 'Emisor domestico — obligado a presentar Form 3/4/144',
  };
}
