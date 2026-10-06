<!-- progress/spec_F-009.md -->
# Spec F-009 · Alta de albaranes de compra para el pipeline (PRE-1 de albaranes F-053) — v8.2

Spec-author. v1 y v2 del 2026-10-01 (respuestas del humano a la PARADA 1); v3 del 2026-10-02 (T0); v4 del 2026-10-02 (respuestas a N1-N3); **v5 del 2026-10-05** (huecos de `contrato_albaranes.md` §5 y decisiones del humano; §v5); **v5.1** del mismo día (respuestas a N4-N12; §v5.1); **v6** del mismo día (repetición de T0 y decisiones del humano; §v6); **v7** del mismo día (T0b-bis y decisiones del humano; §v7); **v8 del 2026-10-06** (T0b-ter, T0b-quater, contrato v7.1 y decisiones del humano; §v8); **v8.1 del mismo día** (T0b-quinquies, cierre de T0 y retirada del script; §v8.1); **v8.2 del mismo día** (ajuste puntual durante el lote B: importes, ε del stock y §Equivalencia; §v8.2). Rama
`feature/F-009-alta-albaran-compra` desde `dev` (2a5ac24). Estado `spec_ready`, `sdd`, rigor
`critico`, prioridad 7 (antes que F-007 y F-008). Spec en `specs/F-009-alta-albaran-compra/`.
**No se ha llamado a la API, ni a Azure, ni al SQL Server**: lo que depende de cómo trabaja el
escritorio de Sigrid queda como medición de solo lectura (T0) o como verificación manual.

`bash harness/init.sh` en verde **con el venv del proyecto**. Desde una sesión con `VIRTUAL_ENV`
heredado de otro repositorio sale en rojo (`azure.functions` ausente): el portero respeta un
venv ya activado. No es un fallo del repo; se lanza sin esa variable.

## v8.2 (2026-10-06): ajuste puntual durante la revisión del lote B

Spec-author, a petición del líder. Solo spec y contrato (redacción); sin código, tests ni `tasks.md` (ninguna
verificación cambia: R17 y R19 siguen cubiertos por T5-T7 y R33 por T12). Origen: `review_F-009_loteB_2.md`
(§«Decisión 1», §«Decisión 11», O2) e `impl_F-009_loteB.md` (decisiones 1 y 11).

1. **Importes de la vinculada: opción C** (humano, 2026-10-06; review §Decisión 1). `pre`, `tar` y `dto` del `ctrpro`
   solo si |`precio` − `ctrpro.pre`| ≤ 0,0001 **y** `round(cantidad·precio, 2)` = `round(cantidad·ctrpro.pre, 2)`
   (`Decimal`, `ROUND_HALF_UP`, H33); si no, vía de `precio_distinto_del_contrato` (`pre` = `tar` = `precio`, `dto`
   `''`, aviso). `tot` = `round(cantidad·pre, 2)` siempre: la fila es coherente y el total es el aprobado. Descartadas A
   (`cantidad·precio`: `tot` ≠ `can·pre` escrito en silencio) y B (`cantidad·pre` sin más: descuadre de hasta
   0,0001·|cantidad| que sv9 marcaría `importe_distinto`). Alineados en la misma regla R17, design §Importes y el
   contrato §2.2 y §3.1 (antes discrepaban), más §3.2 (cuándo salta el aviso) y la fila H14 de §5: **solo redacción**,
   sin cambio de forma, campos, códigos ni estados; línea v8.2 en la cabecera del contrato. Coste aceptado: algún aviso
   más y la pérdida de `tar`/`dto` del contrato en líneas grandes con diferencia mínima. **Para el implementer**: el
   código del lote B aplica A (`importe_linea` con `precio`, decisión 1 del informe); hay que pasarlo a C.
2. **Stock con residuo binario** (review §Decisión 11; cambio requerido 1). R19: con |`stock + can`| < ε = 1e-6 se
   conserva el PMP y se escribe `almcan` 0; `almcan`/`almpma` son «Real» y se comparan con tolerancia. Sin regla nueva:
   un residuo de 1e-17 *es* el 0 de R19. design §`prepma` remite a ese ε (`siguiente_balance`).
3. **§Equivalencia (R33, T12; O2)**: se declaran `con.res` (128 aquí, 200 en el clásico) y `mov.almpma` con stock final
   0 (aquí se conserva el PMP; el clásico pone `pre`, `create_purchase_albaran_use_case.py:360`). La opción C no añade
   diferencia: en el dominio de R33 (`precio` = `ctrpro.pre`) escribe `pre`, `tar`, `dto` y `tot` como el clásico, salvo
   los empates de H33 ya declarados.

Topes: `requirements.md` 150/150 (cabecera compactada para el renglón de más de R19) y `design.md` 250/250 (§`prepma` y
§Condicionales resumidos, con enlace a §v8.1 y §v6-§v8.1). **Abierto para el humano**: nada nuevo; confirmar solo que
la redacción de §3.2 del contrato (cuándo salta `precio_distinto_del_contrato`) entra en «solo redacción» para F-053.

## v8.1 (T0c): resultado de T0b-quinquies (M14e, 2026-10-06), cierre de T0 y retirada del script

Spec-author. Solo spec; sin llamar a la API, Azure ni el SQL Server. Fuente: el fichero de resultados del humano
(`%TEMP%`, 2026-10-06 14:31; **no** se versiona: lleva datos de negocio). Aquí solo cifras agregadas y conclusiones.
Definición de M14e: `impl_F-009_T0a_quinquies.md` (APPROVED en la segunda pasada: `review_F-009_T0a_quinquies.md`).

### Resultado

| M | Resultado agregado | Decisión en la v8.1 |
|---|---|---|
| M14e | Los 50 `mov` de albarán más recientes (7 albaranes, 6 productos). Media ponderada global con el stock anterior de todos los almacenes: **2 de 34 entradas (5,9 %)** y **4 de 16 devoluciones (25,0 %)**; sus variantes (stock global posterior, `canent − cansal`, `prc`) empatan; solo el stock del almacén, 0 %. Comprobaciones de la muestra al 100 % (almacén en `proalm`, cadena de `almcan`). El producto de la muestra (QA9999) tiene > 4 M unidades en 147 almacenes: una entrada de 25 apenas mueve la media global y el `prepma` real cambia en la tercera cifra | **Refutada** la media global (≥ 95 % exigido). Regla nueva (abajo) |
| M14, M14c, M14d (repetidas) | `dcapro.prepma` = `mov.prepma` 100 % (8.734 líneas desde 2026-09); sin `mov`, 0 en el 99,5 % (2.914 de 2.930); `mov.prepma` = PMP del almacén antes de la entrada 9,7 % (842 de 8.670); = `prepma` del `mov` anterior o siguiente del producto 29,5 %; forma de pago y efecto del albarán anterior 94,2 % / 97,7 % | Sin cambios (R21, M14b); el 9,7 % se explica abajo |

### Regla nueva de `prepma` (decisión del humano, «sí», 2026-10-06)

`mov.prepma` (y `dcapro.prepma`, igual el 100 %) = **el `almpma` del último `mov` del mismo producto y almacén antes
de la línea**: el PMP del almacén vigente en el momento del alta; encadenado si el albarán lleva varias líneas del
mismo par; sin `mov` anterior, 0; sin `mov` (`tipmov` 0), `prepma` 0 como en la v8.

- **Evidencia**: en el albarán más reciente de la muestra (5 `mov` consecutivos de QA9999 en un mismo almacén),
  `prepma(n)` = `almpma(n-1)` en 4 de 4; coincide con la primera pasada de T0 (M14: «el del escritorio coincide con el
  PMP vigente del almacén»).
- **Por qué el histórico da poco** (M14c: 9,7 %): al entrar un albarán con fecha anterior, el escritorio recalcula los
  `mov` posteriores (M10) y reescribe su `almpma`, pero el `prepma` queda congelado con el valor del alta. En el albarán
  anterior de la muestra (ya recalculado) la igualdad no se da.
- **Estado**: hipótesis **coherente con los datos, no demostrada sobre el histórico**. Verificación manual en **T22**
  (primer commit autorizado: comparar con un albarán del escritorio dado de alta el mismo día en el mismo almacén) y
  en **T24** (primera alta real: `prepma` frente al `almpma` del `mov` anterior; consulta en §Manuales). Si no
  cuadra, solo difiere ese campo (no toca stock, importes ni medición): ficha correctiva.

### Lo que se simplifica

El valor ya lo lee L12 (último `mov` del producto y almacén, para el balance; E7 dentro, con `UPDLOCK`). Se retira
todo lo que solo servía a la media global: **L12b** (`prepma` anterior del producto), **L12c** (stock global),
**E7b** (su lectura dentro de la transacción **sin** `UPDLOCK`) y su riesgo, y la función **`siguiente_prepma`**
(`siguiente_balance` devuelve también el PMP de partida). Desaparece la decisión (b) de §v8 «Preguntas abiertas».

### Decisiones del humano aprobadas (2026-10-06)

- (a) Campo `naturaleza` **retirado** (no se conserva «si viene, manda»).
- (c) `cuacomcod` sin una única `cua` en la empresa del albarán ⇒ `naturaleza_no_valida` (configuración), sin código nuevo.
- `tex` **vacío** en las sin vincular (§Reseteo).
- (b) E7b sin `UPDLOCK`: **desaparece** con la simplificación.

### Qué cambió en la spec

| Cambio | Dónde |
|---|---|
| `prepma` = PMP de partida del almacén (hipótesis, verificación manual); fuera L12b-c, E7b, `siguiente_prepma` y su riesgo; descartada la media global | R19, R26, R35; design §Ficheros a crear, §`prepma`, L12, E7, §Flujo, §Condicionales, §Riesgos; tasks T4, T5, T10, T22, T24 |
| T0 cerrada: §Condicionales solo con lo que se verifica a mano (T22-T24) | design §Condicionales; R35; tasks (precondición, T0a-quinquies, T0b-quinquies y T0c hechas) |
| Script de mediciones y su prueba retirados (N3) en un commit propio de T0c; quedan en el historial | `scripts/medir_f009_t0.py`, `tests/test_f009_t0_script.py` |
| Contrato (solo estado, sin tocar la forma de §2-§4, congelada para F-053): cabecera v8.1, §0, H11, H28 y la fila «Abierto» de §8 | `contrato_albaranes.md` |

R21 y T6 no cambian de texto (`dcapro.prepma` = `mov.prepma`; `mov` con `prepma` de §`prepma`). §Equivalencia
mantiene `prepma` como diferencia declarada (el clásico escribe el PMP resultante). Topes tras la v8.1
(`python -m harness.tamano --feature F-009`): `requirements.md` 150/150 y `design.md` 249/250.

### Preguntas abiertas y notas

**Ninguna pregunta abierta.** Notas que siguen en pie (de §v8, sin cambios): el hallazgo para Administración (el
maestro de `MA9999` lleva `MA1501`; fuera de F-009) y la nota de M19 (el «0 sin alta» no prueba que no haya altas sin
`log`). F-053 no cambia. Siguiente: aprobación del humano de la v8.1 y PARADA 1 de implementación (T1).

## v8: resultados de T0b-ter y T0b-quater (2026-10-06) y decisiones del humano

Spec-author. Solo spec; sin llamar a la API, Azure ni el SQL Server. Fuentes: los dos ficheros de resultados del
humano (`%TEMP%`, 2026-10-06 00:56 y 09:58; **no** se versionan: llevan datos de negocio), el contrato v7.1
(`2631b1a`, H34 y H35) y las decisiones del humano del 2026-10-06. Aquí solo cifras agregadas y conclusiones; ni
proveedores, ni usuarios, ni filas, ni importes. Definiciones de M14c y M16c: `impl_F-009_T0a_ter.md`; de M14d, M16d
y M19: `impl_F-009_T0a_quater.md`. Las cifras son de T0b-quater salvo indicación (T0b-ter da lo mismo ±0,1 %).

### Resultados y decisión

