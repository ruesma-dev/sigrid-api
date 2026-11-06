<!-- progress/spec_F-008_enmienda1.md -->
# F-008 · Enmienda 1 de la spec (v3.1 → v3.2), 2026-11-06

Autor: spec-author. Rama `feature/F-008-registrar-factura`. Origen: G1 (`FR26/11425`), donde la línea `MA9999` salió con
`0444.CDSB37` por el mapeo `MA9999`→`MA99`. Las decisiones D1-D5 están en `design.md` §9. **Ajuste del humano (mismo día):**
el forzado pasa a ser **por empresa** (`"<emp>:<producto>"`) y vive en App Settings nuevas. Solo spec, sin código.

## Requisitos que cambian

- **R23**: en FR, cada línea lleva **o** `producto` (+`partida?`, `paride?`, `unidad?`) **o** `cuenta` + `analitica` (+`unidad?`).
  Dan 400 sin `codigo`: los dos juegos a la vez (ambigua), un juego incompleto, `partida`/`paride` sin producto, o ninguno.
- **R25**: la naturaleza sale por R49-R50. **R26-R27**: valen también para la línea FR con `cuenta`. **R28**: la elección la
  decide la línea, no la serie.
- **R32, R17, R38**: el fondo no cambia; los detalles (`<cod>_NN`, las columnas copiadas, los valores de `consii`) pasan a
  `design.md` §6 para caber en el tope.
- **R47**: de F-009 solo cambia la naturaleza de las sin vincular. F-007 y F-016 siguen sin editarse.
- **R48**: añade `contrato_albaranes.md` (H34), con aviso previo a `albaranes`.

## Requisitos nuevos

- **R49**: si hay clave `<emp>:<producto>` para la empresa de la obra y ese producto, manda la naturaleza forzada. Si no, la
  ficha (`pro.natide`). Valen la validez y la analítica de F-009 R13b y R15. Aplica a FR y a `sigrid/albaran`.
- **R50**: un producto no forzado cuya ficha no trae naturaleza o trae una no válida da `naturaleza_no_valida` (mismo código).
  El mensaje dice si venía del forzado o de la ficha.
- **R51**: proforma y `albaran-directo` no cambian. **R52**: FR con cuenta, como FRGG. **R53**: el forzado da lo del mapeo viejo.
- **R54**: App Settings nuevas `SIGRID_FACTURA_NATURALEZA_FORZADA` y `SIGRID_ALBARAN_NATURALEZA_FORZADA` (`{}` por defecto).
  Se dejan de leer las dos `_NATURALEZA_POR_PRODUCTO`: si siguen en Azure, se ignoran y la app arranca.
  Validación: una clave mal formada (emp no entero o ≤ 0, producto vacío, con espacios o de más de 24), un valor vacío o claves
  repetidas tras normalizar (`01:` = `1:`) hacen fallar `Settings`.

## Por qué App Settings nuevas (se valida la propuesta del líder)

- Reutilizar los nombres viejos con el formato nuevo **rompe el arranque**: el valor cargado hoy (`"MA9999"`) no pasaría la
  validación.
- Aceptar los dos formatos mezclaría en silencio forzados globales y por empresa.
- Con nombres nuevos y `extra="ignore"` en `Settings`, desplegar es seguro y la ficha manda desde el primer minuto. T34 solo
  borra las viejas y carga las excepciones reales. Queda una sola vía de marcha atrás sin redesplegar: cargar
  `{"1:MA9999": "MA99"}`.
- El mapa de proformas no se toca (P23): sigue con claves por producto.

## Diseño (resumen)

- **Una sola regla** en `albaran_compra_statements.py`:
  - una lectura nueva, `L15D_NATURALEZA_DE_FICHA` (`pro` LEFT JOIN `auxpronat`, `p.ide IN (?)`);
  - una función pura, `naturalezas_elegidas`;
  - el validador `parse_naturaleza_forzada` en `config/settings.py`.
- **Quién la usa**: `_Catalogo._leer_naturalezas` en albaranes, con `PerfilAlta.naturaleza_de_ficha` (solo `PERFIL_ALBARAN`), y
  `_lecturas_fr` en facturas. En FR, el resolvedor se elige por línea. Sin escrituras nuevas ni tocar `infrastructure/security/`.

## Tareas (`tasks.md`)

T26 Settings · T27 lectura y función pura · T28 albaranes · T29 facturas (ficha) · T30 modelo FR con cuenta · T31 resolvedor
por línea · T32 mutación · T33 documentación (con commit en `azure-apps`; el contrato de albaranes, después del aviso) ·
T34 MANUAL (humano): despliegue, previas, borrar las viejas y cargar excepciones, con autorización · T35 reviewer ·
T36 `init.sh`.

## Medición (solo lectura, `sql/read` de la API desplegada)

- **M76: desplegar ya pasa `MA9999` a la ficha** (`MA1501`, CDMA15) en la empresa 1, en facturas y en albaranes. De las 59
  obras con albaranes de 2026, 57 tienen `<obra>.CDSB37` y 57 `<obra>.CDMA15`, y ninguna tiene la primera sin la segunda: no
  aparece ningún `analitica_no_resuelta` nuevo. Las empresas 31 y 34 no tienen albaranes en 2026.
- **M77**: la empresa 34 no tiene FR de 2026 con obra. Su ficha de `SM370001` es `SM08`, que lleva la misma cuenta
  (`6060000000`) que `SM37` y `MOD.CDSM08`. (M75 es la del líder que venía en el encargo.)

## Riesgos

- **Desplegar cambia el resultado** en producción, también en albaranes, que escriben con la llave abierta. Hay que avisar a
  `albaranes` antes de desplegar (T34) y antes de tocar su contrato (T33).
- **H34 se invierte**: ahora manda el maestro, y una ficha mal puesta imputa mal sin aviso. Lo mitigan el forzado y «Comprobar».
- El riesgo de «el mapa es global» **desaparece** con el forzado por empresa (antes, `SM370001`→`SM37` habría caído también
  en la 34).
- Las pruebas de F-009 con producto no forzado tendrán dobles que respondan a L15D, y las que leen
  `sigrid_albaran_naturaleza_por_producto` cambian de campo. Se ajustan, se listan y no se borran.
- G1 (`FR26/11425`) sigue con `0444.CDSB37`: la corrige Administración en el escritorio, no esta enmienda.

## Preguntas abiertas para el humano

- **P22 · `albaran-directo`**: no usa ningún mapeo (copia la última `dcapro`) y nadie la llama. **Recomendada:** no tocarla.
- **P23 · proformas**: comparten `_Catalogo`. **Recomendada:** dejarlas como hoy y decidir en una enmienda de F-007.
- **D3 · código**: confirmar que se reutiliza `naturaleza_no_valida` en vez de crear `producto_sin_naturaleza`.
