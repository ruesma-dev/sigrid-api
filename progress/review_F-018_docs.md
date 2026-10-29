<!-- progress/review_F-018_docs.md -->
Revisión completa (pasada 1) del bloque de documentación y contratos, sobre HEAD `7ce2240` (azure-apps `f168a36`)

# F-018 · Revisión troceada: documentación y contratos con otros proyectos

- **Veredicto:** CHANGES_REQUESTED (siete cambios, todos de texto; el código no se toca)
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`). Este trozo no cubre tests, cobertura,
  fase RED ni mutación: van en otros trozos. Por encargo, ni `init.sh`, ni mutantes, ni red, ni Sigrid.
- **Alcance:** `contrato_albaranes.md` v8.4 (incluido el texto de albaranes de `7aae0ba`), `contrato_proformas.md`
  v1.3 (cabecera y §8 de `6d11dcd`), `docs/ARCHITECTURE.md`, docstring de `sigrid_albaran`,
  `azure-apps/sigrid_api.md` (`f168a36`, sin cambios posteriores en ese fichero) y `verificacion_manual.md`.
- **Cómo se verificó:** cotejo con el diff de código (`git diff dev`) y con las funciones puras ejecutadas en local
  (`importe_con_dto`, `texto_de_dto`, `porcentaje_de_dto`, `usa_precio_del_contrato`, `LineaAlbaranIn`,
  `ReceivedLine`). Cálculo puro, sin red ni BBDD.

## Checkpoints de este bloque

- [x] **Ejemplos ROUND_HALF_UP.** Todos cuadran con `importe_con_dto`: 1·18,625·0,6 → 11,18; 36·4,278·0,6 → 92,40 con
  `pre` 2,5666…; −0,4·1.275,68·0,975 → −497,52; 265·0,965 → 255,73; 0,3·12.825·0,99 → 3.809,03. Ejemplo de proformas
  (`tar` 4,278 al 40 %, 12,5 uds): v1.3 32,09 frente a v1.2 32,08. También cuadran los textos `40%`, `1,5%`, `21,45%`,
  `0,01%` y `100%`, y la lectura de `10+2,5`, `5` y `1.5%` como no legibles.
- [x] **Validación de `dto` (§2.2, §3.4).** Se rechazan `true`, `"40"`, `"10+5"`, 100,01, −1, 12,345 y NaN. Se
  aceptan 0 (sin descuento), 40, 100, 1,5 y 0,01. Cuadra con R4 y con el texto pegado de albaranes (`round(d, 2)`,
  0 < d ≤ 100).
- [x] **v8.4 §2.2, §2.3, §3.1 (respuesta, `impbru`), §3.2, §4.2, §4.3 y H8 frente al código.** Coinciden con el código:
  la vinculada con `dto` no aplica la opción C; la R15 exige dto legible > 0 y `tar` ≠ 0; `mov.pre` = `dcapro.pre`
  (línea 1059); `impbru` es el bruto de las líneas con descuento más el `tot` de las demás; el aviso de bruto compara
  con `ctrpro.tar` (±0,0001); `dto_distinto_del_contrato` trata «sin dto» como 0 y lo no legible como distinto; no hay
  SQL nuevo. Salvedad: cambio 4.
- [x] **Texto de albaranes (`7aae0ba`).** Está pegado tal cual. Solo se escaparon las barras `\|`. No choca con §2.2,
  §3.1 ni R1-R7: albaranes valida que la línea da el importe (±0,01) y la previa compara con tolerancia 0,05.
- [ ] **Estado de los contratos.** Los dos dicen «pendiente de acuse», aunque los acuses ya llegaron. Ninguno de los
  dos dice que F-018 está sin desplegar. Cambios 1 y 2.
- [ ] **v1.3 de proformas, cota a origen.** El «hasta un céntimo por línea» contra `importe_origen_cadena` es falso.
  Cambio 3.
- [x] **ARCHITECTURE y docstring.** Coinciden con el código: modo extendido, R15, avisos, serializador, traza
  `n_lineas_con_dto`, proforma que hereda R15 sin tocar `create_proforma_use_case.py`, y §Semántica 9 = D11 (P7).
  Salvedades: cambio 5 (clásico y directo) y la observación O1.
- [ ] **`sigrid_api.md`.** Marca F-018 como «PENDIENTE DE DESPLIEGUE» en §8.6 y §8.10, y §9.4 y §12 son correctos. Pero
  §8.6 contradice al código en el clásico y en `albaran-directo` (cambio 5), y §13/§10 tienen notas caducadas
  (cambio 6).
- [ ] **`verificacion_manual.md` V0-V5.** Lo que está bien:
  - solo V4 lleva `commit:true`, y con autorización expresa;
  - nunca usa `DELETE` y anula desde la UI;
  - V1a, V1b, V1c y las lecturas de V4 son SQL parametrizado con `?`;
  - las columnas existen: cotejadas con `sigrid_tablas.md` y con las listas `*_COLUMNAS` del código (`dca.synckey` y
    las de `mov` están en el código);
  - las llamadas a `sql/read` usan `parameters`/`max_rows` y paran si viene `truncated`;
  - los cuerpos coinciden con `AlbaranCompraRequest` y `ProformaRequest`;
  - barrido de sensibles sin hallazgos (patrones: CIF `[A-HJ-NP-SUVW]\d{7}[0-9A-J]`, `https?://`, `azurewebsites`,
    IPv4, `func-sigrid`, `rg-`): ni secretos, ni personas, ni proveedores, ni CIF; el usuario es `prueba`.

  Pero V3 da por buenos unos «sin avisos» que fallarán, y V4 fija la obra. Cambio 7.