| M | Resultado agregado | Decisión en la v8 |
|---|---|---|
| M9 (`XA9999`) | Empresa 1, julio-septiembre: `XA9999` con `tipmov` 1, `mov` en 1.049 de 1.065 (98,5 %); MA9999 y QA9999 100 %, SB9999 99,9 %, SM9999 98,9 %. Septiembre: `tipmov` 1 ⇒ 99,8 %; 0 y −1 ⇒ 0 % | **Cerrada**: la regla `mov` ⇔ `pro.tipmov` = 1 vale para los tres productos de la lista blanca (R19) |
| M14 | Repite T0b-bis: `dcapro.prepma` = `mov.prepma` 100 % (8.538); forma de pago y efecto del albarán anterior 94,1 % / 97,6 % frente al 81,3 % / 87,0 % del maestro; sin vincular de 2026, las mismas proporciones; ninguna columna fuera del reseteo se arrastra | Sin cambios (R21, M14b) |
| M14c | `prepma` de la línea sin `mov`: 0 en 2.871 de 2.887 (99,4 %); nunca `pro.prepma`. `mov.prepma` (8.507): = PMP del almacén antes de la entrada 10,8 %, = PMP resultante 2,5 %, = `pro.prepma` 0,5 % | **Cerrada sin `mov`** (0; R21). Con `mov`: no es un PMP del almacén ⇒ M14d |
| M14d | `mov.prepma` («Precio Medio Compra» **del producto**) = el del `mov` anterior del producto en cualquier almacén 29,8 %, = el del siguiente 29,9 %, = `mov.pre` 0,7 %; entre el anterior y el precio 69,7 % (compatible con una media ponderada); el `mov` anterior es de albarán de compra el 100 % | **Abierta → M14e** (T0b-quinquies): media ponderada global `(prepma_ant·stock_global_ant + can·pre)/(stock_global_ant + can)`, stock global = suma del último `almcan` por almacén. Regla escrita **condicional a M14e** (design §`prepma`): ≥ 95 % ⇒ fijada; si no, mejor aproximación con riesgo declarado y verificación en T22 y T24 |
| M16 / M16b | Repiten T0b-bis (vinculadas, `caaide` del `ctrpro` 100 % y 99,9 %; orden de almacén confirmado; `dcaproana` 0 de 189.532) | Sin cambios |
| M16c (T0b-ter) | `cueide` = `cua` del `cuacomcod` de la naturaleza de la línea: 97,9 % del total, 100 % en MA9999, QA9999 (99,9 % con partida) y XA9999; ninguna `cua` repetida ni de otra empresa. `numemp` 0 en las 170 naturalezas usadas (99,9 % de las líneas; el resto, sin naturaleza), ninguna de la empresa ni de otra. Analítica con «lo que sigue al primer `.`»: 86,8 % del total; XA9999 0 % (su `caagascod` `CDXA01` no lleva `.`); MA9999 con partida 92,3 % (las `MA1501` fallan) | **P2, P3 y P4 cerradas**: `numemp` ∈ {0, empresa}; `cueide` de la `cua` del `cuacomcod` (en MA9999, la de la línea y la del producto coinciden); la regla de la v7 cambia de sufijo (M16d) |
| M16d (T0b-quater) | Sufijo = `caagascod` **entero** si no lleva `MOD.`: XA9999 5.429 de 5.430 y 91 de 91. Por grupo con la regla ampliada: QA9999, SB9999, SM9999 y XA9999 98,5-100 % (100 % con partida). MA9999: con `MA99` (`MOD.CDSB37`) 23.216 de 23.217; con `MA1501` (`MOD.CDMA15`) 85,5 %, y el resto de esas líneas ya va a `CDSB37`. Ninguna `caa` repetida por (centro, código). Control: los `ctrpro` cumplen la misma regla el 96,3 %. La naturaleza de MA9999 no la fija ninguna dimensión sola (obra 79 %, proveedor 80 %, usuario 76 %) | **Cerrada** (H10): `caa` del centro de la línea con `<obra>.<caagascod sin el prefijo MOD.>`; ninguna ⇒ `analitica_no_resuelta` (R15, design §Analítica) |
| M19 (H35) | Vinculadas desde 2025 (98.431): `cod2` = el del `ctrpro` 100 % de las que lo traen (el 10,3 %, ambos vacíos); `dncide` y `dncproide` iguales 98,8 % (el resto, ambos 0). Sin vincular con planificación: `cod2` = el de su `dncpro` 100 %. Sin vincular sin planificación: ninguna regla para el `cod2` (la mejor, la línea anterior de la misma obra y producto, 67,2 %) | **Cerrada**: vinculadas copian `cod2`, `dncide` y `dncproide` del `ctrpro` (R12); sin vincular, vacíos (§Reseteo; decisión del humano) |
| M19 (altas) | Líneas de MA9999, QA9999 y XA9999 desde 2025-09 (48.788): 19 usuarios de alta, todos personas; ninguno técnico ni la API; todos en `usu`. El albarán de la API de junio no tiene genéricos | Informativa: no hay altas automáticas previas de genéricos con las que compararse |

### Decisiones del humano aplicadas (2026-10-06)

- **H34** («ok»): la naturaleza de las sin vincular sale del mapeo de configuración
  `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO` (sexta App Setting, defecto `{}`, despliegue `{"MA9999": "MA99",
  "QA9999": "QA99", "XA9999": "XA99"}`, solo objeto JSON), **nunca** del maestro (`MA9999` tiene `MA1501`). Sin
  entrada o naturaleza que no vale ⇒ `naturaleza_no_valida`. **Consecuencia escrita** (design §Analítica, §Riesgos):
  el escritorio imputa ~42 % de las MA9999 a `CDMA15`; el alta automática las lleva todas a `MA99`/`CDSB37`
  (criterio de negocio: «códigos genéricos»).
- **Campo `naturaleza`**: **se retira** (propuesta del humano). El contrato v7.1 lo conservaba «si viene, manda»,
  pero a confirmar; no tiene sentido mantenerlo: F-053 no lo manda, negocio dice que las naturalezas específicas «a
  efectos prácticos no se usan» y permitiría a un llamante saltarse el mapeo. Con `extra="forbid"`, mandarlo da 400
  sin código. Menos superficie (validador de R6, L15a por `ide`, tests y mutantes).
- **H35** confirmada por medición (M19).
- **Contrato** (regla nueva del humano): «el contrato solo se toca para actualizar consumos». Escrita en la
  cabecera de `contrato_albaranes.md`: las reglas, la validación, la escritura y los códigos los cambia sigrid-api en
  su spec; albaranes (u otro consumidor) solo edita lo que consume (campos que manda, origen y mapeo de respuestas y
  códigos a sus estados).

### Qué cambió en la spec

| Cambio | Dónde |
|---|---|
| Sexta App Setting, `parse_string_dict` (objeto JSON o no arranca), fase RED en R10 | R10, R34; design §Ficheros a modificar; tasks T2, T19 |
| Naturaleza del mapeo; campo `naturaleza` retirado; `numemp` ∈ {0, empresa}; `cueide` de la `cua` del `cuacomcod`; L7 sin `natide`; L15a por código; L15c completa | R6, R13, R13b; design §Modelo, §Analítica, L7, L15a-c, §Códigos; tasks T3, T6, T7, T21 |
| Sufijo de la analítica sin `MOD.` (entero si no lo lleva), `sufijo_analitica` | R15; design §Analítica; tasks T5 |
| `cod2`, `dncide` y `dncproide` del `ctrpro` en las vinculadas; diferencia declarada en R33 | R12; design §Filas, §Reseteo, §Equivalencia; tasks T6, T12, T22 |
| `prepma`: 0 sin `mov`; `mov.prepma` = media ponderada global [M14e]; L12b-c y E7b (sin `UPDLOCK`), `siguiente_prepma` | R19, R21, R26, R34; design §`prepma`, L12b-c, E7b, §Condicionales, §Riesgos; tasks T4, T5, T6, T10, T22, T24 |
| T0b-ter y T0b-quater hechas; T0a-quinquies (M14e) y **T0b-quinquies** `--solo M14`; T0c vuelca en la v8.1 y retira el script | tasks; R35 |
| Contrato: cabecera con la regla del humano y la v8; §1.3, §2.2-§2.4, §3.3, §3.4, §4.3, H10, H11, H20, H28, H34, H35, §6.f y §8 (todo absorbido) | `contrato_albaranes.md` |

Topes tras la v8 (`python -m harness.tamano --feature F-009`): `requirements.md` 150/150 y `design.md` 249/250.
Para caber: `elegir_modo_albaran` pasa de bloque de código a prosa (misma regla, R1); las cifras de la analítica y de
`prepma` viven aquí; §Condicionales en prosa; se compactaron §Respuesta, §Devoluciones, §Riesgos y R10, R13b, R15,
R19 y R21. Ninguna regla se ha quitado.

### Preguntas abiertas y notas

1. **M14e** (T0b-quinquies): el implementer la añade al script (T0a-quinquies); el humano lanza `--solo M14`. Con
   ella, T0c (v8.1) y la retirada del script.
2. **Para validar** (decisiones del spec-author): (a) campo `naturaleza` retirado, no conservado; (b) E7b (`prepma`
   anterior y stock global) se lee **sin** `UPDLOCK` dentro de la transacción, porque bloquear todos los `mov` de un
   genérico escalaría a tabla; el precio es que un alta simultánea del escritorio puede desviar ese `prepma`;
   (c) `cuacomcod` sin una única `cua` en la empresa ⇒ `naturaleza_no_valida` (es configuración), no un código nuevo.
3. **Hallazgo para Administración** (fuera de F-009): el maestro de `MA9999` lleva `MA1501` («cerámico»); corregirlo
   es un cambio de datos en Sigrid que deciden ellos. El mapeo no deja de hacer falta.
4. **Nota de M19**: su TOP 10 lista albaranes con genéricos (estado 10) sin fila de alta en `log`, mientras el conteo
   por usuario da «0 de 48.788 sin alta» (solo cuenta líneas con fila de alta). No cambia la conclusión (las altas de
   la API no tocan genéricos), pero el «0» no prueba que no haya altas sin `log`.
5. Heredada, sin cambios: `tex` vacío en las sin vincular (el escritorio lo rellena en el 11 %, texto propio): confirmar.
6. **F-053** no cambia: no mandaba `naturaleza` y `naturaleza_no_valida` ya iba a `error`.

## v7: resultados de T0b-bis (2026-10-05) y decisiones del humano

Spec-author. Solo spec; sin llamar a la API, Azure ni el SQL Server. Fuente: el fichero de resultados
del humano (`%TEMP%`, 2026-10-05 16:32; **no** se versiona: lleva datos de negocio). Aquí solo cifras
agregadas y conclusiones; ni proveedores, ni filas, ni importes. Definiciones de M14b, M16b y M17b:
`impl_F-009_T0a_bis.md`; las anteriores, §T0 v5.

### Resultados de T0b-bis y decisión

| M | Resultado agregado | Decisión en la v7 |
|---|---|---|
| M9 | Albaranes de septiembre de 2026 (2.724; 11.121 líneas): con `mov` el 74,7 %. Por `pro.tipmov`: 1 ⇒ 8.302 de 8.319 (99,8 %); 0 ⇒ 0 de 2.782; −1 ⇒ 0 de 20. `pro.tipinv` no lo explica (0 ⇒ 22,7 %). Genéricos de la empresa 1, julio-septiembre: MA9999 5.871 de 5.871 y QA9999 2.031 de 2.031 (100 %), SB9999 99,9 %, SM9999 98,9 %; los cuatro con `tipmov` 1 | **Cerrada**: `mov` si y solo si `pro.tipmov` = 1, para cualquier producto, vinculado o no (R19; L7b lee el de los `ctrpro`). **H20 cerrado** (decisión del humano: se replica el escritorio); la puerta dura se retira como cumplida (R35, T22) |
| M11 | Genéricos en las empresas 1, 31 y 34, con `comide`/`ivacomide` 0; en 31 y 34, sin líneas en la ventana. Empresa 1, julio-septiembre: MA9999, 13,3 % de proveedores con más de un IVA; el IVA de la línea previa **del mismo proveedor** acierta el 97,7 % frente al 95,0 % de la previa de cualquiera. QA9999: 6,0 %; 99,5 % frente a 95,9 %. La combinación más frecuente (cuenta, IVA, naturaleza, unidad) cubre solo el 6,6 % / 9,0 %. `ivacuo` ≠ `round(tot·iva, 2)` en 13 de 40.601 | **Cerrada**: L8b justificada (R13, H15); `ivacuo` con `dbo.iva` (R17) |
| M14 (`prepma`) | `dcapro.prepma` = `mov.prepma` de su propio `mov` en 8.328 de 8.328 (100 %); = `mov.almpma` (el PMP resultante) solo en 215 (2,6 %) | **Corrige R21** de la v6 (decía «PMP resultante»): `dcapro.prepma` = `mov.prepma`. Qué valor es `mov.prepma` y cuál lleva la línea sin `mov`: **P1** [M14c] |
| M14 (API) | Albarán de la API frente a tres del escritorio del mismo proveedor: ninguna columna de `con`, `dca` ni `dcapro` con un valor que el escritorio no use. Sin vincular de 2026 (94.750): las proporciones de T0b se repiten | Sin cambios (§Reseteo cerrada en la v6) |
| M14b | 2.744 albaranes desde 2026-09; 2.725 con albarán anterior del mismo proveedor y empresa: `pagide` 94,5 % frente al 81,5 % del maestro del proveedor; `efeide` 97,8 % frente a 87,1 % | **Cerrada**: la plantilla L5 se mantiene (R21) |
| M16 | Repite T0b: vinculadas, `caaide` del `ctrpro` 100 % (misma partida) y 99,9 % (distinta); sin vincular, de la partida 2,7 %; orden de almacén de R15 confirmado | Sin cambios |
| M16b | 189.373 sin vincular desde 2025. Ningún campo da el código de la `caa` por sí solo (`caagascod`, `caaexicod`, `cuafaccod`, cuenta: 0 %; partida 6,4 % en el resto, 0 % en los genéricos). Propiedades: `caa.cenide` = `dcapro.cenide` ~100 %; el código de la `caa` contiene el de la obra y el del centro ~100 %; cuenta 6XX ~100 %; cuenta = `cuacomcod` de la naturaleza **del producto** 100 % en MA9999 (QA9999 99,9 %; resto 96,7 % / 70,4 %). Naturaleza de la línea = la del producto: MA9999 48,7 % (con partida) y 52,0 % (sin); QA9999, SB9999 y SM9999 100 %. Muestra de las 20 combinaciones más frecuentes (54.572 líneas): todas siguen `<obra>.<lo que sigue al «.» del caagascod de la naturaleza de la línea>` (`MOD.CDSB37` en la obra `0678` ⇒ `0678.CDSB37`); en las dos en que la naturaleza de la línea difiere de la del producto manda la de la línea. `dcaproana`: 0 de 189.373 | **Regla de la naturaleza, condicional a M16c** (≥ 95 %; si no, PARADA): design §Analítica, R13b, R15, L15a-c. Campo opcional **`naturaleza`** (decisión del humano), `naturaleza_no_valida`; `analitica_no_resuelta` si no existe la `caa` compuesta. Sin `dcaproana` (R25) |
| M17 / M17b | `log` sobre albaranes (último millón de `ide`): `ope` 2 en 820 filas. Tras la `ope` 2: el albarán no existe en 513 (62,6 %); existe con el mismo `cod` y un alta posterior en 305 (37,2 %); sin alta posterior, 2 (0,2 %). Ningún albarán con `fecbaj`; `est` 1, 2, 3, 10 (y 0 en 6) | **Cerrada**: anular **borra** el `con` y el escritorio **reutiliza** el `cod` (coherente con el índice único `(emp, tip, cod)`). H9 cerrado: R30 sin cambios, R30b retirada; F-053 puede repetir el alta con la misma referencia tras anular. T23 comprueba que el `con` ya no existe |

