<!-- progress/review_F-007_proforma.md -->
Revisión completa del bloque funcional (pasada 1) sobre HEAD `fe85523`: caso de uso, statements, modelos y ruta de F-007

# F-007 · Revisión funcional acotada (proforma)

- **Veredicto del bloque:** CHANGES_REQUESTED. Lo provoca D1 (contradice R17). D2-D5 son menores. El veredicto
  binario de la feature lo da el informe consolidado del líder.
- **Nivel de rigor:** `critico`, el que declara la feature. En este encargo solo se mira la conducta frente a R1-R30 y a
  `contrato_proformas.md` v1. `init.sh` y la suite completa no se ejecutaron porque así lo pidió el coordinador.
- **Ejecutado:** `python -m pytest tests/test_f007_*.py -q` dio **466 passed** en 3,83 s. Hice cuatro sondas sobre los
  dobles de `tests/f007_dobles.py`, guardadas en el scratchpad y sin tocar el árbol: forma JSON de `existente`, la
  idempotente de dentro, la hora de Madrid con el cambio de año y el respaldo de R14.

## Defectos (cambios requeridos)

1. **D1 · R17: un producto del contrato sin plantilla se escribe con IVA 0** (media).
   `application/use_cases/create_albaran_compra_use_case.py:1566-1568` (`_de_la_plantilla_del_contrato`) pone
   `natide`, `cueide`, `caaide` **e `ivaide`** a 0 cuando no hay L8b ni L8. R17 dice sin condiciones que el IVA sale
   «del `ctrpro` de ese producto». Escenario: una línea nueva con un producto del contrato que nunca ha salido en un
   albarán (L8b y L8 vacías) y un `ctrpro.ivaide` del 21 %. Resultado: `dcapro.ivaide` 0, `ivacuo` 0, y `totiva` y
   `totdoc` de la proforma por debajo. Además el aviso dice «cuenta e IVA a 0». El test
   `tests/test_f007_perfil.py:413-417` fija esa conducta, y la desviación 10 del informe la declara.
   Arreglo: conservar el `ivaide` del `ctrpro` también sin plantilla. Ojo: la fila toma el IVA **de la plantilla**
   (`albaran_compra_statements.py:1006`, `(plantilla or {}).get("ivaide")`), así que sin plantilla hay que pasárselo
   de forma explícita. La otra salida es que el humano acepte la desviación 10 y se enmiende R17. En los dos casos hay
   que corregir el test.
2. **D2 · R28 no repite R23 bajo el applock** (baja, es una carrera). Dentro de la transacción, E1
   (`create_albaran_compra_use_case.py:727-731`) decide con `_resolver_referencia` (`:637-655`), que es la regla de
   F-009: mismo `entide` y misma obra. No mira ni `cla` ni contrato, y L11 no trae esas columnas. Pasa lo mismo fuera,
   en la L11 del núcleo (`:338-345`), que se ejecuta después de LP5. Escenario: dos peticiones con `PRF-77`, una con el
   contrato A y otra con el B del mismo subcontratista y obra (la bandeja reenvía con `cod_contrato` mientras el
   primer commit sigue en marcha). Las dos pasan LP5. La primera crea la proforma en A. La segunda, bajo
   `SIGRID_REFEXT_14`, recibe `idempotente` con el documento de A y `contrato.cod` = B, cuando R23 y R28 piden
   `referencia_en_conflicto`. Pasaría lo mismo con un `AC` de `sigrid/albaran` con ese `synckey`; con D11 no ocurre,
   porque `PRF-` y `ALB-` no se cruzan. El test `test_f007_r28_dentro_aparece_la_misma_referencia_y_es_idempotente`
   da por buena una fila L11 sin contrato.
   Arreglo: una costura en la que el perfil valide la fila que encuentra E1 (LP5 por el cursor más `es_proforma`), o
   que el humano acepte el residuo y se reescriba R28. La desviación 8 lo justifica solo con los prefijos.