- N/A **C1, C2, C3, C4, C4 bis y C4 ter.** Son de otros trozos de esta revisión troceada (encargo del líder): aquí no
  se ejecuta `init.sh`, ni tests, ni mutación.
- N/A **C3 bis.** F-018 no añade ni cambia nada en `docs/referencia/` (`git diff dev --stat`).

## Cobertura de este bloque (requisito → dónde)

| Requisito | Dónde queda cubierto |
|---|---|
| R27 | `verificacion_manual.md` V0-V5 y su lista en `current.md` (con el cambio 7) |
| R28 | contratos v8.4 y v1.3 (`02dc4ad`, más `7aae0ba`), ARCHITECTURE y docstring (`536ce9c`), `sigrid_api.md` (`f168a36`) |
| R2/R3 (ejemplos) | cotejados más arriba con `importe_con_dto` y `texto_de_dto` |

## Cambios requeridos

1. **`contrato_albaranes.md` l. 54 y l. 72-73: el estado está caducado.** Hay que tocar tres cosas:
   - Cambiar «**pendiente de acuse de albaranes**» por «acusada por albaranes el 2026-10-29». Es lo que pone
     `impl_F-018.md` l. 12 y sigue la forma de la v8.3.
   - Marcar como hecho el punto 6 («Poner al día lo suyo»), que albaranes ya escribió en `7aae0ba`.
   - Añadir «**pendiente de despliegue**» de sigrid-api. Hoy solo lo deja entrever el texto de albaranes
     (`ALTA_SIGRID_ENVIAR_DTO` apagada).
2. **`contrato_proformas.md` l. 9-10 y §8 (l. 419-427): lo mismo.** Hay que tocar dos cosas:
   - Cambiar «pendiente de acuse de `proformas`» por «acusada el 2026-10-29».
   - Decir que F-018 está **pendiente de despliegue**, como decía la v1.2 de F-016 hasta `6d11dcd`.

   Sin eso, la v1.3 está en presente y parece vigente: hoy la API no escribe esas líneas como Sigrid.
3. **`contrato_proformas.md`: la cota a origen está mal.**
   - **Dónde:** l. 16-17 (punto 2: «hasta un céntimo por línea […] a origen, entre el ORIGEN de la hoja y
     `cadena.importe_origen_cadena`») y l. 264-265 (§3.1, «esos céntimos»).
   - **Por qué:** `importe_origen_cadena` = Σ round(`canoriori`·`pre`, 2), y el `pre` neto sale de la cantidad del
     MES. La desviación se multiplica por `canoriori`/`cantidad`.
   - **Medido** (`ctrpro` 36 uds, `tar` 4,278 al 40 %; el `tot` del MES es igual al de la v1.2):

     | MES | `canoriori` | v1.3 | v1.2 | Diferencia |
     |---|---|---|---|---|
     | 1 | 30 | 77,10 | 77,00 | 10 céntimos |
     | 0,5 | 30 | 76,80 | 77,00 | 20 céntimos |
     | 2 | 36 | 92,34 | 92,40 | 6 céntimos |

   - **Qué escribir:** que a origen la diferencia no está acotada a un céntimo y crece con `canoriori`/`cantidad`. Y
     que el `importe_anterior_cadena` del mes siguiente la hereda, porque lee esos `pre`.
   - **Para el humano:** el código cumple R21 (P8 = a). Si esa magnitud es aceptable para el cotejo de `proformas` es
     decisión suya; aquí solo se pide que el contrato diga la verdad.
