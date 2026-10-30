<!-- specs/F-008-registrar-factura/design.md -->
# F-008 · Diseño: `POST /api/sigrid/factura`

Requisitos: [`requirements.md`](requirements.md). Mediciones: [`explore_F-008.md`](../../progress/explore_F-008.md) (M52-M60).

## 1. Respuesta corta a lo que pedía la spec

| Pregunta | Respuesta (medida) |
|---|---|
| ¿Qué escribe Sigrid al registrar? | En REC: `con` tip 15 (`est` 1), `dcf` (`cla` 1001, serie `FR<aa>/`), `dcfpro` ×N, `dcfrec` ×0-1, `con` tip 25 + `pag` ×M, `consii`, `log` (M52, M53, M58) |
| ¿Qué arrastra en el alta? | Albarán: `dcaprodes`, `dcapro.canfac`, `dca.estfac/fecfac/horfac/antestfac`, `con.est` 10 FAC; contrato: `ctrpro.canfac`, `ctr.estfac` (M54) |
| ¿Y la contabilidad? | **No está en el alta.** REC y COM: 0 asientos y 0 `regiva`; 100 % desde CON. La hace «Contabilizar» (M53, M55). Vencimientos, cartera y SII **sí** están en el alta (M58) |
| ¿Stock? | Ninguno: octubre, 0 `mov` de factura (M53) |
| ¿Qué recalcula el endpoint? | Totales de cabecera, retención, vencimientos, `canfac`, estados. Las líneas se **copian** del albarán |
| ¿Qué deja a Sigrid? | Comprobar, contabilizar (`asi`, `apu`, `regiva`, `regirp`, `consii.regivaide`), firmas, aprobación de pago, remesa |
| ¿Cabe en este microservicio? | **El alta, sí**: es el mismo tipo de escritura que el albarán. **La contabilidad, no**: se propone dejarla fuera, sin alternativa aquí (§7, P1) |

## 2. Encaje en la arquitectura

Mismo patrón que `sigrid/proforma`: ruta en `function_app.py`, modelo Pydantic, caso de uso que valida con lecturas y ejecuta en
`run_in_write_transaction` un trabajo reentrante, y un módulo puro de sentencias y filas. **No hereda** de
`CreateAlbaranCompraUseCase`: comparte funciones sueltas de `albaran_compra_statements`, no el flujo, y no toca `dca` al nacer.
Es «cierre» de lo que F-007/F-009 abren: registra el documento que factura esos albaranes.

Flujo que deja: `proformas`/albaranes registran → Administración **contabiliza el albarán** → `facturas` concilia y un humano aprueba
→ `sigrid/factura` da de alta en REC → Administración comprueba y contabiliza en el escritorio.

## 3. Ficheros a crear

| Ruta | Capa | Qué |
|---|---|---|
| `domain/models/factura_models.py` | domain | `FacturaRequest`, `FacturaResultado`, `FacturaError(ValueError)` con `codigo` y `details` |
| `application/use_cases/factura_statements.py` | application | Lecturas `Lnn`, escrituras, listas blancas y constructores puros de filas |
| `application/use_cases/factura_vencimiento.py` | application | Regla pura de vencimientos (§6) |
| `application/use_cases/create_factura_use_case.py` | application | `CreateFacturaUseCase.run(request)` |
| `specs/F-008-registrar-factura/verificacion_manual.md` | spec | Pasos MANUAL del humano (T17-T19) |
| `tests/test_f008_*.py`, `tests/f008_dobles.py` | tests | `models`, `route`, `settings`, `statements`, `vencimiento`, `use_case`, `transaccion` |

## 4. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `function_app.py` | Ruta `sigrid/factura`, `_exigir_escritura_de_facturas` y manejo de `FacturaError` |
| `config/settings.py` | `SIGRID_FACTURA_WRITE_ENABLED` (False), `SIGRID_FACTURA_PREFIJOS_REFERENCIA` ([]), `SIGRID_FACTURA_MAX_LINEAS` (500) |
| `.env.example` | Las tres variables, sin valores |
| `docs/ARCHITECTURE.md` | Ruta, modelos y caso de uso |
| `azure-apps/sigrid_api.md` | §4, §7.2, §7.5, §7.6, §8.11 (nueva), §9.5, §10 (mismo trabajo) |
| `CLAUDE.md` (mapa) | La ruta nueva |