3. **D3 · Una `idempotente` resuelta dentro de la transacción trae `origen` y los avisos de la hoja** (baja).
   `create_proforma_use_case.py:257-265` llama a `_convertir` con `origen` y `avisos` aunque el núcleo devuelva
   `estado` `idempotente`. La sonda da `origen` = {2651.0, 17024.28, …} en lugar de `null`. Contradice
   `contrato_proformas.md` §3: «En `idempotente` viene el contrato y `origen` es nulo». La idempotente de fuera
   (`_idempotente`, `:327-330`) sí lo cumple. Arreglo: con `nucleo.estado == "idempotente"`, `origen=None` y
   `avisos=[]`. Hay que añadir la aserción a `test_f007_transaccion.py:130-139`.
4. **D4 · R13/R14: una línea con `producto` y `medicion_contrato` > 0 se vincula en silencio** (baja, riesgo de
   integración). `proforma_models.py:158-161` la clasifica como línea de contrato y `revisar_lineas` y
   `traducir` (`proforma_statements.py:389-415`, `:690-696`) descartan el `producto` sin avisar. La sonda,
   con un contrato de una sola línea, sin `partida`, con medición 55 frente a 100, unidad UD frente a M3 y precio 99
   frente a 10, devuelve esa línea vinculada al `ctrpro` 1 sin ningún fallo. R14 dice «ninguna → `linea_no_es_del_contrato`».
   El respaldo laxo está documentado (desviación 6, nota ² del contrato), pero que se ignore el `producto` no lo está.
   Si `proformas` reenvía la columna «Medición de Contrato» también en las filas nuevas, esas líneas acabarían
   vinculadas. También es incoherente con R8: `_contiene` (`:289-297`) es estricto y da `False` para esa misma línea,
   así que la conducta cambia según haya uno o varios candidatos.
   Arreglo propuesto: rechazar `producto` junto con `medicion_contrato` > 0 (400 de R2), o que el `producto` decida
   que la línea es nueva.
5. **D5 · R18 «hora de Madrid» y el cambio de año sin test en F-007** (baja, rigor crítico, R34). Todos los tests usan
   `AHORA` = 08:15 UTC y ninguno ejercita la conversión de `create_proforma_use_case.py:179`. La conducta es correcta
   según la sonda: el 31-08 a las 22:30 UTC, `periodo` 202609 da `previsto`, y a las 21:30 UTC da
   `periodo_no_valido`. El 31-12-2026 a las 23:30 UTC, `periodo` 202612 sale con `PROF26/`, `fec` 20261231 y `entref`
   `PROF1226_0719`. Hay que fijar esos tres casos en `test_f007_use_case.py`.

## Los diez puntos del encargo