4. **`contrato_albaranes.md` l. 68-69 (punto 4) y l. 355-357 (§3.1): falta una condición.** Los dos sitios dicen
   «un céntimo; la tolerancia de 0,05 lo cubre» sin la condición `cantidad` ≤ `ctrpro.can`, que sí está en §2.2.
   - **Medido:** con el `ctrpro` del cambio 3, una vinculada de 1.000 uds casa por la opción C. Con R15 da 2.566,80
     frente a 2.566,67 aprobados: 0,13 > 0,05, así que sv9 marcará `importe_distinto` ⇒ `revisar`.
   - **Qué escribir:** la condición, y que fuera de ella (o con un `ctrpro` que no cumple `pre` = `tot`/`can`) sv9
     puede ver `importe_distinto`.
   - **También en** `azure-apps/sigrid_api.md` §8.6 (l. 1168, «puede mover 1 céntimo»).
5. **`azure-apps/sigrid_api.md` l. 1156-1157: contradice al código.** Dice que el clásico y `albaran-directo` «no
   lo admiten (400 sin código)». No es así:
   - `ReceivedLine` y `DirectLine` no llevan `extra="forbid"`.
   - `ReceivedLine.model_validate({..., "dto": 40})` valida y **descarta la clave en silencio**.
   - El riesgo: quien mande el bruto con `dto` a esas rutas obtiene la línea sin descuento y sin error.

   Hay que escribir que lo ignoran; solo `sigrid/proforma` da 400. En `docs/ARCHITECTURE.md` l. 130, «no admiten
   `dto`» debe decir lo mismo: «lo ignoran (sin `extra="forbid"`)».
6. **`azure-apps/sigrid_api.md` §13 y §10: notas caducadas.**
   - §13, l. 1780: dice «**F-016 (implementada, pendiente de revisión y de despliegue)**». Contradice §8.10.1 («F-016,
     desplegada el 2026-10-28»), que `f168a36` sí corrigió. Hay que actualizarla.
   - §13: falta la entrada de F-018 (pendiente de despliegue).
   - §10, l. 1657: la fila de `proformas` cita el contrato «v1.2». Debe citar la v1.3 (F-018, pendiente de despliegue).
7. **`verificacion_manual.md` V3 y V4 (y su resumen en `current.md` l. 18-19).**
   - **V3:** promete «sin avisos» para r3 (y sin avisos de precio ni de dto para r1), pero los cuerpos no llevan
     `partida`. Si el `ctrpro` tiene partida, sale `sin_partida_en_linea_con_partida`. Y `$B[7]` (la cantidad de un
     albarán pasado) puede superar lo pendiente, con lo que sale `supera_pendiente`. Hay que acotar a «sin avisos de
     precio ni de dto» y decir que esos dos son ajenos a F-018.
   - **V4:** graba con `$cuerpoA`, es decir, la obra 0692 y el CIF real de V1a. Design §V dice «en la obra que diga el
     humano». Hay que escribirlo en V4: el humano fija la obra y el proveedor antes de autorizar.

## Observaciones (no bloquean)

- **O1.** ARCHITECTURE l. 118: «Con descuento efectivo, `precio` es el bruto» es inexacto en la R15, donde `precio` es
  el neto del `ctrpro`. La frase siguiente lo aclara; bastaría con decir «con `dto` pedido».
- **O2.** La respuesta vuelca `dto` como `40.0`, no `40` como en el ejemplo de §3.1. Es el mismo número JSON y no
  rompe a nadie.
- **O3.** Las notas «PENDIENTE DE DESPLIEGUE (F-015)» de `sigrid_api.md` (l. 796, 824, 1115 y 1767) están caducadas,
  pero son del cierre de F-015 (`current.md` l. 103), no de F-018.

## Automejora (propuesta, no aplicada)

Añadir a este bloque de revisión: «toda cota numérica de un contrato ("un céntimo", "la tolerancia lo cubre") se
comprueba con un contraejemplo fuera de sus supuestos». Los cambios 3 y 4 solo se ven así.
