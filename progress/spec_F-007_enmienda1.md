<!-- progress/spec_F-007_enmienda1.md -->
# F-007 · Enmienda 1 de la spec (2026-10-26)

Autor: spec-author. Fuente: las decisiones del humano del 2026-10-26 sobre `review_F-007_proforma.md` (D1, D2, D4 y
O3) y `review_F-007_nucleo.md` (O1). Solo se ha tocado `specs/F-007-registrar-proforma/`. Topes: requirements 150/150
y design 248/250.

## Cambios

- **requirements.md (v3.1)**
  - **R14**: el respaldo sin `ctrpro_ide` es ahora **estricto** por `partida` (código) y precio (±0,0001), sin volver
    atrás si un filtro deja cero. Una línea da esa; ninguna da `linea_no_es_del_contrato`; varias dan `linea_ambigua`
    con `candidatos`, y desempata `proformas`. Medición, unidad y `producto` ya no cuentan, y se quita la cifra M33
    del embudo antiguo. Con `ctrpro_ide`, sin cambios.
  - **R8**: una línea «está» en un contrato por su `ctrpro_ide` o, sin él, por partida y precio, con la misma regla
    que R14.
  - **R17**: el IVA sale del `ctrpro` «haya o no plantilla»; sin plantilla, naturaleza, cuenta y analítica 0 (D1).
  - **R28**: R23 se repite con LP5, y una fila de otro contrato o que no es proforma da `referencia_en_conflicto`
    (D2). Antes decía «repetir R23 y R24 con LP1», que era ambiguo.
  - **R24 (O3)**: «sin `otra_del_mes`» en la condición de `existente`. Con `otra_del_mes`, haya una del mes con el
    mismo total o con otro, sale el aviso y sigue. Así lo hace ya el código y así lo enseña el ejemplo del contrato.
  - Para no pasar de 150 líneas he compactado la introducción.
- **design.md (v3.1)**
  - §Costuras 1-2 nombran ahora `cifras_serie`, `campo_max_lineas`, `error`, `siguiente_cod(..., cifras=)` y
    `PERFIL_PROFORMA` (O1). La tabla de ficheros a modificar recoge `siguiente_cod`.
  - Costura 3: para R28, el gancho ve la fila de E1 antes de su salida idempotente.
  - Costura 4: el IVA del `ctrpro` también sin plantilla.
  - §Contrato y §Líneas describen la regla nueva, con las cifras de M33 de partida + precio: 88,4 % única, 9,2 %
    varias y 2,3 % ninguna. M32 queda anotada como medida con partida y medición. D6 ya no habla de embudo.
- **contrato_proformas.md v1.1**
  - Cabecera nueva, nota ² reescrita y filas `partida`, `medicion_contrato` y `otra_del_mes` de §2.
  - En §8, una línea de cambios fechada.
- **tasks.md**: nuevo lote E (T25-T32), que va antes de T20-T24. Incluye R8/R14, R17, R28, los defectos D3 y D5 de
  la revisión y la mutación.

## Para validar (humano o líder)

1. **Sin `partida` en el respaldo, no casa ninguna** y sale `linea_no_es_del_contrato`. Es mi lectura de «filtro
   estricto por partida». La otra opción sería filtrar solo por precio.
2. **R24/O3**: he dejado escrito que `otra_del_mes` se salta también la `existente` del mismo total. Así lo hace hoy
   el código, pero no estaba entre las decisiones dictadas.
3. Las tareas de D3 y D5 (T29-T31) son ajustes del código a la spec y no requieren decisión, pero entran en el lote E.
4. Hay que avisar a `proformas` de la v1.1 del contrato.