### Decisiones del humano aplicadas (2026-10-05)

- **H20**: se replica el escritorio, `mov` si y solo si `pro.tipmov` = 1, para cualquier producto.
- **Naturaleza**: campo opcional `naturaleza` (`auxpronat.cod`, 1-16) en la sin vincular; sigrid-api lo
  valida (existe, sin baja, de la empresa de la obra; si no, `naturaleza_no_valida`) y, si falta, usa la del
  producto. `natide`, `caaide` y `cueide` salen de la naturaleza resultante. Qué naturaleza manda albaranes
  está consultado a negocio (Administración y Control de Costes): pendiente de F-053, no bloquea F-009.
- **Vinculadas**: sin cambio, `caaide` del `ctrpro`.
- Del contrato v6.1 (decisión del humano del mismo día) se absorbe la lista blanca con `XA9999` (R10, T19).
  Su regla de analítica (la de la última sin vincular del par obra-producto) queda superada por M16b.

### Qué cambió en la spec

| Cambio | Dónde |
|---|---|
| `mov` según `pro.tipmov`; L7b; H20 cerrado sin puerta; `mov` con `tipmov` 0 como diferencia declarada del clásico | R19, R35; design §Filas, L7, §Condicionales, §Equivalencia; tasks T6, T22; contrato §2.3, §4.2, H20 |
| Naturaleza, analítica y cuenta de las sin vincular; campo `naturaleza`; L15a-c; `naturaleza_no_valida` y `analitica_no_resuelta` | R6, R13, R13b, R15, R34 (fase RED); design §Modelo, §Filas, §Analítica, §Sentencias, §Códigos, §Flujo; tasks T3, T4, T6, T7, T21; contrato §2.2-§2.4, §3.3, §4, H10, §6.f |
| `dcapro.prepma` = `mov.prepma` (corrige la v6); su valor [M14c] | R21; design §Filas, §Condicionales |
| L8b (M11) y L5 (M14b) cerradas | R13, R17, R21; design L5, L8b, L9; contrato H15 |
| Anular borra: R30b retirada, L11 sin filtro | R30; design L11; tasks T8, T23; contrato H9, §0 |
| Sin `dcaproana` | R25, fuera de alcance |
| Lista blanca con `XA9999` | R10; tasks T19; contrato §8 |
| T0b-bis hecha; **T0b-ter** `--solo M16` (M16c); T0c vuelca en la v8 y retira el script | tasks; R35; contrato H28 |

Topes tras la v7 (`python -m harness.tamano --feature F-009`): `requirements.md` 150/150 y `design.md`
250/250. Para caber se reescribieron sin perder reglas: R2, R6, R7, R9, R10, R36 y fuera de alcance;
en design, §Caracterización, §Importes, §Devoluciones, §Códigos, §Equivalencia, el paso 3 del flujo y
§Riesgos (los descartes de analítica viven ahora en §Analítica).

### Coherencia de `prepma` (P1)

T0b-bis prueba que `dcapro.prepma` y `mov.prepma` son **el mismo valor**, no qué valor es. La regla A
(M5) solo comprobó `almcan` y `almpma` del `mov`, nunca `mov.prepma`, así que no la contradice. El
clásico escribe `mov.prepma` = PMP resultante (= `almpma`), lo que el escritorio hace solo en el 2,6 %:
el clásico tampoco lo replica (no se toca, R2). La primera pasada de M14 decía que el `prepma` del
escritorio «coincide con el PMP vigente del almacén», sin compararlo con el `mov`. Dos hipótesis:
(a) el PMP del almacén **antes** del movimiento (el `almpma` del `mov` anterior del mismo producto y
almacén por `fechor`), que sigue L12/E7 sin escribir nada más; (b) el precio medio global del producto
(`pro.prepma`, «Precio Medio Almacén» en el diccionario; `mov.prepma` se titula «Precio Medio Compra»),
que podría exigir que el escritorio actualice `pro.prepma`/`pro.canact` en cada alta: una escritura que
F-009 no hace (R25, fuera de alcance «escribir `pro`») ⇒ PARADA. No hay evidencia para elegir sin medir.

### Preguntas abiertas (numeradas)

1. **P1 · `prepma`**: ¿se añade **M14c** a T0b-ter? Propuesta: `mov.prepma` frente a (a) y (b) en los
   `mov` de albarán desde 2026-09, y `dcapro.prepma` de las líneas sin `mov` frente a 0 y a `pro.prepma`.
   Sin M14c, la alternativa es fijar (a) sin medir (no recomendado: es otro valor «plausible»). Para la
   línea sin `mov`, la propuesta provisional es 0 (no hay movimiento de almacén), también a M14c.
2. **P2 · «naturaleza de la empresa»**: se interpreta como `auxpronat.numemp` = empresa de la obra, pero
   no está medido y hay indicio en contra: la combinación más frecuente en las líneas de MA9999 de la
   empresa 1 usa la naturaleza del maestro de MA9999 de las empresas 31 y 34, no la del de la 1. Propuesta:
   que M16c (o una lectura en T21) cuente el `numemp` de las naturalezas usadas en la empresa 1; si sale 0
   u otra empresa, la validación pasa a «existe y sin baja» (o `numemp` en {0, empresa}).
3. **P3 · `cua` por empresa**: L15c busca la cuenta por `cod` y `con.emp`; no medido. Propuesta: que
   M16c compruebe que el `cuacomcod` de cada naturaleza da una sola `cua` en la empresa 1.
4. **P4 · cuenta con la naturaleza cambiada**: el humano decide que `cueide` sale de la naturaleza
   resultante, pero en la muestra de M16b, cuando el usuario cambia la naturaleza, la cuenta financiera
   coincide con la de la naturaleza **del producto** (la de `MOD.CDMA15`, no la de `MOD.CDSB37`). M16c ya
   mide `cueide_linea` frente a `cueide_producto`. Si gana la del producto, PARADA: o se replica el
   escritorio (cuenta del producto, analítica de la línea) o se mantiene la decisión.
5. **P5 · `XA9999`**: no lo midieron M9, M11 ni M16b (no estaba en el script). Con H20 cerrado no
   bloquea (su `tipmov` decide), pero conviene añadirlo a los genéricos de T0b-ter o verlo en T21.
6. **P6 · F-053** (no bloquea F-009): qué `naturaleza` manda albaranes (consulta a negocio) y qué estado da
   a `naturaleza_no_valida` (propuesta: `no_admitido`).
7. Heredadas de la v6, sin cambios: `cod2` (consulta a negocio; vacío por defecto) y `tex` vacío en las
   sin vincular (confirmar).

### Notas para el líder y el implementer

- **T0b-ter** = `--solo M16` con M16c (en curso). Si el humano aprueba P1, añadir M14c y lanzar
  `--solo M14 M16`. P2, P3 y P5 caben en la misma pasada como lecturas informativas.
- La spec no cambia de forma con M16c si sale ≥ 95 % con la naturaleza de la línea y la obra; si gana el
  centro o la naturaleza del producto, es un cambio de una línea en design §Analítica y L15b (PARADA corta).
- L15b busca la `caa` por (`cenide` de la línea, `cod`), como el control de `caa` repetidas de M16c.
- T0c: volcado de T0b-ter en la v8 y retirada del script y su test (N3) antes de T1.

## v6: resultados de T0 (repetición del 2026-10-05) y decisiones del humano

Spec-author. Solo spec; sin llamar a la API, Azure ni el SQL Server. Fuente: el fichero de
resultados del humano (`%TEMP%`, 2026-10-05 13:24; **no** se versiona: lleva datos de negocio) y el
maestro de genéricos de la primera pasada (`%TEMP%`, 2026-10-02). Aquí solo cifras agregadas y
conclusiones. Definiciones de cada medición y su «debe salir / decide»: §T0 v5 (abajo).

### Resultados de T0 (repetición del 2026-10-05) y v6

| M | Resultado agregado | Decisión en la v6 |
|---|---|---|
| M3 | Partidas usadas desde 2025: 100 % `tip 1`, `tipdes 0` (`tipvis` 0 el 99,6 %, 1 el 0,4 %). 5.207 pares (obra, código) repetidos; **4.312 entre imputables** (11.402 filas) | **Cerrada**: R14b activa, `paride` opcional con `partida` (`paride_no_valido`). F-049 debe conservar el `ide` de cada partida (contrato H17) |
| M7 | 0 de 272.235 líneas con partida desde 2025 tienen fila en `dcapropar`; `parcandes` ≠ 0 en 0 | **Cerrada**: no se escribe `dcapropar` (R25, fuera de alcance) |
| M9 | `ReadTimeout` en `sql/read` | **Abierta** → T0b-bis. Debe cubrir MA9999 **y QA9999** (puerta H20 para los dos) |
| M11 | `ReadTimeout` en `sql/read` | **Abierta** → T0b-bis (IVA por proveedor de los productos de la lista) |
| M13 | 4.027 filas de alta de albarán en `log` desde 2026-09: `est` 1 y `ori` 0 en el 100 %. 1.368 de 1.371 albaranes AC desde 2026-09-15 (99,8 %) con fila de alta | **Cerrada**: `con.est` 1 `PDT` y fila de alta con `est` 1, `ori` 0 (R22, design §Filas) |
| M14 (cabecera) | Forma de pago y efecto de 2.608 albaranes desde 2026-09: los del maestro del proveedor aciertan el 82,9 % (`pagide`) y el 88,8 % (`efeide`). La comparación con el albarán de la API falló por interbloqueo (1205) en la lectura; ya estaba decidida en la primera pasada | **Abierta como M14b**: comparar con la regla actual (último albarán del mismo proveedor, L5); si acierta menos, `pagide`/`efeide` del maestro |
| M14 (sin vincular) | 94.369 líneas sin vincular de 2026. Vacías (≤ 0,1 %): `parcandes`, `anades`, `serdes`, `fecimp`, `item`, `taride`, `fec`, `pla`, `texcom`, `pac`, `refent`, `desesp`, `edilin`, `garfec`, `mesrevpre`, `ejerevpre`. Con valor: `cod2` 20,8 %, `dncide`/`dncproide` 5,8 %, `med`/`canmed` 1,8 %, `anexo` 0,3 %, `tex` 11,0 %, `prepma` 77,0 %. `dcapro.fec` = fecha del albarán en 0 %. Arrastre (3 líneas seguidas del MA9999 de la empresa 1 frente a su plantilla): ninguna columna se copia; las que tienen valor difieren de la plantilla | **Cerrada**: ninguna se arrastra; las que el escritorio rellena cambian línea a línea con otra fuente ⇒ se vacían. §Reseteo ampliada (`dncide`, `dncproide`, `desesp`, `edilin`, `garfec`, `mesrevpre`, `ejerevpre`), todas a 0/`''`; `fec` 0; `prepma` según R21. `cod2`: vacío por defecto, pendiente de una consulta del humano a negocio (no bloquea) |
| M16 (analítica) | Vinculadas con la misma partida que el `ctrpro` (92.771): `caaide` del `ctrpro` 100 %, de la partida 0,9 %. Con partida distinta (3.646): del `ctrpro` 99,9 %, de la partida 0,3 %. Sin vincular con partida (175.820): de la partida 2,7 %. Sin partida (15.022): `alm.caaproide` coincide en 7 (0,0 %) y ningún almacén tiene analítica | **Cerrada para las vinculadas**: `caaide` del `ctrpro` siempre. **Hipótesis de la v5 refutada** (partida / `alm.caaproide`): se retira. Sin vincular: **M16b**, sin regla provisional (decisión del humano) |
| M16 (almacén) | Sin vincular con contrato (129.874): almacén del contrato 100,0 %, de la ficha 100,0 %. Sin contrato (59.118): de la ficha 98,3 %. Ficha de las 89 obras con albaranes desde 2025: con `almide` 100 %, de su obra 98,9 %, con `cenide` 100 % | **Cerrada**: orden de R15 (contrato → ficha de obra → único `alm`) confirmado |
| M17 | `log.ope` sobre albaranes (último millón de `ide`, 2025-08-20 a 2026-10-05): 1 (46.204), 2 (822), 3 (11.443), 5 (90.658), 30 (2.287); `log.emp` 1 en el 99,96 %. El albarán sigue existiendo (mismo `emp`, `tip`, `cod`) tras `ope` 2 en el 37,5 %, tras 3 en el 99,0 %, tras 5 en el 99,5 % y tras 30 en el 95,8 %. Ningún albarán con `fecbaj` > 0; `est` desde 2025 solo 10, 3, 1, 2 (y 0 en 6) | **No concluyente**: la `ope` 2 parece la baja, pero el 37,5 % que «existe» podría ser un `cod` reutilizado. **M17b** lo decide; si no, T23. R30b sigue condicional |
| M18 | `refent` informado en 0 de 287.259 líneas desde 2025 (188.992 sin vincular, 98.267 vinculadas); 0 de 184.455 líneas de factura con `refent` copiado del albarán | **Cerrada**: `referencia_linea` (1-24) en `dcapro.refent`, devuelta en `idempotente` (R30c; N9 aprobada) |

