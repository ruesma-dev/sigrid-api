<!-- progress/review_F-006_docs.md -->
Revisión completa (pasada 1), acotada a C3 bis y documentación · rama `feature/F-006-alta-parte-reclamacion` en HEAD `22ba2a5`

# Review F-006 · bloque C3 bis + documentación (R23)

**Nivel de rigor:** `critico` (declarado). Este encargo solo cubre C3 bis y R23;
`init.sh`, la suite, cobertura y mutación los revisan otros revisores en paralelo
(**N/A aquí por reparto del encargo**, no se ejecutaron).

## C3 bis — Documentos que entran de fuera

- [x] **Cabecera con origen y fecha.** `postventa_pasos_crear_parte.md` l.4-5: `PASOS CREAR PARTE.docx`, 2026-09-24, convertido con `markitdown`. `postventa_manual_sigrid.md` l.4-5: `Manual Sigrid Postventa con Portal.pdf`, 2021-01-17, `markitdown`. Ambos siguen el «Caso 1» de `docs/referencia/README.md`. El README (índice) no es documento externo: se actualizó con las dos filas.
- [x] **Originales fuera del árbol y del historial.**
  `git log --all --diff-filter=A --name-only` filtrado por `\.(pdf|docx?|xlsx?|pptx?|odt|rtf|png|jpe?g|gif|bmp|emf|wmf)$` → **0 resultados** (exit 1). `find` en el árbol (sin `.git`/`.venv`) de `*.pdf|*.doc*|*.xls*|*.ppt*|*.odt` → vacío. `git status --ignored` → ningún ofimático ignorado. Imágenes embebidas: `data:image/...;base64,<datos>` → 0 en el árbol y 0 en el historial de los ficheros (las capturas quedaron como `data:image/png;base64...` literal, sin datos).
- [x] **Barrido de datos sensibles ejecutado por el reviewer** (tabla abajo). Sin correos, IPs, GUID, teléfonos, credenciales, tokens ni nombres de personas.
- [x] **Lo redactado, declarado en cabecera.** Manual l.7-9: teléfono, fax, teléfono comercial y correo del fabricante → `[REDACTADO]` (l.28-32 lo confirman). Historial: `git log --all -p` de los ficheros → las únicas líneas `Tel.:/Fax:/Mail:` que entraron ya venían `[REDACTADO]`; nunca hubo el dato en claro. El Word declara que las capturas (nombres de propietarios) **no se transcriben** (l.7-10). También consta la cláusula de copyright y la decisión del humano de incorporarlo.

### Barrido: ficheros, patrones y resultado

Ficheros: `docs/referencia/{postventa_pasos_crear_parte,postventa_manual_sigrid,README}.md`,
`specs/F-006-alta-parte-reclamacion/{requirements,design,tasks}.md`,
`progress/explore_F-006_modelo_parte.md`, `progress/impl_F-006.md`, `progress/mutacion_F-006.md`.
Además, el diff de `azure-apps` 7df52e9 (P1-P3, P5-P6, dominios Azure) y las líneas añadidas en todo el historial de esos ficheros (P1-P4, P8, `Tel./Fax:/Mail:`).

