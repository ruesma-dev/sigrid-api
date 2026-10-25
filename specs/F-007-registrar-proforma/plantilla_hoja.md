<!-- specs/F-007-registrar-proforma/plantilla_hoja.md -->
# Plantilla de hoja de proforma recomendada para los jefes de obra (propuesta para el humano)

**Propuesta** de F-007 v3 (2026-10-25), sacada de la estructura común de las cuatro hojas de ejemplo de la obra 0719
(`docs/referencia/proforma_ejemplo_*.md`). No es una norma hasta que el humano y Administración la aprueben. Lo que
la API necesita de cada campo está en [`contrato_proformas.md`](contrato_proformas.md) §2;
casar las partidas con el contrato y elegir los productos se hace en la bandeja de `proformas`.

## 1. Lo que las cuatro hojas tienen en común

- **Cabecera**: Nº ORDEN, MES («AGOSTO-26»), OBRA («719.<nombre>»), SUBCONTRATISTA (nombre, sin CIF), Nº CONTRATO.
- **Una fila por línea del contrato, en el orden del contrato**, también las que no tienen MES (a 0), y debajo las
  partidas fuera de contrato.
- **Columnas**: Partida (código de partida del presupuesto) · Medición de contrato · UD. · Trabajos realizados ·
  MEDICIÓN EJECUTADA ORIGEN / ANTERIOR / MES · P. unit. · IMPORTE EJECUTADO ORIGEN / ANTERIOR / MES · OBSERVACIONES ·
  IMPORTE TOTAL (= medición de contrato · precio).
- **Fila de TOTALES** con los importes ORIGEN, ANTERIOR y MES, y bloque de firmas (subcontrata, jefe de obra, jefe de
  grupo, administrativo).
- **Una pestaña por mes** en el mismo fichero (la del mes en curso y las anteriores).

## 2. Lo que varía y conviene fijar

| Observado en los ejemplos | Problema para el registro | Propuesta |
|---|---|---|
| Nº CONTRATO vacío (ZANELA) | Sin contrato no hay línea de contrato ni retención | Rellenarlo siempre; si no hay contrato, escribir «SIN CONTRATO» |
| Misma partida en varias líneas (suministro, elaboración, colocación) | La partida sola no identifica la línea (M33) | Mantener siempre la **medición de contrato** y el precio del contrato en su fila |
| Partidas fuera de contrato mezcladas, con medición 0 o vacía (BERENJENO, regularización, seguridad y replanteo) | Hay que distinguirlas de las de contrato | Bloque aparte «FUERA DE CONTRATO», con medición de contrato vacía |
| Columnas y hojas auxiliares (notas de albarán, resumen de horas, pilotes) | Ruido al leer | Notas solo en OBSERVACIONES; cálculos auxiliares en otra pestaña con nombre que no sea un mes |
| ORIGEN por encima de la medición de contrato (ferralla, muros) | Exceso sobre contrato | Se registra igual; la API avisa (`supera_pendiente`, `supera_contrato`) |
| Códigos con coma o con espacios («CI.1,11») | No casan con la partida de Sigrid | El código tal como está en el presupuesto de la obra |
| Nombre del fichero distinto del mes de la hoja | Confusión al elegir la pestaña | Fichero `AAMM_<obra>_<contrato>.xlsx`; pestaña con el mes `AAAA-MM` |
| Celdas de MES vacías cuando no hay ejecución | Ambiguo (¿0 o falta?) | MES = ORIGEN − ANTERIOR, siempre con número (0 si no hay) |

## 3. Plantilla propuesta

```text
Nº ORDEN: <n>            MES: <AAAA-MM>
OBRA: <código obra> <nombre>     SUBCONTRATISTA: <nombre>  CIF: <CIF>     Nº CONTRATO: <CTxxAA/NNNN o SIN CONTRATO>

LÍNEAS DE CONTRATO (todas, en el orden del contrato)
Partida | Medición contrato | UD | Trabajos realizados | Cant. ORIGEN | Cant. ANTERIOR | Cant. MES | P. unit. |
        Imp. ORIGEN | Imp. ANTERIOR | Imp. MES | Observaciones

FUERA DE CONTRATO (sin medición de contrato)
Partida | (vacía) | UD | Trabajos realizados | Cant. ORIGEN | Cant. ANTERIOR | Cant. MES | P. unit. | Imp. … | Observaciones

TOTALES                                         Imp. ORIGEN | Imp. ANTERIOR | Imp. MES
Firmas: subcontrata · jefe de obra · jefe de grupo · administrativo
```

Reglas: números como números (punto o coma decimal, sin texto en la celda); ORIGEN = ANTERIOR + MES en cada fila y en
los totales; el ANTERIOR es el ORIGEN de la pestaña del mes anterior; un contrato por hoja (si el subcontratista tiene
dos contratos en la obra, dos hojas). Añadir el **CIF** del subcontratista ahorra resolverlo por nombre (D4).
