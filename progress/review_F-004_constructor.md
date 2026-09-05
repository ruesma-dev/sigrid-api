<!-- progress/review_F-004_constructor.md -->
# F-004 · Review ACOTADO: constructor, guardia del documento y settings

Revisión completa (pasada 1), encargo **acotado** sobre `8a37b21` (código medido en `87098d6`). NO cubre caso de uso, ruta, modelos ni papeleo (otros dos reviewers). `init.sh` no se ejecuta aquí por encargo expreso: lo corre el líder.

**Veredicto (constructor / guardia / settings): APROBADO**
**Rigor:** `critico`. En mi ámbito: fase RED, SQL constante, control negativo. Cobertura y mutación las mide el líder sobre la feature entera.
**Ejecutado:** `pytest -k f004` → **175 passed / 1,55 s**; `pytest -k "f003 or database_reference"` → **921 passed** (R5).

## 1 · ¿El gráfico queda localizable en Sigrid? [x]

Verificado **ejecutando** el constructor, no leyendo el informe. Salida real (`emp=1, gratipide=35, res='PARTE FIRMADO'`):
- E4 documental `res=''`, `gratipide=0`, `vin=3`, `ima=bytes`; E5 negocio `res`/`gratipide` de la petición, `vin=3`, `ima=None`.
- `documental['cod'] is negocio['cod']` → **True**, y `emp` → **True**: `cod` se genera una vez (l. 232) y la closure `fila()` lo cierra; es imposible que difieran. Es la propiedad de la que depende todo (`explore_..._relacion_gra.md` §Respuesta 4).
- Las **29 columnas** de `GRA_COLUMNAS` (l. 26-31) coinciden una a una y en orden con `explore_F-004_mediciones.md` §2.1, y las constantes con §2.3 (`cla`/`texrev`/`salusu`/`saltex`/`guid`=`''`; `estcon`/`tipocu`/`numrev`/`salfec`/`salhor`/`mntide`/`graant`/`anx`/`ori`/`tip`=0; `tex`/`cam`/`pul`=NULL; `nom`==`nomori`).
- E6: las 7 columnas reales, `cla=0`, `feclee=0`, `fecalt=0`; `pos` de L4 = `ISNULL(MAX(pos),0)+64`. `rcg.gra` recibe el `ide` de **negocio** (`attach_concepto_grafico_use_case.py:456-457`, el reservado por E2 sobre `dbo.gra`), nunca el documental de E1.
- L5, L6 y E7 cruzan por `(emp, cod)`, jamás por `ide` (l. 122-133, 147-151).

Cero desviaciones de la tabla de columnas del `design.md`.

## 2 · SQL constante y seguro (R18-R20) [x]

Volcadas las 15 sentencias: **todos** los valores por `?`; único identificador no literal `[ruesma_rep]`, por `IdentifierGuard` (`ruesma_rep];DROP` → `IdentifierValidationError`; el regex no admite `]`, no hay escape que forzar). Ninguna `UPDATE/DELETE/MERGE/DDL`, ningún `;`.
Control negativo ejecutado por mí: con `allowed=['ruesma']` el `DatabaseReferenceGuard` rechaza **exactamente 5** (L5, L6, E1, E4, E7 documental) y `extract_database_references` da `[]` o `['ruesma_rep']`, nunca otra base. La autovalidación de `__init__` (l. 156-161) corre antes de abrir conexión.
`git diff dev...HEAD` sobre `sql_write_guard.py`, `sql_query_guard.py`, `database_reference_guard.py` e `identifier_guard.py` → **vacío**.

## 3 · `cod` y la hora de Madrid (R13) [x] — con recomendación