## 5. Ficheros que NO se tocan

`infrastructure/security/*` (ni un guardia), `application/use_cases/albaran_compra_statements.py` (se importa, no se edita),
`create_albaran_compra_use_case.py`, `create_proforma_use_case.py`, `create_purchase_albaran_use_case.py`,
`attach_concepto_grafico_use_case.py` y la configuración de `SIGRID_DOCUMENT_ALLOWED_CONTIP` (es P9, ajuste aparte).

`domain/ports/sql_repository.py` e `infrastructure/repositories/sql_server_repository.py` no cambian:
`run_in_write_transaction` ya existe. `colision_de_clave` hereda su reintento de toda `IntegrityError` (§7.5 de `sigrid_api.md`).

## 6. Clases, funciones y reglas

```python
class CreateFacturaUseCase:
    def __init__(self, repository: SqlRepository, settings: Settings) -> None: ...
    def run(self, request: FacturaRequest) -> dict[str, Any]: ...

def calcular_vencimiento(fec: int, dias: int, pagdia: str, pagmes: str) -> int: ...
def vencimiento_retencion(fec: int, token_r: str) -> int: ...
def construir_con_factura(...) -> dict[str, Any]: ...
def construir_dcf(...) -> dict[str, Any]: ...
def construir_dcfpro(dcapro: Mapping[str, Any], *, cuenta_pendiente: int) -> dict[str, Any]: ...
def construir_dcfrec(dcarec: Mapping[str, Any], *, bas: Decimal, cuo: Decimal) -> dict[str, Any]: ...
def construir_pag(...) -> tuple[dict[str, Any], dict[str, Any]]: ...
def construir_consii(...) -> dict[str, Any]: ...
def construir_dcaprodes(...) -> dict[str, Any]: ...
```

**Petición** (`FacturaRequest`, `extra="forbid"`): `database`, `usu` (≤24), `referencia_externa` (1-128), `cif_proveedor`,
`numero_factura` (1-128, a `dcf.entref`), `fecha_factura` (entero `AAAAMMDD`, a `fecdoc`), `albaranes` (1..N códigos únicos),
`total_base`, `total_iva`, `total_factura` (el líquido, con retención), `vencimiento` (opcional, `AAAAMMDD`), `commit` (`false`).

**Cabecera `con`:** `tip` 15, `cod`, `res` = `<entres>. (<entref>)` truncado a 128 (72,4 % de FR26/1 exacto, 87,4 % con ese prefijo), `fec`
= hoy en Madrid (`sellos_del_alta(instante, None, "FR")`), `est` = REC de `conest`, `tiemod`, `tex` vacío.

**Cabecera `dcf`:** lista blanca. Del primer albarán, por `cod` (M57, entre 92,6 % y 100 %): `ent*`, `obride`, `cenide`, `almide`, `empide`,
`dir*1`, `pagide`, `pagtex`, `pagfor`, `efeide`, `eioide`, `ivadif`, `cocide`, `tipgar`, `fecent`, `feclim` y `ban*`. Del proveedor: `cueide`. Del
contrato de los albaranes: `ctride`. Fijas: `cla` 1001, `synckey`. `hor` del sello. Totales de R15. Todo lo demás, el vacío del tipo
(T0 fija la lista contra `sys.columns`, con su nulabilidad). `estfac`, `estser`, `estped`, `docoritip`, `facoriide`, `fecpag`: 0 (M57).

**Línea `dcfpro`:** R14 + `cueide` = `prv.cuepdtide`, `docide`, `ide`, `pos` múltiplo de 64, `docoritip` 14, `docoricod` = `con.cod` del albarán,
`docoriide`, `linoriide`, `canoriori` = `can`, `imporiori` = `tot`, el resto a 0. Con R12 solo hay albaranes de mes, donde esa regla es exacta (M56).

**Vencimiento `cla` 0** (77,3 % de acierto, M58): `calcular_vencimiento`, con el **primer** número de `pagfor`:

1. `d0` = `con.fec` + días.
2. Días de pago: los números de `prv.pagdia`; ninguno (o `0`), 15 y 30.
3. Meses sin pago: los números de `prv.pagmes`.
4. Resultado: la primera fecha ≥ `d0` con un día de pago, en un mes permitido; un día mayor que el mes pasa a su último día.

**`pag`** (M58): `cla` 0: `tot` = `totpag`, y `efeide`, `cueide`, `entide`, `cenide`, `entref`, `ban*` de `dcf`. `cla` 2: `tot` = `cuo`, `retide` = `recide`,
`cueide` = `dcfrec.cueide`, resto igual. `con`: `tip` 25, `cod` `<cod>_NN`, `res` `Pago i de n <res>`, `fec` = `con.fec`, `est` = PDT.

**Marcas (`UPDATE`, siempre por `ide` y con `?`):**

```sql
UPDATE dbo.dcapro SET canfac = canfac + ? WHERE ide = ? AND canfac = 0;     -- exige 1 fila (R24)
UPDATE dbo.dca SET estfac = 1, fecfac = ?, horfac = ?, antestfac = 3 WHERE ide = ? AND estfac = 0;
UPDATE dbo.con SET est = ? WHERE ide = ? AND tip = 14 AND est = ?;          -- CON -> FAC (R25)
UPDATE dbo.ctrpro SET canfac = canfac + ? WHERE ide = ?;
UPDATE dbo.ctr SET estfac = ? WHERE ide = ?;
```

**SQL:** no hay ficheros `NN_*.sql`: el proyecto lleva el SQL parametrizado en constantes de `*_statements.py`, sin esquema nuevo.

## 7. Transacción

Previa: lecturas `L1-Ln` con `execute_read_query` y construcción sin escritura.

Commit: `run_in_write_transaction` con applocks **en este orden fijo**, compatible con los existentes (`_con` antes y `_log` al final):

`SIGRID_REFEXT_15`, `SIGRID_SERIE_15`, `SIGRID_IDE_con`, `SIGRID_IDE_dcfpro`, `SIGRID_IDE_dcaprodes`, `SIGRID_IDE_dcfrec`, `SIGRID_IDE_pag`,
`SIGRID_IDE_consii`, `SIGRID_IDE_log`.

Dentro, reentrante: (1) re-comprobar R31 y R32; (2) releer con `WITH (UPDLOCK, HOLDLOCK)` `dcapro` y `dca` de los orígenes y repetir R10-R11, porque
el escritorio no toma nuestros applocks; (3) reservar `cod` e `ide` (`pag` comparte `ide` con su `con`: de ese rango); (4) `INSERT`s; (5) `UPDATE`s; (6)
relectura R34. El `work` no calcula con estado de intentos anteriores.

## 8. Riesgos y decisiones

- **Vencimiento estimado.** Una de cada cuatro fechas diferirá de la que habría puesto Sigrid. Se acepta porque la `pag` nace en PDT, fuera de
  remesas, y Administración la revisa en «Comprobar»; la respuesta lo avisa. Si V3 dice que el escritorio no deja corregirla, **se para**.
- **Omitir `pag` o `consii`** se descarta como opción por defecto: el 100 % de las facturas con líneas los tiene, y no sabemos si el
  escritorio los regenera. Una factura sin cartera podría contabilizarse sin vencimientos.
- **Exigir el albarán contabilizado (R10)** es más estricto que el escritorio (0,7 % sin asiento): sin él, el asiento de la factura carga en
  4009 lo que nadie abonó. Consecuencia: una proforma de F-007 recién creada (`est` 1 PDT) da `origen_sin_contabilizar`.
- **Clonar la cabecera** se descarta: F-015 midió lo que arrastra una plantilla. Por eso, listas blancas (R23).
- **`dca.idefac` a 0:** 20,7 % de los casos y sin regla (M54); el enlace es por línea.
- **`con.est` del albarán a FAC con la factura en REC** es lo que hace el escritorio (M54), aunque luego se rechace la factura.
- **Reversión:** no hay. Un alta equivocada se anula en el escritorio, nunca con `DELETE`. V4 confirma si revierte las marcas.
- **Carrera con el escritorio:** `UPDLOCK` sobre las líneas y el `UPDATE` condicionado a `canfac` = 0 cierran el doble facturado. Fuera de eso, el
  índice `con_emptipcod` obliga a reintentar por `cod`.