| # | Patrón (ERE / ripgrep) | Aciertos | Dictamen |
|---|---|---|---|
| P1 correo | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` | 0 | limpio |
| P2 IPv4 | `\b([0-9]{1,3}\.){3}[0-9]{1,3}\b` | 0 | limpio |
| P3 GUID | `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}` | 0 | limpio |
| P4 teléfono | `(\+34[ -]?)?\b[6789][0-9]{2}[ .-]?[0-9]{2,3}[ .-]?[0-9]{2,3}...` | 0 | limpio |
| P5 credencial | `password\|pwd\|contraseña\|secret(o)?\|api_key\|function_key\|client_secret\|connection string\|AccountKey\|SharedAccess\|Bearer\|x-functions-key\|code=` | 5 | falsos positivos: manual l.318/384 «contraseña» (texto funcional del portal); `requirements.md` l.16 nombre de la cabecera `x-functions-key`; `tasks.md` l.4 nombre de variable `SIGRID_API_FUNCTION_KEY`; `explore` l.7 «Sin secretos». Ningún valor |
| P6 token/base64 | `[A-Za-z0-9+/=_-]{32,}` | 67 | todos rutas, nombres de App Settings, códigos de error o texto OCR repetido del manual (l.701/703). Ningún token |
| P7 hex largo | `\b[0-9a-f]{24,}\b` | 3 | SHAs de git (impl l.148, mutacion l.8/31) |
| P8 imagen embebida | `data:image/[a-z]+;base64,[A-Za-z0-9+/]{10,}` | 0 | limpio |
| P9 DNI/NIE/CIF | `\b([0-9]{8}[A-Z]\|[XYZ][0-9]{7}[A-Z]\|[ABCDEFGHJNPQRSUVW][0-9]{7}[0-9A-J])\b` | 0 | limpio |
| P10 IBAN/tarjeta | `\bES[0-9]{2} ?[0-9]{4}\|\b[0-9]{4}[ -][0-9]{4}[ -][0-9]{4}[ -][0-9]{4}\b` | 0 | limpio |
| P11 URL | `https?://[^ )>]+` | 1 | manual l.305 `https://postventa.ruesma.com/`: portal **público** de propietarios, citado por el fabricante. No es IP ni recurso interno |
| P12 Azure/corp | `ruesma\.(es\|com)\|\.database\.windows\.net\|\.azurewebsites\.net\|\.blob\.core\|subscription\|tenant` | 1 | el mismo P11 |
| P13 nombres de pila | ripgrep, ~110 nombres españoles frecuentes con variantes acentuadas | 1 | manual l.27 «María Tubau 4, 3º»: **calle** del domicilio social del fabricante, no una persona |
| P14 apellidos | ~110 apellidos españoles frecuentes | 1 | el mismo «Tubau» |
| P15 Nombre Apellido | `\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\b` (y variante de 3 palabras) | ~230 | revisados todos: rótulos de Sigrid («Portal Postventa», «Dirección Facultativa», «Datos Fiscales»…), ningún nombre de persona |
| P16 logins/ide | `pgris\|pablo\|"usu":"…"\|login…` y `(ide\|per\|pro)…[=:][0-9]{3,}` | 12 | `usu:"prueba"` (usuario de prueba acordado); `pgris` solo en rutas temporales locales del informe de mutación (l.32-39, las escribe la herramienta; usuario de Windows, no credencial). Ningún `ide` de propietario |

Nota de método: con `grep -E` del Git Bash el patrón P13 **no casó «María»** (locale sin UTF-8); se repitió con ripgrep, que sí lo casa. Los resultados de P13-P15 son los de ripgrep.

`explore_F-006_modelo_parte.md` l.5-7 declara la regla («propietarios y personas por `ide`, nunca por nombre; el login, solo por su longitud») y el barrido la confirma.

## Documentación (R23)

