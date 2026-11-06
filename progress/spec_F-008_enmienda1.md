<!-- progress/spec_F-008_enmienda1.md -->
# F-008 · Enmienda 1 de la spec (v3.1 → v3.2), 2026-11-06

Autor: spec-author. Rama `feature/F-008-registrar-factura` (avanzada a `dev` `09339e8` antes de editar). Origen: hallazgo de
financiero sobre G1 (`FR26/11425`): la línea sin origen `MA9999` salió con `0444.CDSB37` porque la naturaleza venía solo del
mapeo (`MA9999`→`MA99`). Decisiones D1-D5 del humano en `design.md` §9. Solo spec: no hay código.

## Requisitos que cambian

- **R23**: en FR, una línea lleva **o** `producto` (+`partida?`, `paride?`, `unidad?`) **o** `cuenta` + `analitica` (+`unidad?`).
  Las dos a la vez (ambigua), un juego incompleto, `partida`/`paride` sin producto o ninguno: 400 sin `codigo`. FRGG igual.
- **R25**: la naturaleza de la FR con producto sale por R49-R50 (antes, solo del mapeo).
- **R26-R27**: valen también para la línea FR con `cuenta` (mismas validaciones y escritura, `proide`/`paride`/`natide` 0).
- **R28**: «un solo camino»; lo que decide R25 o R26-R27 es la línea, no la serie.
- **R47**: F-009 deja de estar congelada **solo** en la naturaleza de las sin vincular; F-007 y F-016 siguen sin editarse.
- **R48**: añade `contrato_albaranes.md` de F-009 (H34), avisando antes a `albaranes`.
- **R17 y R38**: sin cambio de fondo; las listas de columnas y de valores de `consii` se movieron a `design.md` §6 por el tope.

## Requisitos nuevos

- **R49**: naturaleza = la del mapeo de la ruta si el producto está en él (forzado); si no, `pro.natide` del producto en la
  empresa de la obra, con las mismas reglas de validez y analítica de F-009 R13b y R15. Vale para FR y para `sigrid/albaran`.
- **R50**: fuera del mapeo y sin naturaleza válida en la ficha (0, NULL, sin `auxpronat`, baja, otra empresa, cuenta no única):
  `naturaleza_no_valida`, con mensaje que dice si venía del mapa o de la ficha. **Se reutiliza el código** (decisión del
  spec-author, D3): `albaranes` ya lo clasifica como `error` (configuración o maestro) y uno nuevo obligaría a tocar F-053.
  `analitica_no_resuelta` no cambia de significado.
- **R51**: `sigrid/proforma` y `sigrid/albaran-directo` quedan como están (P22, P23 abiertas).
- **R52**: línea FR con `cuenta` + `analitica`, como la FRGG; convive con producto y orígenes.
- **R53**: regresión: con el mapa cubriendo el producto, mismos resultados que hoy; la ficha ni se lee.

## Diseño (resumen)

Una sola regla, en el módulo de F-009 (`albaran_compra_statements.py`): lectura nueva `L15D_NATURALEZA_DE_FICHA` (`pro` LEFT
JOIN `auxpronat` por `p.ide IN (?)`) y función pura `naturalezas_elegidas`, que usan `_Catalogo._leer_naturalezas` (albaranes,
tras un `PerfilAlta.naturaleza_de_ficha` que solo `PERFIL_ALBARAN` activa) y `_lecturas_fr` (facturas). En FR, el resolvedor
pasa a elegirse por línea. Sin SQL de escritura nuevo, sin tocar `infrastructure/security/`.

## Tareas nuevas (`tasks.md`)

T26 lectura y función pura · T27 albaranes · T28 facturas (ficha) · T29 modelo FR con cuenta · T30 resolvedor por línea ·
T31 mutación · T32 documentación (`azure-apps/sigrid_api.md` con commit allí, `ARCHITECTURE.md`, contrato de albaranes tras el
aviso) · T33 MANUAL del humano tras desplegar (previas y App Settings de mapeo solo con excepciones reales, con autorización) ·
T34 reviewer · T35 `init.sh`.

## Medición hecha (solo lectura, `sql/read` de la API desplegada)

**M76**: de las 59 obras de la empresa 1 con albaranes de 2026, 57 tienen `<obra>.CDSB37` y 57 `<obra>.CDMA15`, y ninguna
tiene la primera sin la segunda: pasar `MA9999` de `MA99` a la ficha (`MA1501`) no añade `analitica_no_resuelta`. Las
empresas 31 y 34 no tienen albaranes en 2026. (M75 es la medición del líder que traía el encargo.)

## Riesgos

- **H34 se invierte**: F-009 eligió el mapeo porque «el maestro tiene mal `MA9999`»; ahora manda el maestro y una ficha mal
  puesta imputa mal sin aviso (mitigación: el forzado del mapa y «Comprobar»).
- **El mapa es global y la ficha, por empresa**: un forzado vale en todas (`SM370001`→`SM37` también en la 34, cuya ficha dice
  `SM08`). Por eso los mapas deben quedarse solo con excepciones reales (T33).
- **Desplegar no cambia nada visible**: los mapas actuales cubren todos los productos de las listas blancas; el cambio real
  llega en T33, al quitar entradas (hoy `MA9999`→`MA99` sigue forzando CDSB37 en facturas **y en albaranes**).
- **Pruebas de F-009** con producto fuera del mapa: sus dobles tendrán que responder a L15D; se ajustan, no se borran.
- **Contrato con albaranes congelado** (F-053 usa `8a6ecab`): no cambia ningún código ni campo, pero sí la regla H34; el líder
  avisa a la sesión de `albaranes` antes de T32.
- **G1 ya grabada** (`FR26/11425`) sigue con `0444.CDSB37`: la corrige Administración en el escritorio, no esta enmienda.

## Preguntas abiertas para el humano

- **P22 · `albaran-directo`.** El encargo la incluye, pero **no usa ningún mapeo**: copia `natide`/`cueide` de la última
  `dcapro` del producto y no calcula analítica; nadie la llama (obsoleta según `azure-apps/sigrid_api.md` §10). Aplicarle D1
  es rediseñar una ruta legado. **Recomendada:** no tocarla (así está escrita la spec, R51); si se quiere, feature aparte.
- **P23 · proformas (F-007).** Comparten el mismo `_Catalogo` y D1 no las nombra. **Recomendada:** dejarlas igual aquí y
  decidir en una enmienda de F-007, avisando a `proformas`.
- **D3 · código**: confirmar que vale reutilizar `naturaleza_no_valida` (alternativa descartada: `producto_sin_naturaleza`).
