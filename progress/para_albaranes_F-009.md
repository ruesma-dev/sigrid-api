<!-- progress/para_albaranes_F-009.md -->
# Para el agente de albaranes · huecos de `contrato_albaranes.md` que os tocan

Del líder de sigrid-api, 2026-10-05. Contrato completo y numeración estable de huecos en
`sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md` §5 (no lo copiéis: enlazad).
sigrid-api resuelve en la **spec v5 de F-009** los suyos (H2, H3, H10-H19, H21, H26, H27, H32,
H33); el estado de cada uno queda en el §5 del contrato.

## Decisiones del humano (2026-10-05)

| Hueco | Decisión | Qué os toca |
|---|---|---|
| H4 | F-009 conserva «imputable» (`tip 1`, `tipdes 0`, `tipvis` 0/1) y no exige hoja | **F-049**: añadir `tip, tipdes, tipvis` a `SQL_PARTIDAS_POR_OBRA` y sacar de la lista lo no imputable |
| H5 / sin partida | **«Almacén» no existe como concepto**: es una línea **sin partida** (una o varias por albarán), que luego se pasa a partida en Sigrid al desacopiar. F-009 v5.1 quita el campo `almacen` de la línea: `partida` ausente o `null` ⇒ `paride` 0 (nunca heredada). El almacén físico (`almide`) lo sigue poniendo sigrid-api en todas las líneas | **F-053**: no mandar `almacen`; omitir `partida` cuando `codigo_partida_final` esté vacío. **F-051**: «sin partida» y «almacén» son lo mismo en el visor |
| H8 | Negativas solo con cantidad **e** importe negativos; signos opuestos ⇒ `revisar` (`signo_incoherente`); descuentos comerciales, a mano por ahora. F-009 rechaza además el precio negativo con el fallo de línea `precio_negativo` | **F-053** R10/R12 y mapeo `precio_negativo` → `revisar` |
| H9 | Se mide ya, por lectura (M17 en la repetición de T0 de F-009). Si el escritorio marca en vez de borrar, F-009 excluye anulados en la idempotencia | **F-053**: si marca, `ALB-{document_id}-{n}` tras cada `anulado` y excluir anulados en R14. Esperad al resultado |
| H17 | Depende de M3: si quedan códigos repetidos entre imputables, la línea llevará `paride` opcional | **F-049**: conservar el `ide` de cada partida, por si acaso |
| H20 | El modo real no se abre sin M9 cerrada; si MA9999 mueve stock, se decide entonces | Nada hasta M9 |
| H29 | Confirmado: las vinculadas sin importe no se mandan | Nada |
| H30 | No se toca sv6 ahora: el ALM impreso sigue como sin vincular | Nada |
| H19 | **sigrid-api no rechaza fechas futuras**: la plausibilidad de la fecha es solo de la app | **F-053**: `fecha_no_plausible` ⇒ `revisar` (futura o anterior a hoy − 365 días) |
| H31 (N4) | Mandar `cod_contrato` siempre que la valoración tenga contrato, aunque no case ninguna línea: F-009 ya lo admite (enlaza `dca.ctride` y no toca la medición) | **F-053** R12 |
| N8 | Aviso nuevo `iva_de_otro_proveedor`: informativo | **F-053** |
| N9 | Si M18 sale libre, `referencia_linea` se escribe en `dcapro.refent` (≤24, visible en la UI de Sigrid) | **F-053**: `referencia_linea` ≤ 24 |
| N12 | Códigos nuevos: `obra_de_empresa_no_permitida` → `error`, `precio_negativo` → `revisar`, `paride_no_valido` → `no_admitido`; avisos nuevos informativos | **F-053** (tabla de H25) |

## Huecos que son solo vuestros (propuesta del contrato §5, aceptada)

- **F-053**: H1 (`usu` = `ALTA_SIGRID_USUARIO`; `usuario_no_valido` → `error`), H5 (sin
  `partida` para toda partida vacía; retirar `linea_sin_partida`), H6 (longitudes y descripción
  vacía ⇒ `no_admitido`), H7 (en vinculadas no mandar `unidad` ni `descripcion`), H12, H13
  (`almacen_de_obra_no_resuelto` → `no_admitido`), H14 (precio a 6 decimales), H16 (guardar solo
  lo que se usa de la respuesta), H18 (comparar totales también en `idempotente`), H19
  (`fecha_no_plausible` ⇒ `revisar`), H21 (CIF normalizado), H22 y H24 (códigos a
  `no_admitido` / `error`), H25 (tabla de avisos al día con F-009 v4/v5), H26 (orden de líneas).
- **F-049**: H4, H17 y H23 (no repartir si alguna parte queda a 0).
- **F-051**: H5 (R10-R12: «sin partida» deja de ser un estado distinto del almacén).

**Importante:** F-053 v5 está alineada con F-009 **v2**. Hay que realinearla con la **v5.1**
(aprobada por el humano el 2026-10-05; códigos y campos nuevos en el contrato). Queda pendiente
una sola repetición de T0 en sigrid-api (M3, M9, M16, M17, M18…) que puede ajustar H9, H10, H17 y
H20: las reglas condicionales están marcadas en la spec.