- [x] **`azure-apps` 7df52e9 solo toca `sigrid_api.md`** (`git show --stat`: 1 fichero, +112/−3).
- [x] **`.env` de `azure-apps` sin trackear**: `git ls-files | grep .env` vacío; `git check-ignore -v .env` → `.gitignore:15`; `git log --all -- .env` vacío (nunca entró). Árbol de `azure-apps` limpio.
- [x] **Cobertura de secciones de R23:** §1.1 (árbol), §4 (4 App Settings) y §4.1 (valores en `dev`: «aún sin desplegar»), §7.1 (nota de lote), §7.2 punto 7, §7.5 (serie dentro de la transacción), §7.6 (fila nueva), §8 (tabla) y §8.9 nueva, §9.2 (`tip` 707/708), §10 (`postventa-incidencias` F-040). Todas presentes.
- [x] **Ruta:** `POST /api/sigrid/partes-reclamacion` = `function_app.py` `@app.route(route="sigrid/partes-reclamacion", methods=["POST"])`.
- [x] **Petición y defectos** contra `parte_reclamacion_models.py`: `extra="forbid"` en los tres modelos; `obra`/`usu` ≤24; `partes` ≥1 (tope en el caso de uso, l.199); `commit=False`; `referencia_externa` 1-80; `unidad_postventa` ≤24; `descripcion` 1-128; `descripcion_larga` → `rcp.tex` con defecto la descripción (`statements` `"tex": descripcion_larga or descripcion`); `tipo="0002"` (PRIMER LISTADO POSTVENTA según `explore` l.150); `clase` opcional → `rcpide 0`; `oficio` ≤24 y en `obrofc` (use case l.476); `ubicacion` ≤48; `forma_comunicacion` `Literal[0,1]=1`; `intervinientes` ≤10 `{oficio, proveedor?, causante=False}`. Coincide.
- [x] **Respuesta:** `{ok, committed, dry_run, database, obra{ide,cod,emp}, resumen{5 contadores}, avisos, partes[]}` y `ResultadoParte{indice, referencia_externa, estado, ide, cod, motivo, filas, avisos}`; los 5 estados de `EstadoParte`; `committed = resumen.creados > 0` (l.251); preview con `cod`/`ide` provisionales consecutivos (`_NumeracionProvisional`). Coincide.
- [x] **Códigos:** los 7 de lote = `CODIGOS_DE_LOTE`; los 14 de parte + `presupuesto_de_tiempo_agotado` como `no_procesado` = `CODIGOS_DE_PARTE` (15). Lectura truncada → `ValueError` → 400 en la ruta; `ValidationError` → «Solicitud invalida.»; resto → 500. Coincide.
- [x] **App Settings y defectos** contra `config/settings.py`: `WRITE_ENABLED=False`, `MAX_PARTES=50`, `PREFIJOS_REFERENCIA=[]` (lista vacía rechaza todo, también en dry-run: `_planificar` no depende de `commit`), `PRESUPUESTO_SEGUNDOS=150`. La doble llave (`SIGRID_DOMAIN_WRITE_ENABLED` + credenciales) = `_exigir_llaves_de_escritura`; `ALLOWED_WRITE_DATABASES` vacía no abre = `_validar_base`. `local.settings.sample.json` lleva las cuatro. Coincide.
- [x] **Idempotencia por `RCPCLI` con `PVI-`:** `COD_REFERENCIA_EXTERNA="RCPCLI"`, búsqueda por `conext.cod/valt` + `tip 708` + `emp`; misma UPV → `idempotente`, si no → `referencia_en_conflicto`; en commit dentro de la transacción bajo `SIGRID_REFEXT_708`. Prefijo sensible a mayúsculas (`startswith`) y comparación de referencias CI (`casefold`): así lo dice el doc.
- [x] **Qué escribe y qué no:** `con`, `rcp` (cliide/recide = `ISNULL(upv.cliide/peride,0)`), `rcpint` `pos 0`, `conext`, `log` `ope 1`; relectura E14 antes del COMMIT; orden de los 7 applocks idéntico a `APPLOCKS`; `UPDLOCK, HOLDLOCK` en E2-E7; patrón `LIKE` con 4 `[0-9]`; `numeracion_agotada` pasado 9999; `rcp.pos` `MAX+64`; reintentos con `domain_write_max_retries`. «No hace» coincide con «Fuera de alcance» de la spec.
- [x] **Consumidor `postventa-incidencias` F-040** en §10, marcado «implementado, pendiente de despliegue y de la prueba manual». Correcto a fecha de hoy.
- [x] **`docs/ARCHITECTURE.md`:** ruta, `parte_reclamacion_models` y `create_partes_reclamacion_use_case` + `parte_reclamacion_statements`.
- [x] **Mapa de rutas de `CLAUDE.md`:** `sigrid/partes-reclamacion` añadida.

## Observaciones (no bloquean)

1. `sigrid_api.md` §8.9, idempotencia: el código también da `referencia_en_conflicto` si el parte coincidente **no tiene fila `rcp`** (`upvide` NULL, `_resolver_referencia` l.570). El doc solo dice «de otra UPV o con más de uno». Hay 1.512 partes SAT sin `rcp` (`explore` l.48), aunque ninguno con referencia `PVI-`. Conviene añadir «o sin ficha `rcp`» cuando se toque el doc.
2. §7.2 punto 7: se podría añadir que `base_de_datos_no_permitida` salta **también en dry-run** (`_validar_base` corre siempre), como ya se dice de los prefijos.
3. En la raíz del repo hay un fichero **sin seguimiento y vacío**, `` `0`].{t `` (0 bytes, 2026-09-24 12:31), restos de un comando mal escapado. No es de F-006 ni está en ningún commit; que lo borre el humano o el líder.

## Automejora (propuesta, no aplicada)

C3 bis pide un barrido «con los patrones usados» pero no dice **dónde** se ejecuta. Con el `grep -E` de Git Bash en Windows las clases con acentos fallan en silencio (aquí, «María»). Propuesta para `CHECKPOINTS.md` C3 bis y para `arnes-base`: «el barrido de nombres y de texto acentuado se hace con ripgrep (herramienta Grep), no con `grep -E` de Git Bash».

VEREDICTO PARCIAL: APROBADO