Maestro de genéricos (primera pasada): `QA9999` («alquiler de maquinaria») existe en las empresas 1,
31 y 34 con `natide` propio; `pro.gaside` = 0 en los cuatro genéricos (MA, QA, SB, SM).

### Decisiones del humano (2026-10-05) aplicadas

- **Toda línea es vinculada (`ctrpro`) o lleva un producto de la lista blanca**; nada más. «De
  momento, en general siempre materiales o maquinaria» ⇒ despliegue de
  `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO` = `["MA9999", "QA9999"]` (R10, T19). Albaranes elige el
  producto por línea (contrato §2.2 y §2.4, para F-053). La puerta dura H20 cubre los dos (R35, T22).
- **La cuenta analítica sale del vínculo**: vinculada ⇒ la del `ctrpro` (M16); sin vincular ⇒ la del
  producto, **condicional a M16b** y sin regla provisional. Hipótesis en estudio: la naturaleza del
  producto (`auxpronat.caagascod` con partida, `caaexicod` sin partida), quizá compuesta con la obra.
  Retirada la hipótesis de la v5 (design §Analítica; R15; contrato H10).

### Qué cambió en la spec

| Cambio | Dónde |
|---|---|
| `paride` opcional con `partida` (sin `partida`, 400 sin código); `partida_ambigua` solo sin `paride`; L6 sin `caaide` y el `paride` se busca entre las partidas leídas por código | R6, R14, R14b; design §Modelo, L6, §Códigos; contrato §2.2, §3.3, H17 |
| `referencia_linea` 1-24 en `dcapro.refent` (todas las líneas), leída en L11 y devuelta en `idempotente`; diferencia declarada en R33 | R30c (antes la mitad de R30b), R21; design §Modelo, §Respuesta, §Filas, L11, §Equivalencia; contrato §2.2, §3.1, 6.d, H18 |
| `con.est` 1 y `log` con `est` 1, `ori` 0; sin `dcapropar` | R22, R25, fuera de alcance; design §Filas |
| §Reseteo ampliada y cerrada; `prepma` (M14) | R13, R21; design §Reseteo; contrato H11 |
| Analítica: vinculada del `ctrpro`; sin vincular [M16b]; L10 sin `caaproide`; L15 la fija M16b | R12, R15; design §Analítica, L10, §Condicionales, §Riesgos; contrato §2.3, H10 |
| Lista blanca `["MA9999", "QA9999"]`, producto por línea; H20 para los dos | R10, R13, R35; tasks T19, T21, T22; contrato §1.3, §2.2-§2.4, §4.3, H20 |
| Forma de pago y efecto de la cabecera [M14b] | R21; design §Filas, §Condicionales |
| T0b hecha; **T0b-bis** `--solo M9 M11 M14 M16 M17` tras ampliar el script con M14b, M16b y M17b; T0c sin cambios | tasks; R35; contrato H28 |

Topes tras la v6 (`python -m harness.tamano --feature F-009`): `requirements.md` 150/150 y
`design.md` 250/250. Para caber: §Condicionales lista las cerradas en una frase y tabula solo las
abiertas; las cifras de M14 y M16 viven en esta sección.

### Notas para el líder y el implementer

- **T0b-bis** necesita, además de M14b, M16b y M17b, que **M9 y M11 midan también QA9999** (ahora
  está en la lista blanca): la puerta H20 y la plantilla L8b valen para los dos productos. Si el
  script ya recorre `PRODUCTOS_GENERICOS`, basta comprobar que la conclusión los separa.
- M16b debe medir el `caaide` de las sin vincular frente a `auxpronat.caagascod`/`caaexicod` de su
  naturaleza (con y sin partida) y, si no llega a ≥ 95 %, frente a la combinación con la obra.
- M9 y M11 se cortaron por `ReadTimeout`: conviene acotar su ventana para no repetir el corte.
- T0c no cambia: tras T0b-bis, el volcado será la v7 (o una PARADA si M16b no da regla).

**Decisiones abiertas para el humano:** (1) `cod2`: consulta a negocio pendiente (no bloquea; vacío
por defecto). (2) `tex`: se mantiene vacío en las sin vincular, como en la v5 (el escritorio lo
rellena en el 11 %, texto propio de la línea, nunca de la plantilla); confirmar. (3) Las reglas que
fijen M9, M11, M14b, M16b y M17b (o T23) tras T0b-bis.

## v5.1 (2026-10-05): respuestas del humano a la v5

Spec-author. Solo spec; sin llamar a la API, Azure ni el SQL Server. Topes tras la v5.1:
`requirements.md` 150/150 y `design.md` 249/250 (`python -m harness.tamano --feature F-009`).

### Respuestas a N4-N12

| N | Respuesta | Efecto en F-009 |
|---|---|---|
| N4 | Aprobada: F-053 manda `cod_contrato` siempre que la valoración tenga contrato | Ninguno (F-053 R12); contrato §5 H31 |
| N5 | Aprobada: `SIGRID_ALBARAN_EMPRESAS_OBRA` defecto `[]`, despliegue `[1]` | Ninguno |
| N6 | Aprobada: no se rechazan obras de baja | design §Riesgos; contrato §5 H2 |
| N7 | Aprobada: `precio_negativo` (fallo de línea) sustituye al `ge=0` de Pydantic | Ninguno |
| N8 | Aprobada: `iva_de_otro_proveedor`, informativo en F-053 | contrato §3.2 |
| N9 | Aprobada: `referencia_linea` en `dcapro.refent` si M18 lo deja libre | Ninguno (R30b) |
| N10 | **Sustituida** por el cambio 2 | — |
| N11 | Aprobada: F-009 solo normaliza mayúsculas y espacios del CIF | Ninguno |
| N12 | Aprobada: mapeo de §3.3 del contrato en F-053, ya sin `fecha_no_valida` | contrato §3.3 |

### Cambio 1: la línea sin partida es el «almacén» de Ruesma

Textual: «almacén en Ruesma es simplemente dejar la línea del albarán sin partida. Si miras en Sigrid
verás que hay bastantes. No usamos un concepto almacén como tal, sino albarán sin partida en una o
varias líneas, que luego se puede pasar a partida cuando se desacopia.»

- **Sin campo `almacen`** en la línea; `partida` opcional: ausente o `null` ⇒ línea sin partida,
  `dcapro.paride` 0, **nunca** heredada del `ctrpro` ni de otra línea. R6 ya no exige «uno de
  `partida`/`almacen:true`» (R6, R14; design §Modelo). Con `extra="forbid"`, mandar `almacen` da 400
  sin código: F-053 debe dejar de mandarlo (contrato §0, §2.2, §3.4 y H5).
- `almide`/`cenide` (almacén físico: stock y `mov`) siguen en **toda** línea según R15, como el
  escritorio (M8). «Almacén» queda solo para eso; spec y contrato hablan de «sin partida».
- Aviso renombrado: `almacen_en_linea_con_partida` → **`sin_partida_en_linea_con_partida`**
  (vinculada sin partida cuyo `ctrpro.paride` ≠ 0), informativo (R16, design §Códigos, H12).
- Respuesta por línea sin `almacen`: basta `paride` 0 y `partida` nula (design §Respuesta, contrato
  §3.1; la comparación de la previa en sv9 pasa a ser por `partida`, incluida la nula).
- Pasar la línea a partida al desacopiar se hace en Sigrid: «fuera de alcance» y contrato §2.3/§4.3.
- M16 no cambia: `M16_caa_almacen` sigue midiendo el `caaide` de las líneas con `paride` 0 (el
  nombre de la consulta no se toca; el script lo amplía otro agente en paralelo).
- Contrato: §0, §1.2, §2.2 (fila `almacen` retirada), §2.3 (filas renombradas y una nueva para
  «pasar a partida»), §2.4, §3.1, §3.2, §3.3, §3.4, §4.1, §4.3, §5 (H5, H12) y ejemplos 6.a-6.e.
  Los textos históricos de §5 que citan `almacen` quedan, con una nota al principio de §5.

### Cambio 2: la API no rechaza fechas futuras

Textual: «la conexión no debe rechazar fechas futuras per se; eso se hará desde la app.»

- Fuera `fecha_no_valida` de R11, design (§Modelo, §Flujo, §Códigos), tasks (T3, T7) y contrato
  (§2.1, §3.3, §4.1, §4.3; H19 pasa entero a albaranes). Queda solo la validación de formato y
  rango que ya había (`fecha_albaran` 19000101-29991231, Pydantic); R6 lo dice y T3 lo prueba.
- Fase RED: no había una propia de la fecha. R34 conserva la de R11 por la resolución de la obra en
  las empresas admitidas (H2), que sigue.

### Otros

- `harness/features.json` (description y acceptance; estado `spec_ready`) y `BACKLOG.md` regenerado.
- §Manuales: el cuerpo de T21 deja `almacen` y gana `usu` (obligatorio desde la v3; sin él, 400).
- **No tocados**: `scripts/medir_f009_t0.py` y `tests/test_f009_t0_script.py` (otro agente),
  `progress/para_albaranes_F-009.md` (sin trackear; si cita `almacen: true` o `fecha_no_valida`,
  lo debe alinear quien lo lleve) y el fichero sin trackear de la raíz.
- `bash harness/init.sh` en este árbol: **rojo solo por el trabajo a medias del otro agente** (T0a):
  `test_f009_t0_hay_una_medicion_por_cada_m_de_la_spec` ya espera M16-M18 y el script aún no las
  tiene, y la puerta de cobertura cuenta esas líneas. Con solo los ficheros de la v5.1 sobre `ca4c2b5`,
  en un worktree temporal (ya retirado): 1897 passed, 1 skipped; todo en verde salvo «Falta `.env`»
  (el worktree no lo tiene y no se copió). Ningún fichero de la v5.1 es código.

**Decisiones abiertas para el humano:** ninguna nueva; validar la v5.1. Siguen T0b (repetición única
de T0) y T0c (volcado y retirada del script) como precondición de `in_progress`.

## v5 (2026-10-05): huecos del contrato con albaranes y decisiones del humano

> **v6: en parte sustituida.** Las filas H10 (`caaide` por hipótesis de M16), H11 (lista de
> reseteo), H17 y H18 (condicionales a M3 y M18), H20 (solo MA9999) y H28 (una sola repetición) se
> leen con §v6: la hipótesis de analítica queda refutada, R14b y R30c activas, lista blanca de dos
> productos y T0b-bis. Se conserva como evidencia.

Fuente: `specs/F-009-alta-albaran-compra/contrato_albaranes.md` §5 (H1-H33, escrito el mismo día
por el agente de albaranes contra la v4) y las decisiones del humano del 2026-10-05 sobre H4, H8,
H9, H17, H20, H28 y H31. Estado de cada hueco: tabla al principio de §5 de ese documento. Topes:
`requirements.md` 150/150 y `design.md` 249/250; para caber, el detalle campo a campo y los
ejemplos se enlazan a `contrato_albaranes.md` y el razonamiento de N1 y de la regla A a este informe.

### Qué cambió en la spec