`construir_cod` da `202609051230451101.aechevarria`: sello + `int(sha[:8],16)%10000` con ceros a la izquierda + `.` + `usu`; reproducible y **el mismo en cada reintento**.
**La regla de horario de verano es correcta**, verificada con dos controles independientes míos: (a) `_ultimo_domingo` contra `calendar.monthcalendar` en seis meses de **1996-2040** → 0 discrepancias; (b) los cuatro bordes de 2025, 2026 y 2027 dan UTC+1 a las 00:59 UTC y UTC+2 a las 01:00 UTC del último domingo de marzo, y el inverso en octubre. Los tests parametrizados (l. 303-322) cubren los cuatro bordes de 2026 más el cruce 2027→2028: bien elegidos.
La justificación es real, no una excusa: en este `.venv`, `ZoneInfo("Europe/Madrid")` **falla** («No time zone found with key») y `tzdata` no está instalado.
**Recomendación (no bloqueante, decide el humano):** añadir `tzdata` a `requirements.txt` y usar `ZoneInfo` con este cálculo de *fallback*. Motivo: si la UE deroga el cambio de hora, la regla a mano queda desfasada **en silencio** y ningún test lo detecta; con `tzdata` el cambio llega solo. El daño de ese desfase sería una hora en el sello del `cod` —que Sigrid no interpreta [MEDIDO]— y ±1 día en `gra.fec` entre las 23:00 y la 01:00, que sí es dato visible en el ERP. Es mejora, no defecto: hoy el código es correcto y probado, y la spec no autorizaba dependencias nuevas.

## 4 · Guardia del fichero (R8) [x]

13 casos límite ejecutados. Base64 con saltos de línea, con espacio inicial, `urlsafe` o sólo relleno → `ValueError` y **no** `ConceptoGraficoError`, a propósito: R1 los quiere como 400 «Solicitud invalida» y R3 no define código para ellos. Orden correcto: tope sobre la longitud del base64 (`ceil(max*4/3)+4`, l. 64) **antes** de decodificar y sobre los bytes después; `AA==` → `fichero_vacio`; el tope exacto entra y un byte más se rechaza; firma en medio del fichero rechazada; **lista de firmas vacía rechaza todo** y una firma `''` en la lista no abre la puerta (`crudo and ...`, l. 114); `sha256` siempre en Python y comparado tras la firma. Listas de `contip` y `gratipide` vacías rechazan todo.

## 5 · Settings (R4, R5) [x]

Los siete campos con el defecto exacto de R4, todos cerrados. `parse_int_list` acepta JSON y CSV y **falla al arrancar** ante lo que no entiende en vez de degradar a lista parcial: decisión correcta y razonada en el código. `ALLOWED_WRITE_DATABASES` no aparece en el diff —ni valor ni uso cambian— y los 921 tests de F-003 siguen verdes.

## 6 · C3, convenciones y fase RED [x]

- Capas: el guardia (infrastructure) importa sólo `domain`. El constructor vive en `application` e importa dos guardias de `infrastructure`: es el patrón **ya establecido en `dev`** (`execute_sql_command_use_case` → `SqlWriteGuard`; `execute_sql_query_use_case` → `SqlQueryGuard`), no una desviación nueva. `domain` sigue sin infraestructura.
- Convenciones: primera línea con ruta en los cinco ficheros, español, sin secretos, sin prints. `ruff` limpio en lo nuevo; los 2 avisos `BLE001` de `config/settings.py` son **preexistentes en `dev`** (comprobado pasando `git show dev:config/settings.py` por ruff).
- **Fase RED verificada estructuralmente**, no por su relato: en `d714964` (T3), `4f21c73` (T7) y `15ce980` (T9) entran los tests **solos**, y `git cat-file -e` confirma que ni el guardia ni el constructor existían en esos commits: era imposible que pasaran.

## Observaciones menores (ninguna bloquea)

1. `document_write_guard.py:113` compara las firmas en `latin-1`: las entradas no ASCII de `_TIPOS_POR_FIRMA` (JPEG, PNG, TIFF) sólo se alcanzan desde los tests, porque por App Setting no hay forma cómoda de escribir `\xff\xd8\xff`. El defecto `%PDF-` es ASCII y funciona; si algún día se admite JPEG habrá que aceptar las firmas en hexadecimal.
2. `DocumentoValidado.bytes` (l. 40) sombrea el builtin `bytes` como nombre de campo. Cosmético.
3. `ConceptoGraficoStatements` no pasa `database` por `IdentifierGuard`, sólo `documental`. No es agujero: `database` nunca se interpola en el SQL y `_validar_bases` lo contrasta contra `ALLOWED_WRITE_DATABASES` **antes** de construir las sentencias (`attach_concepto_grafico_use_case.py:97`).

## Automejora (propuesta, no aplicada)

A `.claude/agents/reviewer.md`: **cuando el implementer sustituya una biblioteca estándar por una regla escrita a mano** (aquí `zoneinfo`), el reviewer debe **reproducir esa regla con un control independiente** y dejarlo escrito, en vez de leerla y darla por buena. Aquí costó dos minutos y es lo que separa «parece correcta» de «verificada 1996-2040».