| # | Punto | Resultado |
|---|---|---|
| 1 | R14 `ctrpro_ide` | OK. `identificar_linea` solo comprueba que el `ctrpro` es del contrato y lo devuelve tal cual. Con `cod_contrato` o con un solo candidato, un `ctrpro` de otro contrato de la obra da `linea_no_es_del_contrato` (`test_f007_r14_ctrpro_ide_de_otro_contrato_o_de_ninguno`). Con varios candidatos sale `contrato_no_resuelto` u `hoja_de_varios_contratos`, que es lo que documenta el contrato §4 |
| 2 | R16 | OK. `producto_obligatorio` aunque el contrato tenga un solo producto (`test_f007_r16_..._uno_solo`); sin producto por defecto en ningún camino, también con `sin_contrato` |
| 3 | R24/R28 | OK por contrato. LP1 filtra por `ctride` con `PROF%` en `cod` o `entref` y sin `PREV`, así que entra la `AC` con `entref` `PROF…`. La `existente` trae las líneas LP6, en la previa y con `commit`, sin transacción. Bajo el applock se repite con LP1 y, si cambia, responde sin escribir (`test_f007_r28_*`). La parte de R23 dentro falla: D2 |
| 4 | R12 | OK. Serie `PROF<aa>/` del año de la fecha de R18, rellenada a 5 cifras (`PROF26/01282`); `cla` 141; `docoritip` y `docoriide` 0; `entref` por defecto `PROF<MMAA>_<obra>` (`test_f007_r12_*`) |
| 5 | R15 | OK. Las líneas se construyen como la vinculada del núcleo (`canoriori` = `ctrpro.can`, `imporiori` = `ctrpro.tot` y el resto de los campos `*ori*` a 0). La partida es la del `ctrpro` (código y `paride`) o `partida_imputacion`, con su aviso |
| 6 | R19-R21 | OK. Tolerancias estrictas (> 0,05 € y > 0,001) en `Decimal`. 100 % exacto no avisa; 110 % exacto da `supera_contrato` y por encima, `supera_contrato_10` (`test_f007_r21_supera_contrato_y_10_en_el_borde`). Con importe de contrato 0 no hay porcentaje ni aviso |
| 7 | R18 | Conducta OK; falta el test (D5). Una `fecha_proforma` futura dentro del mes en curso se admite (O5) |
| 8 | R8/R9 | OK. Fecha ≤ fin del periodo, con líneas, por CIF o por nombre normalizado; con varios candidatos decide por las líneas; el `reparto` va por `referencia_linea` y la ruta lo pone en `details.reparto` |
| 9 | Desviaciones 1-14 | Contradicen la spec la 10 (D1) y la 8 (D2). La 6 está documentada, pero deja abierto D4. Las demás son coherentes con la spec y con el contrato v1. Sobre la 13: R31 protege los tests de F-009 y F-015, no el de F-012 |
| 10 | Forma §3 | OK. `existente` lleva `cabecera {fec, entref}`, `totales {totbas, n_lineas}`, `contrato`, `origen` y, por línea, `dcapro_ide`, `linoriide`, `producto`, `cantidad`, `precio` e `importe`. También trae las claves del modo extendido (`database`, `dry_run`, `ok`, `warnings`, `filas`…). La idempotente de dentro no cumple la forma: D3 |

## Observaciones (sin cambio obligatorio; las decide el humano)

- **O1.** `existente` pierde el aviso de línea `anterior_distinto_de_sigrid`, porque `avisos_linea` no se usa en
  `create_proforma_use_case.py:247`. Las líneas son las de LP6 y no se casan con las de la petición. El contrato §3
  lista ese aviso sin decir si es de cabecera o de línea.
- **O2.** En las líneas de `existente`, `proide` vale 0, `referencia_linea` va vacío y, en las no vinculadas,
  `ctrpro_ide` es 0 en lugar de `null` (en la previa es `null`). `proformas` no debería leer esos campos, porque §3
  solo promete los seis de arriba.
- **O3.** `otra_del_mes` se salta también la `existente` del mismo total (`buscar_del_mes`, `:645`). Encaja con el
  ejemplo de §3 y con R35, pero el texto de R24 es ambiguo, así que conviene dejarlo escrito.
- **O4.** `traducir` pasa `ctr.entcif` como CIF, y `locate_contract` compara `t.entcif = ?` con el valor ya
  normalizado. Un `entcif` con espacios o guiones daría `contrato_no_encontrado` después de que R7 o R8 hayan resuelto
  el contrato. Un `entcif` vacío produce un `ValidationError`, que llega como 400 sin `codigo`. Es un caso raro, pero
  es un error confuso para `proformas`.
- **O5.** `fecha_proforma` puede ser posterior a hoy si cae dentro del mes en curso, y un test lo fija
  (`(202610, 20261030, 20261025)`). R18 no lo prohíbe.
- **O6.** Con `otra_del_mes`, si la del mes aparece entre la previa y el commit, el aviso `otra_del_mes` que se
  calcula dentro se descarta (`_avisos`, `:380`). La respuesta sale sin él.

## Propuesta de automejora

Ninguna para el protocolo. Para la spec, si el humano acepta D1, D2 o D4 como residuo, que R17, R28 y R13 lo digan
explícitamente. Así la desviación deja de vivir solo en el informe del implementer.