| Hueco | Cambio | Dónde |
|---|---|---|
| H2 | Obra solo en las empresas de `SIGRID_ALBARAN_EMPRESAS_OBRA` (quinta App Setting, defecto `[]`, despliegue `[1]`); código nuevo `obra_de_empresa_no_permitida`. Con `[1]`, `obra_ambigua` ya no puede darse (índice único `(emp, tip, cod)`, M2) | R10, R11, design L1 |
| H3 | Plantilla de cabecera del mismo proveedor **en la empresa de la obra** (`AND c.emp = ?`) y `con.emp` = la de la obra | R11, design L5 |
| H4 | Decidido: se conserva «imputable» y **no** se exige hoja | R14 |
| H8 | Segunda barrera: `precio` < 0 ⇒ fallo de línea `precio_negativo`. **Ya existía algo equivalente**: `precio` con `ge=0` en Pydantic (400 sin código, toda la petición). Se sustituye por el fallo de línea con código para que F-053 lo pueda mapear; el efecto (rechazo) es el mismo | R17, design §Modelo y §Riesgos |
| H9 | Regla condicional a M17 (R30b) | R30b, design §Condicionales |
| H10 | Almacén y centro para **toda** sin vincular (con o sin partida); `caaide` por hipótesis condicionada a M16 | R15, design §Analítica |
| H11 | Lista de reseteo cerrada para las sin vincular, confirmada con M14 ampliada | R13, design §Reseteo |
| H12 | Aviso `almacen_en_linea_con_partida` | R16 |
| H13 | `obr.almide`/`obr.cenide` antes que el único `alm` de la obra (orden: `ctrpro` o contrato → ficha de obra → único `alm`) | R15, design L10 |
| H14 | Tolerancia 0,0001 (la de M4); si casa, `pre`, `tar` y `dto` del `ctrpro` | R17 |
| H15 | Plantilla de la sin vincular = última `dcapro` del producto **del mismo proveedor** (L8b); si no hay, la del producto con aviso `iva_de_otro_proveedor` | R13, design L8b |
| H16 | `COLUMNAS_BANCARIAS` (15 columnas de `dca` según el diccionario) fuera de `cabecera`, `filas.dca` y trazas; se escriben igual | R7, R32, design §Respuesta |
| H17 | `paride` opcional solo si M3 da repetidos entre imputables (R14b, código `paride_no_valido`) | R14b |
| H18 | `idempotente`: `committed` `false`, `dry_run` = `not commit`, líneas por `pos` con `indice` desde 0; `referencia_linea` en `dcapro.refent` condicionada a M18 (y entonces ≤24) | R30, R30b |
| H19 | `fecha_no_valida` si `fecha_albaran` > hoy (Madrid), también en dry-run | R11 |
| H20 | Puerta dura: sin M9 cerrada no hay modo real; si MA9999 mueve stock, PARADA | R35, tasks T22 |
| H21 | `cif_proveedor` a mayúsculas sin espacios | R5 |
| H26, H27 | `indice` desde 0; avisos `{codigo, mensaje}` y `warnings` = sus mensajes | R7 |
| H28 | Una sola repetición de T0 con el script ampliado | R35, tasks T0a-T0c |
| H31 | **Comprobado: F-009 ya admite** `cod_contrato` sin ninguna vinculada (ninguna regla lo prohíbe: se resuelve el contrato, `dca.ctride` queda enlazado y plantilla y almacén salen del contrato). Lo único que faltaba: sin vinculadas no hay `UPDATE` de `ctrpro` ni de `ctr` (E9-E11) | R6, R20, R25 |
| H32 | Docstring de `sigrid_albaran` (T13) y `sigrid_api.md` §4, §7.5, §7.6, §8.6 (T18) | R36 |
| H33 | `Decimal` + `ROUND_HALF_UP` en `tot` e `ivacuo`; diferencia declarada en R33 (el clásico usa `round`) | R17, R33 |

Otros: `cantidad` y `precio` finitos (`NaN`/`inf` fuera); R34 añade fase RED en R11 y R17. Ningún
hueco contradice el código ni las mediciones de la primera pasada. Matiz en H13: la propuesta decía
«`obr.almide` primero»; se mantiene antes el almacén del `ctrpro`/contrato (M8: el del contrato es
de su obra en el 99,4 %) y la ficha de obra pasa a ser el segundo recurso, antes que `alm`.

### T0 v5: mediciones nuevas y ampliadas (solo lectura, `sql/read`)

> **v6**: resultados y decisiones en §v6. Las definiciones siguen valiendo; el «debe salir / decide»
> de M16 sobre la analítica (partida / `alm.caaproide`) queda **sustituido** (M16 lo refuta; M16b) y
> el de M18 y M3, **cumplido** (R30c, R14b). «Una sola repetición» queda sustituida por T0b + T0b-bis.

Una sola repetición (H28): `& .\.venv\Scripts\python.exe -m scripts.medir_f009_t0 --solo M3 M7 M9
M11 M13 M14 M16 M17 M18`, después de que el implementer amplíe el script (tasks T0a). Las sentencias
siguen la regla del error 130: nada de agregados sobre subconsultas o `APPLY` escalares; recuentos
en tablas derivadas. M3, M7, M9 y M13 quedan como están en el script.

- **M16 analítica, almacén y centro (H10, H13)** → decide design §Analítica y el orden de R15.
  - `M16_caa_con_partida`: `SELECT CASE WHEN ISNULL(d.docoritip, 0) = 44 THEN 'vinculada' ELSE 'sin_vincular' END AS tipo, CASE WHEN ISNULL(d.docoritip, 0) = 44 AND ISNULL(d.paride, 0) <> ISNULL(t.paride, 0) THEN 1 ELSE 0 END AS partida_distinta, COUNT(*) AS n, SUM(CASE WHEN ISNULL(d.caaide, 0) = ISNULL(p.caaide, 0) THEN 1 ELSE 0 END) AS caa_de_la_partida, SUM(CASE WHEN ISNULL(p.caaide, 0) = 0 THEN 1 ELSE 0 END) AS partida_sin_caa, SUM(CASE WHEN t.ide IS NOT NULL AND ISNULL(d.caaide, 0) = ISNULL(t.caaide, 0) THEN 1 ELSE 0 END) AS caa_del_ctrpro FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide JOIN dbo.obrparpar p ON p.ide = d.paride LEFT JOIN dbo.ctrpro t ON t.ide = d.linoriide AND d.docoritip = 44 WHERE c.tip = 14 AND c.fec >= 20250101 AND d.paride > 0 GROUP BY` (las dos expresiones `CASE`).
  - `M16_caa_almacen`: `SELECT CASE WHEN ISNULL(d.docoritip, 0) = 44 THEN 'vinculada' ELSE 'sin_vincular' END AS tipo, COUNT(*) AS n, SUM(CASE WHEN ISNULL(d.caaide, 0) = ISNULL(a.caaproide, 0) THEN 1 ELSE 0 END) AS caa_pro_del_alm, SUM(CASE WHEN ISNULL(d.caaide, 0) = ISNULL(a.caaseride, 0) THEN 1 ELSE 0 END) AS caa_ser_del_alm, SUM(CASE WHEN ISNULL(a.caaproide, 0) = 0 THEN 1 ELSE 0 END) AS alm_sin_caa FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.alm a ON a.ide = d.almide WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.paride, 0) = 0 GROUP BY` (el `CASE`).
  - `M16_almacen_sin_vincular`: `SELECT CASE WHEN ISNULL(d.paride, 0) > 0 THEN 'con_partida' ELSE 'almacen' END AS tipo, CASE WHEN ISNULL(a.ctride, 0) > 0 THEN 'con_contrato' ELSE 'sin_contrato' END AS cabecera, COUNT(*) AS n, SUM(CASE WHEN d.almide = t.almide THEN 1 ELSE 0 END) AS alm_del_contrato, SUM(CASE WHEN d.almide = o.almide THEN 1 ELSE 0 END) AS alm_de_la_ficha, SUM(CASE WHEN d.cenide = t.cenide THEN 1 ELSE 0 END) AS cen_del_contrato, SUM(CASE WHEN d.cenide = o.cenide THEN 1 ELSE 0 END) AS cen_de_la_ficha FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide JOIN dbo.dca a ON a.ide = d.docide LEFT JOIN dbo.obr o ON o.ide = d.obride LEFT JOIN dbo.ctr t ON t.ide = a.ctride WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.docoritip, 0) <> 44 GROUP BY` (los dos `CASE`).
  - `M16_ficha_obra`: `SELECT COUNT(*) AS obras, SUM(CASE WHEN ISNULL(o.almide, 0) > 0 THEN 1 ELSE 0 END) AS con_almide, SUM(CASE WHEN a.obride = o.ide THEN 1 ELSE 0 END) AS almide_de_su_obra, SUM(CASE WHEN ISNULL(o.cenide, 0) > 0 THEN 1 ELSE 0 END) AS con_cenide FROM dbo.obr o LEFT JOIN dbo.alm a ON a.ide = o.almide WHERE o.ide IN (SELECT d.obride FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = 14 AND c.fec >= 20250101)`.
  - **Debe salir / decide**: `caa_de_la_partida` ≥ 95 % de `n` en las sin vincular y en las vinculadas con `partida_distinta` 1, y `caa_pro_del_alm` ≥ 95 % en almacén ⇒ hipótesis de design §Analítica confirmada. `alm_del_contrato` dominante en `con_contrato` y `alm_de_la_ficha` en `sin_contrato`, con `con_almide` ≈ `obras` y `almide_de_su_obra` ≈ `con_almide` ⇒ orden de R15 confirmado. Cualquier otro reparto ⇒ PARADA y v6.
- **M17 anulación de albaranes (H9)** → decide R30b (ignorar anulados o no).
  - `M17_ope`: `SELECT ope, COUNT(*) AS n, MIN(fec) AS desde, MAX(fec) AS hasta FROM dbo.log WHERE ide > (SELECT MAX(ide) - 1000000 FROM dbo.log) AND tab = 'con' AND tip = 14 GROUP BY ope ORDER BY ope` (qué operaciones registra el escritorio sobre albaranes; el diccionario no documenta los valores de `log.ope`).
  - `M17_existe`: `SELECT l.ope, COUNT(*) AS n, SUM(CASE WHEN c.ide IS NULL THEN 0 ELSE 1 END) AS con_existe, SUM(CASE WHEN ISNULL(c.fecbaj, 0) > 0 THEN 1 ELSE 0 END) AS con_fecbaj FROM dbo.log l LEFT JOIN dbo.con c ON c.emp = l.emp AND c.tip = l.tip AND c.cod = l.cod WHERE l.ide > (SELECT MAX(ide) - 1000000 FROM dbo.log) AND l.tab = 'con' AND l.tip = 14 AND l.ope <> 1 GROUP BY l.ope ORDER BY l.ope` (si `log.emp` sale 0 o nulo, repetir el `JOIN` solo por `tip` y `cod`).
  - `M17_marcas`: `SELECT est, CASE WHEN ISNULL(fecbaj, 0) > 0 THEN 1 ELSE 0 END AS con_fecbaj, COUNT(*) AS n FROM dbo.con WHERE tip = 14 AND fec >= 20250101 GROUP BY est, CASE WHEN ISNULL(fecbaj, 0) > 0 THEN 1 ELSE 0 END ORDER BY n DESC`.
  - **Debe salir / decide**: si hay una `ope` distinta de alta y modificación cuyo `con_existe` ≈ 0 ⇒ anular **borra**: R30 sin cambios. Si `con_existe` ≈ `n` y aparece una marca (`fecbaj` > 0 o un `est` fuera de `conest`) ⇒ **marca**: L11 añade `AND <no marcado>` y F-053 usa `ALB-{id}-{n}`. Sin `ope` de baja clara ⇒ se decide con T23 (anulación del albarán de prueba, leída después).
- **M18 uso de `dcapro.refent` (H18)** → decide R30b (escribir `referencia_linea` o no).
  - `M18_refent`: `SELECT CASE WHEN ISNULL(d.docoritip, 0) = 44 THEN 'vinculada' ELSE 'sin_vincular' END AS tipo, COUNT(*) AS n, SUM(CASE WHEN ISNULL(d.refent, '') <> '' THEN 1 ELSE 0 END) AS con_refent FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 GROUP BY CASE WHEN ISNULL(d.docoritip, 0) = 44 THEN 'vinculada' ELSE 'sin_vincular' END`.
  - `M18_valores`: `SELECT TOP 20 LEFT(d.refent, 8) AS prefijo, COUNT(*) AS n FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.refent, '') <> '' GROUP BY LEFT(d.refent, 8) ORDER BY n DESC`.
  - `M18_propagacion` (¿pasa `refent` del albarán a la factura?): `SELECT COUNT(*) AS n, SUM(CASE WHEN ISNULL(f.refent, '') <> '' THEN 1 ELSE 0 END) AS con_refent, SUM(CASE WHEN ISNULL(d.refent, '') <> '' AND f.refent = d.refent THEN 1 ELSE 0 END) AS copiada FROM dbo.dcfpro f JOIN dbo.dcapro d ON d.ide = f.linoriide WHERE f.docoritip = 14 AND f.docide IN (SELECT ide FROM dbo.con WHERE fec >= 20250101)`.
  - **Debe salir / decide**: `con_refent` ≤ 0,1 % de `n` ⇒ `refent` libre: se escribe `referencia_linea` (que baja a 1-24) y se devuelve en `idempotente`. Más ⇒ no se escribe. Si `copiada` > 0, la referencia llegaría a la factura (pregunta N9).