- **Sin punto de no retorno en la previa:** un `previsto` no reserva `cod`; el `cod` del `commit` puede ser otro.
- **Permisos (V1):** F-009 no hizo `UPDATE` de `con`, `dca` ni `dcapro`. Si `user_rw` no los tiene, la primera grabación falla con ROLLBACK. Se comprueba
  antes (T17), preguntando a quien administra Sigrid.
- **Tiempo:** 373 líneas son ~1.500 filas; el corte de 230 s no debería llegar, y `MAX_LINEAS` lo acota. Se mide en la previa.
- **Consumidores:** ninguno cambia (M60). Ver P8 para quién llamará.

## 9. Decisiones del humano

**Aprobadas el 2026-10-30** (PARADA 1, «ok» del humano a la tabla de recomendaciones): P1-P10 = la *Recomendada* de cada una.
P3: sin regla de `pagdia` aportada; vale la del 77 %. P4: se rechaza. P10: la factura del proveedor ya cotejada.

**P1. ¿Alcance: alta en REC sin contabilidad?** *Recomendada:* **sí**. Contabilizar no se hace aquí: 19 familias de cuenta, ISP, deducibilidad y periodos, y un error
ahí es un error fiscal. Alternativa: `blocked` por LÍMITE DE MICROSERVICIO de todo F-008; no aporta seguridad, porque el alta no escribe contabilidad.

**P2. ¿Cartera y SII: escribir `pag` y `consii`?** *Recomendada:* **sí**, con vencimiento estimado y `vencimiento` opcional del llamante. Es lo que hay en el
100 % de los casos. Alternativa: dejarlos a Sigrid, solo si V3 confirma que el escritorio los regenera, lo que exigiría una prueba en el escritorio antes.

**P3. ¿Quién da el vencimiento?** *Recomendada:* **la regla, con corrección humana en «Comprobar»**; `facturas` puede mandarlo si lo lee del PDF. ¿Conoce el
humano la regla de `pagdia` y los meses sin pago? Con ella se pasaría del 77 %.

**P4. ¿Origen sin contabilizar?** *Recomendada:* **rechazar** (`origen_sin_contabilizar`). Alternativa: admitirlo con aviso, como el escritorio. Exige que
Administración contabilice las proformas antes de facturarlas: ¿es ya el flujo real?

**P5. ¿Facturas a origen?** *Recomendada:* **fuera de esta feature** (R12): son el 9,5 %, y `imporiori` no se reproduce (31 %). Feature aparte, con su medición.

**P6. ¿Solo albaranes enteros?** *Recomendada:* **sí** (R13): 99,3 %. Una parcial deja `estfac` ambiguo (62 de 69 en 1).

**P7. ¿Abonos y series?** *Recomendada:* **fuera** (R17): el 2,9 %, con `consii` distinto sin medir. Tampoco `FRGG` (95 % sin albarán), ni facturas sin origen, ni
varias obras o contratos (0,7 % y 0,6 %). ¿Hace falta alguna en esta primera versión?

**P8. ¿Quién llama y con qué control?** *Recomendada:* solo **`facturas`**, tras la aprobación humana de su F-012 y con prefijo propio de referencia (`FAC-<id>`), con
`usu` = quien aprueba. `CUADRA` no basta: `facturas.md` dice que no aprueba nada. ¿Es esa la app, o será otra?

**P9. ¿Adjuntar el PDF?** *Recomendada:* **no en este endpoint**: llamar después a `sigrid/concepto-grafico`, añadiendo `15` a `SIGRID_DOCUMENT_ALLOWED_CONTIP` en su despliegue. Casi
toda factura lleva PDF desde COM (M59).

**P10. ¿Factura de proveedor o del jefe de obra?** La memoria de negocio dice cotejar la del proveedor y registrar la del jefe de obra, y eso se decidió para **proformas** (F-007). *Recomendada:* aquí se registra
la **factura del proveedor** ya cotejada: es la de `numero_factura`. ¿Es correcto? Si no, el contrato de la petición cambia.