- **M11 ampliada: IVA de MA9999 por proveedor (H15)** → confirma L8b. Por cada `ide` de MA9999 (uno por empresa):
  - `M11_iva_por_proveedor`: `SELECT COUNT(*) AS proveedores, SUM(CASE WHEN x.n_iva > 1 THEN 1 ELSE 0 END) AS con_varios_iva FROM (SELECT a.entide, COUNT(DISTINCT d.ivaide) AS n_iva FROM dbo.dcapro d JOIN dbo.dca a ON a.ide = d.docide JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ? GROUP BY a.entide) x`.
  - `M11_iva_y_isp`: `SELECT a.tipisp, d.ivaide, COUNT(DISTINCT a.entide) AS proveedores, COUNT(*) AS lineas FROM dbo.dcapro d JOIN dbo.dca a ON a.ide = d.docide JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ? GROUP BY a.tipisp, d.ivaide ORDER BY lineas DESC`.
  - `M11_acierto`: `SELECT COUNT(*) AS lineas, SUM(CASE WHEN x.iva_prev_prv IS NULL THEN 1 ELSE 0 END) AS sin_previa_del_prv, SUM(CASE WHEN x.ivaide = x.iva_prev_prv THEN 1 ELSE 0 END) AS acierta_mismo_prv, SUM(CASE WHEN x.ivaide = x.iva_prev THEN 1 ELSE 0 END) AS acierta_cualquiera FROM (SELECT d.ivaide, LAG(d.ivaide) OVER (PARTITION BY a.entide ORDER BY d.ide) AS iva_prev_prv, LAG(d.ivaide) OVER (ORDER BY d.ide) AS iva_prev FROM dbo.dcapro d JOIN dbo.dca a ON a.ide = d.docide JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ?) x` (si `SqlQueryGuard` rechaza `OVER`, se queda con las dos primeras).
  - **Debe salir / decide**: `acierta_mismo_prv` > `acierta_cualquiera` o IVA distinto con `tipisp` 1 ⇒ L8b justificada. Si aciertan igual, L8b es inocua y se queda. Sigue la comprobación de `ivacuo = round(tot·iva, 2)` de `M11_iva_usado`.
- **M14 ampliada: columnas de la `dcapro` sin vincular (H11)** → confirma o corrige design §Reseteo.
  - `M14_sv_valores`: `SELECT COUNT(*) AS n, SUM(CASE WHEN DATALENGTH(d.med) > 0 THEN 1 ELSE 0 END) AS med, SUM(CASE WHEN ISNULL(d.canmed, 0) <> 0 THEN 1 ELSE 0 END) AS canmed` y el mismo patrón para `parcandes`, `anades`, `serdes`, `fecimp`, `item`, `anexo`, `taride`, `fec`, `pla` (numéricas, `<> 0`), `tex`, `texcom` (`DATALENGTH > 0`), `cod2`, `pac`, `refent` (`<> ''`) y `SUM(CASE WHEN d.fec = c.fec THEN 1 ELSE 0 END) AS fec_igual_albaran`, `FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20260101 AND ISNULL(d.docoritip, 0) <> 44`.
  - `M14_sv_arrastre`: las 3 últimas sin vincular de MA9999 de la empresa 1 (`SELECT TOP 3 d.ide, d.proide FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20260901 AND ISNULL(d.docoritip, 0) <> 44 AND d.proide = ? ORDER BY d.ide DESC`), cada una con `SELECT * FROM dbo.dcapro WHERE ide = ?` y su plantilla `SELECT TOP 1 * FROM dbo.dcapro WHERE proide = ? AND ide < ? ORDER BY ide DESC`; `columnas_distintas` entre cada línea y su plantilla.
  - **Debe salir / decide**: columnas de la lista con ≈ 0 valores no vacíos ⇒ reseteo confirmado. Una que el escritorio rellene siempre (p. ej. `fec` = fecha del albarán, `fec_igual_albaran` ≈ `n`) ⇒ se corrige §Reseteo con ese valor (v6). Columnas fuera de la lista que el escritorio no arrastra de la plantilla ⇒ se añaden.

### Preguntas abiertas para el humano (v5)

- **N4 (H31).** F-009 admite `cod_contrato` sin ninguna línea vinculada: enlaza `dca.ctride`, toma
  plantilla y almacén del contrato y no toca la medición. ¿Debe F-053 mandar `cod_contrato` siempre
  que la valoración tenga contrato, aunque no case ninguna línea? Recomendación: **sí** (el albarán
  queda colgado del contrato, como lo haría el escritorio). Es cambio de F-053 R12, no de F-009.
- **N5 (H2).** `SIGRID_ALBARAN_EMPRESAS_OBRA` con defecto **cerrado** `[]` (sin ella el modo
  extendido no encuentra ninguna obra: `obra_de_empresa_no_permitida`) y despliegue `[1]`, como las
  otras listas de R10. Alternativa: defecto `[1]`. Recomendación: cerrado.
- **N6 (H2, opcional).** ¿Rechazar obras de baja (`con.fecbaj` > 0)? Propuesta: **no** (un albarán
  tardío de una obra cerrada debe poder entrar; con `[1]` ya no hay ambigüedad que resolver).
- **N7 (H8).** El `precio ≥ 0` de Pydantic (400 sin código, toda la petición) pasa a fallo de línea
  `precio_negativo` (400 `lineas_no_validas`, junto con los demás fallos). ¿Conforme?
- **N8 (H15).** «Con aviso si difieren» se ha escrito como: aviso `iva_de_otro_proveedor` cuando el
  proveedor no tiene ninguna línea previa del producto y se usa la de otro. ¿Conforme, y bloqueante o
  informativo en F-053? Propuesta: informativo.
- **N9 (H18, si M18 sale libre).** Escribir `referencia_linea` en `dcapro.refent` hace visible en la
  UI de Sigrid el `id` de la línea de albaranes y obliga a `referencia_linea` ≤ 24 (sv9 manda un
  entero). Si M18 muestra que `refent` se copia a la factura, también aparecería allí. ¿Conforme?
- **N10 (H19).** F-009 solo rechaza fechas **futuras**; la ventana de plausibilidad (hoy − 365 días)
  queda en F-053. ¿Conforme?
- **N11 (H21).** F-009 normaliza mayúsculas y espacios del CIF, pero **no** quita el prefijo `ES` ni
  guiones (lo garantiza albaranes con F-052). ¿Conforme?
- **N12 (códigos nuevos).** Mapeo propuesto en `contrato_albaranes.md` §3.3 para F-053:
  `fecha_no_valida` → `revisar`, `obra_de_empresa_no_permitida` → `error`, `precio_negativo` →
  `revisar`, `paride_no_valido` → `no_admitido`; avisos nuevos, informativos. Es de albaranes (H25).

## Qué cambió en la v2 (lo que la v3 revisa va marcado)

- **Se amplía `sigrid/albaran`** (no hay ruta nueva). Dos modos, decididos por las **claves**
  del JSON: `lineas` o `referencia_externa` → extendido; ninguna → clásico; `lineas_recibidas`
  junto a cualquiera de ellas → 400 `peticion_mixta` (design §La decisión de fondo).
- **Modo clásico idéntico a hoy** (incluida la suma de `lineas_recibidas` al mismo `ctrpro`):
  sus casos de uso y modelos no se tocan y lo fija un **test de caracterización** con fichero
  dorado escrito sobre `dev` antes de cualquier cambio (T1, design §Caracterización).
- **Segunda llave `SIGRID_ALBARAN_WRITE_ENABLED`** (defecto `false`) cierra el `commit` de los
  dos modos de `sigrid/albaran` **y** de `albaran-directo` (R8); el dry-run no cambia.
- **Devolución que deja `canser` < 0: se admite** con aviso `servido_negativo`; `estser` se
  recalcula con la regla de hoy y puede volver a 0 (R18, R20).
- **Negativas en vinculadas y sin vincular** (R6, R18). Si M5 no encuentra devoluciones reales,
  **hipótesis A** (simétrica al alta), verificada con la primera devolución real del pipeline
  (T24, consulta abajo). Pregunta 8 cerrada (opción a).
- Aceptadas las propuestas 3-6 y 9-17: prefijo `ALB-`; productos `["MA9999"]`; partida y precio
  distintos del contrato con aviso; `dcapropar` y `log` fuera salvo M7/M13 (*v3: el `log` se
  escribe*); sin recálculo de `mov` posteriores (*v3: reabierto, pregunta N1*); almacén y centro derivados; `con.est` según M2; lista de reseteo, hora de
  Madrid e IVA por `dbo.iva` solo en el modo extendido; los viejos, obsoletos cuando F-053 esté
  en real (T18); prioridad 7.

## Resultados de T0 (primera pasada, 2026-10-02) y decisiones de la v3

Fuente: el fichero de resultados del humano (en `%TEMP%`, **no** se versiona: lleva datos de
negocio). Aquí solo cifras agregadas y conclusiones. M7 y M9 fallaron (error 130 de SQL
Server, corregido en `28afc96`) y M11 tenía un fallo del script (abajo).

> **v6**: M3, M7 y M13 se cerraron en la repetición del 2026-10-05 (§v6); M9 y M11 siguen abiertas.

| M | Resultado | Decisión en la spec v3 |
|---|---|---|
| M1 | `dca.synckey` vacío en los 312.644 albaranes; ningún `ALB-`; búsqueda sin índice, 0,1 s | **Cerrado**: idempotencia por `synckey` sin índice (R30) |
| M2 | Albaranes desde 2025: 99,97 % en `emp` 1. Estados de `conest` tip 14: 1 `PDT` Pendiente, 2 `COM` Comprobado, 3 `CON` Contabilizado, 10 `FAC` Facturado. `sercon.estini` = 0 en las tres series tip 14 (`AC`, `NTC`, `PROF`), y 0 no es un estado (solo 6 albaranes lo tienen). `mov.emp` = 1 en todos. Índice único `con_emptipcod (emp, tip, cod)` | `cod` por `emp` bajo el índice único (R26); `mov.emp` = `con.emp`; **`con.est` = 1 `PDT`** (R22): el «3» de los no facturados está sesgado por los ya contabilizados, el ciclo es Pendiente → Comprobado → Contabilizado → Facturado y el alta de junio con 1 se vio bien en la UI. Lo confirma la repetición de M13, que lee el `est` de la fila de alta en `log` |
| M3 | Partidas usadas en albaranes desde 2025: 100 % `tip 1`, `tipdes 0`; `tipvis` 0 (99,6 %) o 1. En `obrparpar`: `tip` 0 = 45.783, 1 = 349.408, 99 = 5. 5.207 pares (obra, código) repetidos | Imputable = `tip 1`, `tipdes 0`, `tipvis` 0/1 (R14). **Abierto**: cuántos repetidos quedan entre imputables (repetición) → pregunta N2 si hay |
| M4 | Escritorio, vinculadas desde 2025: partida distinta del `ctrpro` 5,3 % (5.178 de 98.145), precio distinto 1,5 %. `ctrpro` sin `paride`/`cenide`/`caaide` nulos | **Cerrado**: confirma R16/R17 (permitido con aviso); la herencia de partida por `NULL` no ocurre |
| M5 | 119.554 líneas negativas desde 2008 (112.379 sin vincular, 6.411 vinculadas). Muestra de 20: regla A en 13 (todas las que tienen `mov`), sin `mov` en 6, «?» en 1 | **Cerrado: regla A** (R18). La «?» es un albarán con fecha atrasada comparado con el `mov` anterior por `ide` (ver M10). Las 6 sin `mov` son **todas del mismo producto** (ide 571020): depende del producto, no de la devolución → repetición de M9 (`pro.tipmov` «Hace movimientos») |
| M6 | `ctrprodes.can` = cantidad negativa en 20 de 20; `canser` ≠ Σ `ctrprodes.can` en 13 de 5.348; `canser` < 0 en 750 `ctrpro` | **Cerrado**: coherente con admitir `canser` < 0 (R18, R20) |
| M7 | Falló (error 130) | Repetición |
| M8 | 649 obras con un almacén, 5 con dos; `ctr.almide` es de su obra en el 99,4 %; líneas sin partida: almacén de la obra 98,9 %, con el centro del almacén 90,8 % | **Cerrado** (R15); dos almacenes → `almacen_de_obra_no_resuelto` |
| M9 | Falló (error 130) | Repetición: ¿cuándo no hay `mov`? |
| M10 | En las 3 series medidas, la cadena de `almcan` cuadra en orden de `fechor` (0 roturas) y no en orden de `ide` (1 rotura en 2): **el escritorio recalcula los `mov` posteriores** cuando entra uno con fecha anterior | **Pregunta N1** (design §Fecha atrasada) |
| M11 | Hay **un producto genérico por empresa** (1, 31, 34; `tip 3`), todos con `comide` e `ivacomide` a 0 y `natide` propio. «0 líneas de MA9999» era **un fallo del script**: cogía el primer MA9999 de la lista (el de la empresa 31). `dbo.iva` se repite por empresa; `iva` es una fracción (0,16…) | Producto por `(emp, cod)`; cuenta e IVA de su última `dcapro`, naturaleza del maestro (R13). Repetición: líneas de cada MA9999 y comprobación `ivacuo = round(tot·iva, 2)` |
| M12 | El 77,4 % de los albaranes con contrato desde 2025 llevan alguna línea sin vincular | **Cerrado**: confirma el diseño |
| M13 | 13.934 filas de alta de albarán (`tab 'con'`, `tip 14`, `ope 1`) en los últimos 300.000 `ide` de `log` (la comparación con albaranes salió mal: ventana desde fecha 0) | **Se escribe** la fila de alta, con `usu` nuevo y obligatorio en la petición (R5, R25). Repetición: cobertura, `est` inicial y `ori` |
| M14 | La cabecera de la API difería en forma de pago, efecto y dirección, pero **la muestra era de otros proveedores**: la API copió la de su propio proveedor. `dcapro.prepma` de la API = el de la plantilla; el del escritorio coincide con el PMP vigente del almacén. Resto de columnas de línea, sin diferencias | Plantilla de cabecera **solo del mismo proveedor**, sin *fallback* (R11); `prepma` = PMP resultante (R21). Repetición con el mismo proveedor, frente al maestro `prv` y `prepma` contra su `mov` |
| M15 | 748 `mov` con stock negativo desde 2025, en 20 almacenes | **Cerrado**: solo aviso |

**Para F-007 (proformas):** la serie `PROF<aa>/` es `tip 14`, como los albaranes: las proformas
son albaranes de compra con otra serie.

## Repetición de T0 (v4; **sustituida por la de §T0 v5**)

> v5 (H28): **una sola** repetición, con el script ampliado (tasks T0a): `--solo M3 M7 M9 M11 M13
> M14 M16 M17 M18`. Lo de abajo describe lo que ya traía el script para M3, M7, M9, M11, M13 y M14.

M7 y M9 son las que fallaron. Las otras cuatro traen consultas nuevas para cerrar sus [Mn]:
partidas repetidas entre imputables (M3), banderas `pro.tipmov`/`tipinv` y productos de las
líneas sin `mov` (M9), cada MA9999 por empresa e IVA usado (M11), `est` y `ori` de la fila de
alta en `log` y su cobertura (M13), y M14 con el mismo proveedor, frente al maestro `prv` y con
`prepma` contra su `mov`. Se pega de vuelta el fichero de `%TEMP%` entero. La prueba de humo
ahora detecta el patrón del error 130 (agregado sobre subconsulta o sobre un `APPLY` escalar).

## T0: comando para PowerShell

**Retirado en T0c (v8.1)**: `scripts/medir_f009_t0.py` y `tests/test_f009_t0_script.py` salieron del repositorio
en un commit propio (`git rm`); siguen en el historial. Lo que sigue queda como registro.

El script `scripts/medir_f009_t0.py` lanza M1-M15 como SELECT por `POST /api/sql/read` (nada de
escrituras ni de endpoints de dominio; el propio cliente rechaza en local cualquier SQL que no
sea `SELECT`/`WITH` de una sentencia). Lee `SIGRID_API_BASE_URL` y `SIGRID_API_FUNCTION_KEY` del
entorno o, si no están, del `.env` de la raíz de sigrid-api (las dos claves están allí), y no
las imprime nunca. Las 42 sentencias pasan el mismo `SqlQueryGuard` de `sql/read` en la prueba
de humo (`tests/test_f009_t0_script.py`, 97 tests sin red). **No se ha ejecutado contra la API.**

```powershell
cd C:\Users\pgris\PycharmProjects\sigrid-api
git switch feature/F-009-alta-albaran-compra
& .\.venv\Scripts\python.exe -m scripts.medir_f009_t0
# una o varias:  & .\.venv\Scripts\python.exe -m scripts.medir_f009_t0 --solo M5 M6
```

- Tarda varios minutos: las consultas pesadas (M1, M3, M4, M6-M10, M12, M13, M15) piden
  hasta 200 s cada una, por debajo del corte de 230 s; la instancia `dev` admite
  `MAX_QUERY_TIMEOUT_SECONDS` 230 (§4.1). Si una falla, el script lo anota en su bloque y
  sigue con las demás.
- **Qué pegar de vuelta**: el fichero que indica al final (`%TEMP%\f009_t0_<fecha>.txt`),
  **entero**. Cada medición trae sus filas y un bloque «CONCLUSIÓN» con lo que necesita la
  spec (p. ej. `con.est` inicial probable, regla A/B de las devoluciones, columnas de la lista
  de reseteo con diferencia). Una medición que falle se repite con `--solo`.
- El fichero lleva datos de negocio (códigos, CIF, precios): no se versiona, y el script se
  niega a escribirlo dentro del repositorio.
- Añadidos frente a las consultas de §Mediciones: M2 mide también el `est` de los albaranes
  aún sin facturar (el inicial más probable); M4 cuenta los `caaide` nulos; M5 contrasta la
  regla A/B con el `mov` anterior de cada devolución de la muestra; M9 cuenta `mov` según la
  línea tenga partida o no; M10 compara las roturas de la cadena de `almcan` en orden de fecha
  y de `ide`; M13 acota por fechas la ventana de `log`.

## Hallazgos del código actual (el modo clásico los conserva)

1. **No hay ni un test** de `sigrid/albaran` ni de `albaran-directo`: de ahí T1.
2. El `cod` se calcula **fuera** de la transacción (`_next_cod`): carrera con el escritorio.
3. `con.est = 1` y `mov.emp = 1` **escritos a mano**; la serie `AC` medida en junio
   (`serie_stock.txt`, sin versionar) tenía `sercon.estini = 0`.
4. Fecha y hora con `datetime.now()`: en Azure es **UTC**, no Madrid.
5. La `dcapro` se clona de la **última línea del mismo producto en cualquier obra**: si el
   `ctrpro` trae `paride`/`cenide`/`caaide` `NULL`, se quedan los de esa otra línea, y siempre
   arrastra medición, analítica, desglose y `prepma` ajenos. `albaran-directo` hereda además el
   almacén y la partida.
6. `su_referencia` admite 200 caracteres y `dca.entref` es de 128.
7. Tasa de IVA = `ivacuo/tot` del `ctrpro`: con `tot` 0 sale 0.
8. El modelo clásico **ignora** las claves que no conoce: por eso `peticion_mixta` se decide
   antes de validar.

## Mediciones (T0) — solo lectura, por `sql/read`

Texto de la v1. La versión vigente de cada consulta es la de `scripts/medir_f009_t0.py` (M7 y
M9 reescritas; M3, M11, M13 y M14 ampliadas).

Setup de `azure-apps/sigrid_api.md` §8 (`$base`, `$headers`). Cada consulta:

```powershell
function Q($sql, $p = @()) { $b = @{ database = "ruesma"; sql = $sql; parameters = $p; max_rows = 200 } | ConvertTo-Json -Depth 5
  (Invoke-RestMethod -Uri "$base/api/sql/read" -Method Post -Headers $headers -ContentType "application/json" -Body $b) | ConvertTo-Json -Depth 8 }
```

- **M1 `synckey`** (¿libre?, ¿coste sin índice?):
  `SELECT COUNT(*) AS total, SUM(CASE WHEN ISNULL(synckey, '') <> '' THEN 1 ELSE 0 END) AS con_synckey FROM dbo.dca`;
  `SELECT TOP 20 LEFT(synckey, 6) AS prefijo, COUNT(*) AS n FROM dbo.dca WHERE ISNULL(synckey, '') <> '' GROUP BY LEFT(synckey, 6) ORDER BY n DESC`;
  coste: `Measure-Command { Q "SELECT c.ide, c.cod FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?" @(14, "ALB-no-existe") }`.
- **M2 `emp`, estado, serie e índice**:
  `SELECT c.emp, c.est, COUNT(*) AS n FROM dbo.con c WHERE c.tip = 14 AND c.fec >= 20250101 GROUP BY c.emp, c.est`;
  `SELECT tip, est, cod, res FROM dbo.conest WHERE tip = 14`; `SELECT ide, tip, cod, emp, estini, act FROM dbo.sercon WHERE tip = 14`;
  `SELECT emp, COUNT(*) AS n FROM dbo.mov WHERE doctip = 14 AND fec >= 20250101 GROUP BY emp`;
  `SELECT i.name, i.is_unique, c.name AS col, ic.key_ordinal FROM sys.indexes i JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id WHERE i.object_id = OBJECT_ID('dbo.con') ORDER BY i.name, ic.key_ordinal`.
- **M3 partidas**:
  `SELECT p.tip, p.tipdes, p.tipvis, COUNT(*) AS n FROM dbo.dcapro d JOIN dbo.obrparpar p ON p.ide = d.paride JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 GROUP BY p.tip, p.tipdes, p.tipvis`;
  `SELECT tip, COUNT(*) AS n FROM dbo.obrparpar GROUP BY tip`;
  `SELECT COUNT(*) AS repetidos FROM (SELECT obride, cod FROM dbo.obrparpar GROUP BY obride, cod HAVING COUNT(*) > 1) x`.
- **M4 vinculadas del escritorio con partida o precio distintos del contrato**:
  `SELECT COUNT(*) AS n, SUM(CASE WHEN ISNULL(d.paride, 0) <> ISNULL(p.paride, 0) THEN 1 ELSE 0 END) AS partida_distinta, SUM(CASE WHEN ABS(d.pre - p.pre) > 0.0001 THEN 1 ELSE 0 END) AS precio_distinto FROM dbo.dcapro d JOIN dbo.ctrpro p ON p.ide = d.linoriide JOIN dbo.con c ON c.ide = d.docide WHERE d.docoritip = 44 AND c.tip = 14 AND c.fec >= 20250101`;
  `SELECT SUM(CASE WHEN paride IS NULL THEN 1 ELSE 0 END) AS paride_null, SUM(CASE WHEN cenide IS NULL THEN 1 ELSE 0 END) AS cenide_null, COUNT(*) AS n FROM dbo.ctrpro`.
- **M5 devoluciones reales y su `mov`**:
  `SELECT ISNULL(d.docoritip, 0) AS docoritip, COUNT(*) AS n, MIN(c.fec) AS desde, MAX(c.fec) AS hasta FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND d.can < 0 GROUP BY ISNULL(d.docoritip, 0)`;
  `SELECT TOP 20 c.cod, c.fec, d.ide AS linea, d.proide, d.almide, d.can, d.pre, d.paride, m.ide AS mov, m.tip, m.oritip, m.destip, m.canent, m.cansal, m.pre AS mpre, m.prepma, m.almcan, m.almpma, m.fechor FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.mov m ON m.docide = d.docide AND m.linide = d.ide WHERE c.tip = 14 AND d.can < 0 ORDER BY d.ide DESC`;
  por cada `mov`, el anterior: `SELECT TOP 1 ide, almcan, almpma, fechor FROM dbo.mov WHERE proide = ? AND almide = ? AND ide < ? ORDER BY ide DESC`.
  Regla A si `canent` = can y `almpma` = (stock·pma + can·pre)/(stock + can); B si `cansal` = |can| y el PMP no cambia.
- **M6 vinculadas negativas**:
  `SELECT TOP 20 d.ide, d.can, d.linoriide, s.can AS ctrprodes_can, p.can AS ctr_can, p.canser FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.ctrprodes s ON s.lindeside = d.ide AND s.docdestip = 14 JOIN dbo.ctrpro p ON p.ide = d.linoriide WHERE c.tip = 14 AND d.docoritip = 44 AND d.can < 0 ORDER BY d.ide DESC`;
  `SELECT COUNT(*) AS descuadres FROM dbo.ctrpro p WHERE p.ide IN (SELECT linoriide FROM dbo.dcapro WHERE docoritip = 44 AND can < 0) AND ABS(p.canser - (SELECT ISNULL(SUM(s.can), 0) FROM dbo.ctrprodes s WHERE s.docproide = p.ide AND s.docdestip = 14)) > 0.001`.
- **M7 `dcapropar`**: `SELECT COUNT(*) AS lineas, SUM(CASE WHEN EXISTS (SELECT 1 FROM dbo.dcapropar x WHERE x.docproide = d.ide) THEN 1 ELSE 0 END) AS con_desglose, SUM(CASE WHEN ISNULL(d.parcandes, 0) <> 0 THEN 1 ELSE 0 END) AS parcandes FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.paride > 0`.
- **M8 almacén de obra**:
  `SELECT n_almacenes, COUNT(*) AS obras FROM (SELECT obride, COUNT(*) AS n_almacenes FROM dbo.alm WHERE obride > 0 GROUP BY obride) x GROUP BY n_almacenes`;
  `SELECT SUM(CASE WHEN a.obride = t.obride THEN 1 ELSE 0 END) AS alm_de_su_obra, COUNT(*) AS n FROM dbo.ctr t LEFT JOIN dbo.alm a ON a.ide = t.almide`;
  `SELECT CASE WHEN a.obride = d.obride THEN 'alm_de_la_obra' ELSE 'otro' END AS tipo, ISNULL(a.paride, 0) AS alm_paride, CASE WHEN d.cenide = a.cenide THEN 1 ELSE 0 END AS cen_del_alm, COUNT(*) AS n FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.alm a ON a.ide = d.almide WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.paride, 0) = 0 GROUP BY CASE WHEN a.obride = d.obride THEN 'alm_de_la_obra' ELSE 'otro' END, ISNULL(a.paride, 0), CASE WHEN d.cenide = a.cenide THEN 1 ELSE 0 END`.
- **M9 ¿un `mov` por línea?**: `SELECT d.tipsininv, COUNT(*) AS albaranes, SUM(x.lineas) AS lineas, SUM(x.movs) AS movs FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide CROSS APPLY (SELECT (SELECT COUNT(*) FROM dbo.dcapro p WHERE p.docide = d.ide) AS lineas, (SELECT COUNT(*) FROM dbo.mov m WHERE m.docide = d.ide) AS movs) x WHERE c.tip = 14 AND c.fec >= 20260701 GROUP BY d.tipsininv`.
- **M10 fecha atrasada**: `SELECT TOP 20 m.ide, m.proide, m.almide, m.fechor, m.canent, m.almcan FROM dbo.mov m WHERE m.doctip = 14 AND m.fec >= 20260101 AND EXISTS (SELECT 1 FROM dbo.mov n WHERE n.proide = m.proide AND n.almide = m.almide AND n.ide < m.ide AND n.fechor > m.fechor) ORDER BY m.ide DESC`;
  para uno: `SELECT ide, fechor, canent, cansal, almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ? ORDER BY fechor, ide` → ¿el `almcan` de los posteriores incluye la entrada atrasada?
- **M11 productos genéricos e IVA**:
  `SELECT c.ide, c.cod, c.res, c.tip, c.emp, c.fecbaj, p.ivacomide, p.comide, p.natide, p.medide, p.gaside FROM dbo.con c JOIN dbo.pro p ON p.ide = c.ide WHERE c.cod IN (?, ?, ?, ?)` con `@("MA9999","SM9999","SB9999","QA9999")`;
  `SELECT TOP 30 d.cueide, d.ivaide, d.natide, d.unimed, d.caaide, COUNT(*) AS n FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ? GROUP BY d.cueide, d.ivaide, d.natide, d.unimed, d.caaide ORDER BY n DESC` (el `ide` de MA9999);
  `SELECT i.ide, c.cod, i.iva FROM dbo.iva i JOIN dbo.con c ON c.ide = i.ide`.
- **M12 ¿mezcla el escritorio?**: `SELECT COUNT(DISTINCT d.ide) AS con_lineas_sin_vincular, (SELECT COUNT(*) FROM dbo.dca d2 JOIN dbo.con c2 ON c2.ide = d2.ide WHERE c2.tip = 14 AND c2.fec >= 20250101 AND d2.ctride > 0) AS con_contrato FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide JOIN dbo.dcapro p ON p.docide = d.ide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.ctride > 0 AND ISNULL(p.docoritip, 0) <> 44`.
- **M13 ¿fila de `log` al crear un albarán?**: `SELECT COUNT(*) AS n FROM dbo.log WHERE ide > (SELECT MAX(ide) - 300000 FROM dbo.log) AND tab = 'con' AND tip = 14 AND ope = 1`, frente a los albaranes del mismo periodo.
- **M14 diff de columnas** (la lista de reseteo): `SELECT TOP 3 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = 14 AND d.ctride > 0 AND c.fec >= 20260901 ORDER BY c.ide DESC`; después `SELECT * FROM dbo.<con|dca> WHERE ide IN (?, ?, ?, ?)` y `SELECT * FROM dbo.dcapro WHERE docide IN (?, ?, ?, ?)` con esos tres y el de `AC26/15951`; anotar cada columna en que difieran.
- **M15 stock negativo**: `SELECT COUNT(*) AS n FROM dbo.mov WHERE almcan < 0 AND fec >= 20250101`.

## Manuales (T20-T24)

Setup y función `Q` de §Mediciones. Dry-run **clásico** (T20), el mismo cuerpo de junio:
`{ "database": "ruesma", "cod_contrato": "CTSU16/0206", "cod_obra": "0404", "cif_proveedor": "<CIF>",
"su_referencia": "prueba-F009", "lineas_recibidas": [ { "ctrpro_ide": <ide>, "cantidad": 1 } ] }`.

Dry-run **extendido** (T21; los `<...>` se leen antes del contrato y de las partidas de la obra):

```json
{ "database": "ruesma", "cod_obra": "0404", "cif_proveedor": "<CIF>", "cod_contrato": "CTSU16/0206",
  "referencia_externa": "ALB-prueba-F009-1", "su_referencia": "prueba-F009", "usu": "<usuario>", "commit": false,
  "lineas": [
    { "referencia_linea": "1", "ctrpro_ide": <ide>, "cantidad": 1, "precio": 100.0 },
    { "referencia_linea": "2", "producto": "MA9999", "descripcion": "Prueba F-009", "unidad": "UD", "cantidad": 1, "precio": 1.0, "partida": "<cod>" },
    { "referencia_linea": "3", "ctrpro_ide": <ide>, "cantidad": -1, "precio": 100.0, "partida": "<cod>" },
    { "referencia_linea": "4", "producto": "QA9999", "descripcion": "Prueba F-009 maquinaria", "unidad": "H", "cantidad": 1, "precio": 1.0 } ] }
```

**`prepma` de la primera alta real (T24; T22 con el albarán de prueba)**, solo lectura, con su `referencia_externa`:
`SELECT m.ide, m.proide, m.almide, m.prepma, (SELECT TOP 1 a.almpma FROM dbo.mov a WHERE a.proide = m.proide AND a.almide = m.almide AND a.ide < m.ide ORDER BY a.fechor DESC, a.ide DESC) AS pmp_anterior FROM dbo.mov m JOIN dbo.dca d ON d.ide = m.docide WHERE d.synckey = ? ORDER BY m.ide`
→ cuadra si `prepma` = `pmp_anterior` (salvo que un albarán posterior con fecha anterior haya recalculado ese `mov`, M10).
En T22, además, el `prepma` de un albarán del escritorio dado de alta el mismo día en el mismo almacén.

**Primera devolución real (T24)**, solo lectura, con la `referencia_externa` de ese albarán:

- líneas y su `mov`: `SELECT d.ide AS linea, d.proide, d.almide, d.can, d.pre, d.linoriide, m.ide AS mov, m.canent, m.cansal, m.almcan, m.almpma FROM dbo.dcapro d JOIN dbo.dca a ON a.ide = d.docide LEFT JOIN dbo.mov m ON m.docide = d.docide AND m.linide = d.ide WHERE a.synckey = ? AND d.can < 0`;
- `mov` anterior: `SELECT TOP 1 ide, almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ? AND ide < ? ORDER BY ide DESC`
  → cuadra si `almcan` = anterior + `can` y `almpma` = (anterior·pma + `can`·`pre`)/(anterior + `can`);
- medición: `SELECT p.ide, p.can, p.canser, (SELECT SUM(s.can) FROM dbo.ctrprodes s WHERE s.docproide = p.ide AND s.docdestip = 14) AS suma_destinos FROM dbo.ctrpro p WHERE p.ide = ?`
  → `canser` = `suma_destinos`; y `SELECT estser, estfac FROM dbo.ctr WHERE ide = ?` frente a `Σcanser ≥ Σcan`;
- en la UI, la ficha de stock del producto en ese almacén debe dar el mismo stock y PMP.

## Forma final para alinear F-053 (pregunta 18, la hace el líder de albaranes) — v3

> **Contrato completo con albaranes (2026-10-05):**
> `specs/F-009-alta-albaran-compra/contrato_albaranes.md` — petición y respuesta campo a campo, casos
> de línea (almacén, devoluciones, compuestas repartidas), códigos → estados de F-053 y **33 huecos**
> entre F-009 v4, F-053 v5, F-051 v3 y F-049 v4 (9 bloqueantes). Lo de abajo es el resumen de la v3:
> desde la v5.1 no hay campo `almacen` (línea sin partida = `partida` ausente) ni `fecha_no_valida`;
> desde la v6, `paride` opcional, `referencia_linea` de 1-24 (va a `dcapro.refent`) y lista blanca
> `MA9999`/`QA9999` con el producto elegido por línea; manda el contrato.

Ruta `POST /api/sigrid/albaran` (la de siempre), modo extendido. Petición:

```json
{ "database": "ruesma", "cod_obra": "0404", "cif_proveedor": "<CIF>", "cod_contrato": "CTSU16/0206 o null",
  "referencia_externa": "ALB-<document_id>", "su_referencia": "<nº de albarán del proveedor, ≤128>",
  "usu": "<usuario de Sigrid, ≤24>", "fecha_albaran": 20261001, "empide": null, "commit": false,
  "lineas": [ { "referencia_linea": "<id de línea, ≤64>", "ctrpro_ide": 123, "producto": null,
                "descripcion": "<≤128, obligatoria sin vincular>", "unidad": "<≤8>", "cantidad": -2.5,
                "precio": 10.0, "partida": "<cod de obrparpar>", "almacen": false } ] }
```

Exactamente uno de `ctrpro_ide`/`producto` y uno de `partida`/`almacen:true`; `cantidad` ≠ 0
(negativa = devolución, en los dos tipos); `precio` ≥ 0 obligatorio; `ctrpro_ide` exige
`cod_contrato`; **no** enviar `lineas_recibidas` (→ `peticion_mixta`). **Nuevo en v3:** `usu`
obligatorio (va a la fila de alta de `log`; F-053 ya tiene `ALTA_SIGRID_USUARIO`), y el
proveedor tiene que tener algún albarán previo (si no, `proveedor_sin_albaran_previo`: ya no se
copia la cabecera de otro proveedor, así que el antiguo aviso «plantilla de otro proveedor»
desaparece y pasa a ser este error).

Respuesta 200 (dry-run, commit o idempotente): todos los campos de la respuesta clásica (`ok`,
`database`, `committed`, `dry_run`, `con_ide`, `cod`, `contrato`, `cabecera`, `lineas`,
`movimientos`, `estados_contrato`, `totales`, `warnings`) más `estado`
(`previsto`|`creado`|`idempotente`), `referencia_externa`, `avisos[{codigo, mensaje}]` y
`filas`; cada línea suma `indice`, `referencia_linea`, `tipo` (`vinculada`|`sin_vincular`),
`producto`, `paride`, `partida`, `almacen`, `cenide` y `avisos`. Error 400: `{ok:false, error,
details:{type, codigo, lineas?:[{indice, referencia_linea, codigo, mensaje}]}}`; 400 sin
`codigo` = validación Pydantic (`details.validation`); 500 = inesperado.

Códigos de error: `peticion_mixta`, `escritura_albaranes_deshabilitada`,
`base_de_datos_no_permitida`, `demasiadas_lineas`, `referencia_no_permitida`,
`referencia_en_conflicto`, `obra_no_encontrada`, `obra_ambigua`, `contrato_no_encontrado`,
`contrato_ambiguo`, `usuario_no_valido`, `proveedor_sin_albaran_previo`, `estado_inicial_no_encontrado`,
`almacen_de_obra_no_resuelto`, `colision_de_clave`, `filas_afectadas_inesperadas`,
`lineas_no_validas`; por línea: `linea_no_es_del_contrato`, `producto_no_permitido`,
`producto_no_encontrado`, `partida_no_encontrada`, `partida_ambigua`, `partida_no_imputable`.
Avisos: `producto_sin_historico`, `supera_pendiente`,
`partida_distinta_del_contrato`, `precio_distinto_del_contrato`, `servido_negativo`,
`stock_negativo`, `cod_provisional`. Para F-053: los «avisos bloqueantes» pasan a compararse por
`codigo`, no por texto; `colision_de_clave` y los 500 se pueden reintentar con la misma
referencia (la idempotencia lo hace seguro).

## Preguntas de la v3: respondidas por el humano (2026-10-02)

- **N1 → (b).** El movimiento de stock se fecha en el momento del alta (`mov.fec`, `hor` y
  `fechor` de ahora, hora de Madrid); el albarán conserva su fecha. No se recalculan los `mov`
  posteriores. El balance vigente se lee por `fechor DESC, ide DESC` (R19, design §Fecha
  atrasada, L12/E7).
- **N2 → rechazo.** Código de partida repetido entre las imputables de la obra: la línea falla
  con `partida_ambigua` y el revisor lo corrige en sv4 (R14). Sin `paride` en la petición.
- **N3 → retirar el script.** En cuanto T0 quede cerrada, y antes de T1, un commit propio con
  `git rm scripts/medir_f009_t0.py tests/test_f009_t0_script.py`: sale del alcance de cobertura
  y mutación y queda en el historial (tasks T0). **Todavía no se retira**: el humano va a
  repetir `--solo M3 M7 M9 M11 M13 M14`.

No quedan preguntas de diseño abiertas. Las 1-17 de la v1 están respondidas y la 18 (alinear
F-053) es del líder de albaranes; para F-053, N1 no cambia el contrato.

## Riesgo residual

Ninguna escritura hasta T22, con autorización expresa, y T22 no se hace sin M9 cerrada (puerta
H20). Al desplegar con la llave en `false`, el `commit` del modo clásico y de `albaran-directo`
queda cerrado (decidido; nadie los usa en vivo). Devoluciones con la regla A medida en el
escritorio; T24 vigila la primera real del pipeline. *(v6)* T0b hecha y volcada; hasta T0b-bis
(`--solo M9 M11 M14 M16 M17`, con M14b, M16b y M17b), su volcado (v7, o PARADA si M16b no da regla
para la analítica de las sin vincular) y la retirada del script (N3), F-009 no pasa a `in_progress`.
La puerta H20 cubre MA9999 y QA9999.
