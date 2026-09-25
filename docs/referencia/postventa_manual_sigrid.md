<!-- docs/referencia/postventa_manual_sigrid.md -->
# Manual de Sigrid y Portal Postventa (Professional Software)

> Origen: `Manual Sigrid Postventa con Portal.pdf` (Professional Software, S.A., 81 páginas), OneDrive de Posventa · Fecha del documento: 2021-01-17 (metadatos del PDF)
> Convertido a Markdown el 2026-09-24 con la herramienta MCP `markitdown`.
> El original vive fuera del repositorio.
>
> **Redactado.** Se han sustituido por marcadores el teléfono, el fax, el
> teléfono comercial y el correo de contacto del fabricante (líneas de la
> portada). El detalle está en el original, fuera del repositorio.
>
> El original lleva una cláusula de copyright que prohíbe su reproducción. Se
> incorpora por decisión expresa del humano (2026-09-24), como documentación
> interna de referencia.
>
> **Limitaciones de la conversión:** markitdown extrae solo el texto. Las
> capturas de pantalla no aparecen, y los diagramas de flujo (págs. 32 y 46)
> salen desordenados. Para lo que dependa de una captura, consultar el PDF.
> Lo más usado por este repositorio: «Alta de Partes de Reclamaciones»
> (págs. 47-52) y «Asignación de oficios» (pág. 57).

Sigrid y Portal
Post-venta
Professional Software, S.A.
TODOS LOS DERECHOS RESERVADOS
Distribución y soporte:
María Tubau 4, 3º
28050 Madrid
Tel.: [REDACTADO]
Fax: [REDACTADO]
Información comercial: [REDACTADO]
Web: www.prosoft.es
Mail: [REDACTADO]
La información contenida en este documento podría cambiar sin previo aviso.
No se garantiza su corrección ni su idoneidad para ningún propósito. Este documento no puede
ser reproducido ni transmitido, ni total ni parcialmente, por ningún medio y para ningún pro-
pósito, sin la autorización expresa de los propietarios del Copyright.
Los nombres de los productos mencionados en este documento, han sido utilizados con el
único propósito de su identificación y pueden ser marcas comerciales de sus respectivas com-
pañías.

Guía de usuario Sigrid - Portal Postventa
Índice
INTRODUCCIÓN DE POSTVENTA ................................................................. 4
¿Qué es Sigrid Postventa? .................................................................................... 4
Ventajas de uso .................................................................................................... 5
CONCEPTOS DE POSTVENTA EN SIGRID ..................................................... 6
¿Qué es un concepto?........................................................................................... 6
Tipos de Concepto ................................................................................................ 7
Concepto de Entidades ........................................................................................ 7
Obras ............................................................................................................... 8
Conceptos de Postventa .................................................................................... 10
Documentos de compras ................................................................................... 10
Documento de venta ......................................................................................... 11
PORTAL POSTVENTA ................................................................................. 12
¿Qué es el Portal de Postventa? ......................................................................... 12
Usuarios ............................................................................................................. 13
Tipos de usuarios ............................................................................................. 13
Alta de usuarios ............................................................................................... 14
Menus de Acceso ................................................................................................ 17
Mis Datos ........................................................................................................ 17
Inmuebles ....................................................................................................... 20
Reclamaciones ................................................................................................. 22
Manual Postventa Página 2 de 81

Guía de usuario Sigrid - Portal Postventa
GUÍA DE POSTVENTA ................................................................................ 23
1. Intervinientes de la postventa ...................................................................... 24
Asignación del equipo de Postventa de la empresa ............................................... 24
Oficios y proveedores intervinientes en obra ........................................................ 27
Propietarios ..................................................................................................... 30
2. Contabilidad de Postventa y control de costes .............................................. 31
3. Inmuebles, propietarios y plazos de garantía................................................ 32
Alta Unidad Post-venta ..................................................................................... 35
Estableces Tipologías ........................................................................................ 39
Fechas relevantes ............................................................................................ 43
Notificar alta de usuarios en el portal .................................................................. 45
4. Cobertura del Servicio ................................................................................... 46
Alta de Partes de Reclamaciones ........................................................................ 47
Diagnóstico ..................................................................................................... 53
Asignación de oficios ........................................................................................ 57
Creación de Tareas ........................................................................................... 58
5. Método de seguimiento de reclamaciones ..................................................... 65
Diagnóstico ..................................................................................................... 65
Preparación de Trabajos .................................................................................... 77
Reparación ...................................................................................................... 81
Manual Postventa Página 3 de 81

Guía de usuario Sigrid – Portal Postventa
Introducción de Postventa
¿Qué es Sigrid Postventa?
La Ley 38/1999, de 5 de noviembre, de Ordenación de la Edificación en su artículo 17
Responsabilidad civil de los agentes que intervienen en el proceso de la edificación establece:
“1. Sin perjuicio de sus responsabilidades contractuales, las personas físicas o jurídicas que
intervienen en el proceso de la edificación responderán frente a los propietarios y los terceros
adquirentes de los edificios o parte de los mismos, en el caso de que sean objeto de división,
de los siguientes daños materiales ocasionados en el edificio dentro de los plazos indicados,
contados desde la fecha de recepción de la obra, sin reservas o desde la subsanación de éstas:
a) Durante diez años, de los daños materiales causados en el edificio por vicios o defectos que
afecten a la cimentación, los soportes, las vigas, los forjados, los muros de carga u otros ele-
mentos estructurales, y que comprometan directamente la resistencia mecánica y la estabilidad
del edificio.
b) Durante tres años, de los daños materiales causados en el edificio por vicios o defectos de
los elementos constructivos o de las instalaciones que ocasionen el incumplimiento de los re-
quisitos de habitabilidad del apartado 1, letra c), del artículo 3.
El constructor también responderá de los daños materiales por vicios o defectos de ejecución
que afecten a elementos de terminación o acabado de las obras dentro del plazo de un año…”
Y en su artículo 18 Plazos de prescripción de las acciones establece:
“1. Las acciones para exigir la responsabilidad prevista en el artículo anterior por daños mate-
riales dimanantes de los vicios o defectos, prescribirán
en el plazo de dos años a contar desde que se produzcan dichos daños, sin perjuicio de las
acciones que puedan subsistir para exigir responsabilidades por incumplimiento contractual.
2. La acción de repetición que pudiese corresponder a cualquiera de los agentes que intervienen
en el proceso de edificación contra los demás, o a los aseguradores contra ellos, prescribirá en
el plazo de dos años desde la firmeza de la resolución judicial que condene al responsable a
indemnizar los daños, o a partir de la fecha en la que se hubiera procedido a la indemnización
de forma extrajudicial.”
Por este motivo para facilitar la relación entre propietario y técnico de postventa se desarrolla el
módulo de Sigrid Postventa y el Portal Postventa.
Sigrid Postventa es una aplicación modular diseñada para mejorar y optimizar la gestión y
desarrollo de las reclamaciones surgidas durante o tras una obra, gestionada desde dentro del
propio concepto de obra para reunir propiedades, proveedores y reclamaciones y gestionarlas de
forma más eficiente.
Para completar y facilitar la gestión y comunicación desde Sigrid el propietario podrá ver sus
propiedades, canalizar todas sus reclamaciones a través del portal comunicado con Sigrid, la
evolución de las mismas y comunicarse directamente con el técnico de postventa.
Sigrid Postventa se complementa con los módulos de Planificación y/o CRM y Gestión Docu-
mental.
Manual Postventa Página 4 de 81

Guía de usuario Sigrid – Portal Postventa
Ventajas de uso
El módulo de Postventa ofrece a los usuarios de Sigrid la posibilidad de control de reclamacio-
nes por ejecución, control gestión, seguimiento y evolución de las mismas, así como su coordi-
nación y control de costes, facilitando esta labor ayudados del portal postventa atendiendo al
momento en que se realizan las reclamaciones, ya sean preventas, fin de obra o postventas
propiamente dichas.
- Asignar equipo de Postventa.
- Recopilar Oficios/subcontratas que trabajaron en la obra.
- Abrir la contabilidad desde las previsiones para postventa de la
ejecución de obra.
- Alta de inmuebles, propietarios y personas de contacto.
- Registro de incidencias de la Dirección Facultativa.
- Seguimiento y coordinación de equipos.
- Acta de fin de obra y comienzo de periodo de garantías.
- Registro de incidencias de propietarios con control de periodos
de garantía.
- Seguimiento y coordinación de equipos.
- Fin periodo de garantías.
- Evaluación de costes respecto previsión.
- Evaluación de incidencias y tiempo de respuesta.
- Evaluación de oficios.
Postventa Página 5 de 81

Guía de usuario Sigrid – Portal Postventa
Conceptos de Postventa en Sigrid
¿Qué es un concepto?
Conceptos serán los elementos básicos de información de la aplicación. Sirven para homogeneizar
los datos, de forma que puedan organizarse de la manera más conveniente y consultarse de
forma más sencilla.
A cada tipo de concepto se le puede asignar una serie, estado y proceso.
Serie se correspondería con las diferentes codificaciones que podemos darle a un tipo de
concepto, compuesto por una máscara y un correlativo (en un concepto de OBRA, las diferen-
tes series se corresponderían con obra nuestro código de serie sería por ejemplo O, obra de
edificación E, obra de estudio, etc.) Al dar de alta cualquier tipo de concepto siempre se nos
abrirá una ventana que nos pedirá la información siguiente:
Tipo de concepto
Fecha de creación
Código (serie)
Descripción
Delegación
Estado se correspondería con los distintos momentos vitales del concepto (si seguimos en el
caso de un concepto OBRA puede estar en estudio, ofertada, adjudicada, en ejecución, o en
nuestro caso en postventa, etc.)
Procesos se correspondería con el cambio de estado que sufre nuestro tipo de concepto (en
el caso de OBRA, pasar de estudio a ofertado, de ofertado a adjudicado, de en ejecución a
postventa, etc.). Esto conlleva una serie de cambios asociados, y permitirá realizar o no ciertas
acciones.
Postventa Página 6 de 81

Guía de usuario Sigrid – Portal Postventa
Tipos de Concepto
En este apartado se explicarán los diferentes conceptos de Sigrid que intervienen en la Postventa.
Concepto de Entidades
Se llaman entidades a los tipos de Conceptos que representan personas físicas o jurídicas: Pro-
veedor, Cliente, Referencia, Fabricante, Agente, Mi empresa, Empleado y Persona de Contacto.
La ventana de propiedades de estos Conceptos tiene varias pestañas, la primera de ellas corres-
ponde a los datos fiscales, la segunda a las direcciones postales. La tercera a personas de con-
tacto, y son iguales para todas las Entidades con excepción de Agentes y Empleados. El contenido
del resto de las pestañas varía según el tipo de Entidad.
En postventa se trabajará con las siguientes entidades:
Proveedor
Serán aquellos proveedores con los que se han trabajado durante la ejecución de obra,
tanto comerciales de suministros de materiales, contratistas, de servicios, etc., esto quiere
decir que ya tienen cuentas contables asociadas y datos para contactar con ellos.
Referencia
Una Referencia es una entidad que recoge los datos de un propietario o dirección faculta-
tiva, evitando así el darle de alta innecesariamente en contabilidad. Más tarde, se puede
crear un nuevo Cliente o Proveedor a partir de la Referencia, a la que queda asociado.
Postventa Página 7 de 81

Guía de usuario Sigrid – Portal Postventa
Cliente
Un cliente es una entidad que recoge los datos de aquellas personas físicas o jurídicas que
nos encargan un trabajo y vamos a facturarles.
Empleado
Un empleado es un tipo de entidad que recoge a los empleados de la empresa de trabajo
en Sigrid, en el caso de postventa para asociarlo a una obra como técnico de postventa o
como responsable de tramitar las tareas.
Persona de Contacto
Serán Personas de Contacto aquellas que demos de alta para establecer comunicaciones
con ellos que tiene la ventaja de poder asociarse a diferentes entidades como Contactos,
independientemente de que éstas sean referencias, clientes, proveedores, etc.
Estas personas de contacto se emplearán para comunicaciones ya bien sea mailing, comu-
nicación a través del portal, etc.
Obras
Obra/Proyecto
Es el concepto donde se ha generado el seguimiento y localizará todos los datos relativos
a la postventa de esa promoción en la pestaña para tal fin Post-venta.
Esta quedará dividida en 5 subpestañas a su vez:
Unidades Post-venta: Donde quedarán localizadas todos los inmuebles, sus propietarios
y persona de contacto para reclamaciones.
Postventa Página 8 de 81

Guía de usuario Sigrid – Portal Postventa
Tipologías: Servirá para definir los tipos de inmuebles por obra y sus ubicaciones que
serán las estancias separándolas por punto y coma.
Oficios: Será donde se definan los intervinientes en la postventa.
Reclamaciones: Listará todas las reclamaciones asociadas a la obra.
Postventa Página 9 de 81

Guía de usuario Sigrid – Portal Postventa
Productos
Los productos son los conceptos que utilizamos en los documentos de compra/venta.
Las clases de productos utilizados son los siguientes:
Mano de Obra: Indica las horas realizadas por un recurso.
Maquinaria: Se utiliza en la descomposición de la partida y suele indicar las horas reali-
zadas por una máquina.
Material: Indica los materiales a pedir.
Subcontrata: Indica una subcontrata de mano de obra exclusivamente o mano de obra
con aporte de material.
Los productos se clasifican por naturalezas y familias, asociadas a proveedores para facilitarnos
el trabajo a la hora de pedir ofertas a proveedores.
Conceptos de Postventa
Unidades Postventa
Este concepto definirá cada propiedad sobre la que se desee controlar la post-venta, yendo
cada propiedad asociada a una entidad de tipo Cliente o Referencia.
Partes de Reclamación
Este concepto registrará toda la información correspondiente a la reclamación de un pro-
pietario. Se podrán dar de alta manualmente y si se dispone del portal los propietarios o
dirección facultativa darán de alta las reclamaciones desde el mismo.
Tareas
La tarea será el concepto que se emplee para realizar el seguimiento, coordinación y noti-
ficaciones del estado de la reclamación.
Documentos de compras
Oferta de Compra
Son los documentos que generamos por proveedor o referencia para solicitar precios para
las reparaciones.
Postventa Página 10 de 81

Guía de usuario Sigrid – Portal Postventa
Pedido de Compra
Son los documentos que generamos por proveedor o referencia para solicitar precios para
las reparaciones.
Contrato de compra
Será el contrato que firmemos con un proveedor para los suministros de materiales o pres-
taciones de servicios. En este contrato figurarán todas las condiciones de recepción, pro-
veedor, método de pago, etc.
Albaranes de compra
Una vez recepcionados los productos, se generará el albarán con los productos recibidos.
O serán albaranes proformas en caso de ser subcontratistas donde se establecerán los
trabajos realizados que se pueden facturar.
Facturas de Compra
Las facturas de compra se darán de alta una vez recibida la factura de nuestro proveedor
donde figurarán las condiciones y método de pago.
Documento de venta
Pedido de venta
Pedidos de trabajos o suministros a realizar a propietarios que son facturables, para ello
los propietarios deberán ser dados de alta como clientes.
Factura de venta
Factura enviada al cliente y una vez aprobada contabilidad emitirá la factura. Se realizarán
con las condiciones establecidas la oferta con el cliente.
Postventa Página 11 de 81

Guía de usuario Sigrid – Portal Postventa
Portal Postventa
¿Qué es el Portal de Postventa?
El portal Postventa es una plataforma para el intercambio de información entre empresas,
propietarios y dirección facultativa para introducir, gestionar y resolver incidencias por mala eje-
cución de los trabajos realizados durante el proceso de ejecución de las obras. Dicho intercambio,
se realiza desde la base de datos local, hasta la visualización e interacción de los datos en el
portal y viceversa, todo ello a través de un servicio Web.
Este sistema de intercambio de información, se provee de varios mecanismos para poder realizar
el acceso desde la web y llevar a cabo el intercambio de información.
La empresa, tendrá que aceptar las condiciones de uso del portal Postventa, donde siempre que-
darán protegidos sus derechos y confidencialidad.
El objetivo primordial es, facilitar la comunicación de la empresa con los intervinientes de las
reclamaciones, disminuyendo los gastos de gestión y favoreciendo la solución de posibles discre-
pancias.
Para que un propietario tenga acceso a la plataforma, la empresa será quien tenga que dar acceso
al propietario/dirección facultativa, en función de los criterios establecidos. Estos criterios serán
independientes de la plataforma y por lo tanto de Professional Software.
El acceso al portal Web por parte de propietarios, se llevará a cabo a través de la siguiente
dirección:
https://postventa.ruesma.com/
Postventa Página 12 de 81

Guía de usuario Sigrid – Portal Postventa
Usuarios
Tipos de usuarios
En relación a los usuarios entre Sigrid y Portal, tendremos:
- Usuarios de Sigrid  El personal de la empresa, tendrá acceso a la aplicación Sigrid3,
desde donde, podrá configurar y dar de alta los contactos de los propietarios con acceso
al portal. No tendrán acceso al portal.
- Contactos de Propietarios o Dirección Facultativa en el Portal  Los contactos de
los propietarios serán dados de alta como usuarios del Portal por el personal de postventa
a través de Sigrid, tal y como se indicará en el presente manual. Los propietarios acce-
derán con su usuario (correo electrónico) y contraseña. (En el manual del portal, se ex-
plicará y se dará a conocer la interface del Portal. En el caso de los propietarios tendrán
acceso a sus propiedades que figuren como contacto y sus reclamaciones registradas. En
caso de Dirección facultativa tendrán acceso a toda la promoción donde figure como con-
tacto y sus reclamaciones registradas.
Postventa Página 13 de 81

Guía de usuario Sigrid – Portal Postventa
Alta de usuarios
Los encargados de dar de alta los diversos usuarios deberán dar de alta la persona de contacto
de la entidad cliente o referencia para su acceso al portal.
Lo más importante es que los usuarios serán conceptos de tipo persona de contacto, y su login
será el Código de entrada (email) que será único por persona de contacto, no puedo tener dos
personas de contacto con el mismo correo de login.
Para ello tendrán que seguir los siguientes pasos:
En primer lugar, sobre un cliente/referencia
existente o nuevo como mínimo este deberá tener
los datos de Código, Descripción, razón social
y CIF/NIF.
El código y descripción son datos indispensables
para dar de alta un concepto en Sigrid.
La razón social será el campo que se muestra
como Empresa en el Portal Postventa.
Para relacionar toda la información relativa a esta
entidad, se empleará la identificación fiscal, por lo
que se empleará el NIF/CIF, un número único que
evitará duplicidades.
Postventa Página 14 de 81

Guía de usuario Sigrid – Portal Postventa
En segundo lugar, tener un concepto Persona de Contacto nueva o existente y sus datos nece-
sarios:
- Nombre Completo
- DNI
- Correo electrónico
- Nº de teléfono
- Código de entrada (email),
este campo será el correo que
emplearán los usuarios para ac-
ceder al portal, por tanto este
campo es imprescindible.
Postventa Página 15 de 81

Guía de usuario Sigrid – Portal Postventa
En tercer lugar, esta Persona de Contacto deberá estar asociada como Contacto en la pestaña
de contactos a la entidad correspondiente:
Para crear un nuevo contacto se presionará sobre el botón Nuevo Contacto:
Al asociar la Persona contacto automática-
mente rellenará los datos de la Ficha de con-
tacto tales como Nombre del contacto y Datos
comerciales para esta empresa.
A continuación, para empresas se rellenarán:
- Cargo/Departamento. Meramente in-
formativo.
- Tratamiento. Meramente informativo.
- Es administrador, este check solo se
marcará en empresas que tengan varios usua-
rios en el portal, y le permitirá gestionar los
usuarios de su empresa y visualizar todos los
inmuebles y reclamaciones de las promociones
donde figure la empresa.
Finalmente, para dar de alta al usuario en el portal desde lo haremos desde la Unidad de
Postventa u obra, dependiendo del tipo de usuario se esté dando de alta en el portal, en la guía
de Postventa especifica una acción para dar de alta personas de contacto de la dirección
facultativa con su obra asignada y desde las unidades postventa mediante cambio de estado
enviaremos altas masivas a cada propietario con su inmueble definido. En ambos casos mandará
un correo con un enlace con un Token para activar la cuenta e introducir la contraseña, este
token caducará a los 30 días.
Postventa Página 16 de 81

Guía de usuario Sigrid – Portal Postventa
Menus de Acceso
Mis Datos
Desde esta pestaña los propietarios podrán visualizar sus datos de contacto diferenciando entre
dos tipos de usuario:
Usuario normal
Verá los siguientes campos:
PESTAÑA MIS DATOS
Contacto: Nombre Completo que aparece en la ficha de contacto en Sigrid.
Empresa: Razón social de la entidad a la que pertenece la persona de contacto, en este
caso podrán ser entidades de tipo Referencia o Cliente.
Cargo/Departamento: Cargo asignado a la persona de contacto en la ficha de propieda-
des.
Postventa Página 17 de 81

Guía de usuario Sigrid – Portal Postventa
Usuario administrador
Verá los mismos datos en la pestaña de mis datos y además:
PESTAÑA DATOS DE EMPRESA:
Datos Fiscales: Correspondientes a los datos de la pestaña Datos Fiscales y su apartado de
datos fiscales en la ficha de la entidad.
Nombre/Razón Social: Razón social
que aparece en la ficha de entidad en
Sigrid.
CIF/NIF: Identificación Fiscal de la en-
tidad que aparece en la ficha de entidad
en Sigrid.
Dirección: Dirección de la entidad que aparece en la ficha de entidad en Sigrid.
C.Postal: C.Postal de la entidad que aparece en la ficha de entidad en Sigrid.
Municipio: Municipio de la entidad que aparece en la ficha de entidad en Sigrid.
Provincia: Provincia de la entidad que aparece en la ficha de entidad en Sigrid.
País: País de la entidad que aparece en la ficha de entidad en Sigrid.
Datos comerciales: Correspondientes a los datos de la pestaña Datos Fiscales subapartado
de datos comerciales en la ficha de la entidad.
Postventa Página 18 de 81

Guía de usuario Sigrid – Portal Postventa
PESTAÑA MIS CONTACTOS
Esta pestaña mostrará los contactos que tiene esta empresa con acceso al portal, donde la propia
empresa podrá gestionar sus accesos, alta de nuevos usuarios que se registrarán en Sigrid:
Postventa Página 19 de 81

Guía de usuario Sigrid – Portal Postventa
Inmuebles
Los inmuebles serán las unidades postventa a las que tienen acceso los usuarios desde el portal.
En el caso de personas de contacto de la Dirección Facultativa tendrán acceso a toda la promoción
en un estado determinado para introducir las reclamaciones referentes a los repasos de fin de
obra.
En el caso de personas de contacto de propietarios tendrán acceso a las unidades postventa en
las que figuren como propietarios en Sigrid.
Solo se podrán introducir reclamaciones durante el periodo de garantía fijado para el inmueble,
una vez transcurrido dicho periodo desde el portal no se podrán registrar nuevas reclamaciones.
Postventa Página 20 de 81

Guía de usuario Sigrid – Portal Postventa
Clicando sobre el inmueble, se accederá a la ficha del mismo, desde la cual se podrán dar de alta
nuevas reclamaciones, así como visualizar todas aquellas que estén registradas por el usuario
logado.
1
2
3
4
1 En el cuadro superior se visualizarán los datos correspondientes al inmueble, tales como
descripción del inmueble y obra a la que pertenece, periodos de garantía y tipología de vivienda.
2 Alta de nueva reclamación, para registrar las nuevas reclamaciones ya asociadas a la
vivienda en la que está situado el usuario.
3 Listado de reclamaciones ordenado en orden descendente por fecha de registro, donde se
visualizará el código de reclamación,descripción, fecha y hora de registro y estado de la misma.
4 Los usuarios del portal podrán filtrar las reclamaciones para que les sea más fácil localizar
la reclamación que buscan atendiendo a cualquiera de los campos que visualizan.
Postventa Página 21 de 81

Guía de usuario Sigrid – Portal Postventa
Reclamaciones
Las reclamaciones siempre funcionarán igual independientemente del tipo de usuario. El usuario
que las registre en el portal, será el usuario que las visualice.
Desde esta vista se podrán dar de alta nuevas reclamaciones, en este caso, si el usuario tiene
varios inmuebles en garantía al registrar una nueva reclamación deberá indicar sobre que inmue-
ble quiere registrar la reclamación.
Debajo verá el listado de todas las reclamaciones registrada en el sistema separadas por estados,
al clicar en cualquiera de los epígrafes se mostrarán todas las reclamaciones
Postventa Página 22 de 81

Guía de usuario Sigrid – Portal Postventa
Guía de Postventa
Con esta guía se pretende en líneas generales expresar el procedimiento de trabajo de postventa
atendiendo a las políticas de la empresa y presupuesto establecido.
Políticas de Servicio de Postventa a nivel de empresa.
Es importante tener como empresa una política clara y definida del servicio de Postventa y en-
tregarla a los propietarios para ajustar las expectativas entre lo que se espera del servicio y lo
que realmente se entrega. La Política deberá abarcar los siguientes puntos:
1. Los equipos de trabajo para delimitar y esclarecer los campos de actuación, atribucio-
nes o facultades y herramientas que cuenta el departamento de postventa.
2. Contabilidad de Postventa. Es conveniente que durante la ejecución de la obra se
considere una parte del presupuesto a los trabajos de postventa, y este venga reflejado
en los precios de venta presentados al cliente.
Al principio puede ser complicado establecer un valor, siempre se puede partir de un
porcentaje sobre precios de coste, venta o producción; y posteriormente con la experien-
cia evaluar si este porcentaje cubre las necesidades de este departamento.
Así como establecer el procedimiento de gestión de la documentación de compras/ventas
en caso de tenerla.
3. Definir inmuebles, propietarios y plazos de garantía a los que le afecta el inmueble.
4. Cobertura del servicio.
a. Los plazos ideales de atención y control de su cumplimiento.
b. Cuáles serán los casos de urgencia y cuáles son los casos de emergencia y mé-
todo de actuación, plazos fechas, etc.
c. Estandarizar las respuestas de los diagnósticos de visitas de inspección y definir
las condiciones para la recepción de los trabajos, dejando establecido a qué Ma-
nuales, Normativa o Práctica habitual se ajustarán.
5. Método de seguimiento de reclamaciones, método de contacto, horarios y días de
atención para citas técnicas o de reparación, así como cierre de reclamaciones por falta
de disponibilidad del cliente o solicitante.
6. Condiciones de satisfacción del servicio y Resultado.
Para facilitar los servicios de postventa de una promoción todos los datos quedarán registrados
desde el concepto Obra, para reunir en un único concepto todos los datos relacionados.
Postventa Página 23 de 81

Guía de usuario Sigrid – Portal Postventa
1. Intervinientes de la postventa
Para comenzar el trabajo de Postventa lo primero será designar aquellos empleados propios,
ajenos y propietarios que van a intervenir en el proceso.
Desde la obra en la pestaña de Postventa subpestaña de Oficios se definirán los distintos trabajos
relacionados con la postventa, así como el técnico responsable de postventa de la empresa, la
dirección facultativa y su persona de contacto, y los oficios con sus proveedores contratados
durante la ejecución de la obra, o nuevos proveedores si fuese necesario.
Asignación del equipo de Postventa de la empresa
La ventana está dividida en dos secciones diferenciadas, Responsables y Oficios
Postventa Página 24 de 81

Guía de usuario Sigrid – Portal Postventa
Responsables:
Técnico de Postventa Responsable: Será la entidad de tipo empleado perteneciente
a la empresa responsable de la postventa. Este será el técnico responsable de las post-
ventas de la obra, en caso de tener la empresa varios técnicos designados para esta obra,
deberán figurar los demás empleados en la pestaña de intervinientes de la obra.
NOTA: Todos los intervinientes que aquí figuren con rol relacionado con Postventa serán
los que tengan acceso a todas las consultas de MIS DATOS DE POSTVENTA:
Dirección facultativa: Será la entidad de tipo referencia encargada de la dirección de
obra o promotor.
Persona de contacto: Será la entidad Persona de contacto perteneciente a la entidad
de la Dirección facultativa responsable de introducir las reclamaciones de fin de obra y
daremos de alta en el portal de Postventa para tal fin.
Para notificar el alta de la Dirección Facultativa en el portal de Postventa para que puedan
introducir reclamaciones de fin de obra, emplearemos la acción de obra Comunicar
Nueva promoción a Dirección Facultativa (Portal Postventa), para ello presiona-
mos sobre el icono del concepto obra, vamos al epígrafe Acciones y pulsamos sobre la
acción:
Postventa Página 25 de 81

Guía de usuario Sigrid – Portal Postventa
Y en la ventana de dialogo solo tendremos que aceptar el envío. Podremos configurar la
dirección de correo del remitente, por defecto si se deja en blanco, tomará el correo que
tenga del empleado asociado el usuario que está ejecutando el proceso.
El asunto vendrá definido por defecto y se podrá modificar a necesidad del usuario.
El cuerpo del email será una plantilla predefinida.
Y finalmente se podrán indicar otros usuarios con copia o copia oculta a los que se quiera
enviar el email.
El email del destinatario será el que tenga en su ficha la persona de contacto establecida
como contacto de la dirección facultativa.
Postventa Página 26 de 81

Guía de usuario Sigrid – Portal Postventa
Oficios y proveedores intervinientes en obra
La asociación de oficios se realizará de forma manual o masiva mediante un java. Y visualizare-
mos los siguientes campos:
Oficio: Código del oficio.
Descripción Oficio: Descripción del oficio.
Proveedor: Código del proveedor que hemos asociado para este oficio en la obra.
Nombre Proveedor: Descripción del proveedor que hemos asociado para este oficio en
la obra.
Comentario: Servirá para dejar una nota aclaratoria para dicho proveedor en la obra en
concreto. Por ejemplo, si varios proveedores de carpintería han trabajado en la obra para
indicar en que zonas han trabajado cada uno, es un texto libre a rellenar por el usuario
según su necesidad.
Teléfono: Teléfono de la pestaña Datos Fiscales de la Ficha del Proveedor.
Correo Electrónico: Email de la pestaña Datos Fiscales de la Ficha del Proveedor.
En cualquiera de los dos casos los oficios deben estar definidos en la tabla auxiliar Post-Venta:
Oficios (auxofc).
Postventa Página 27 de 81

Guía de usuario Sigrid – Portal Postventa
Asociación Manual
Desde la línea de edición de la pestaña Oficios de la obra se podrán introducir manualmente uno
a uno los oficios y posteriormente se asociará el proveedor, o se seleccionarán todos los oficios
de forma masiva desde la ventana de multiselección presionando * e intro en el campo de edición.
Línea por línea, de los oficios traídos a la pestaña de oficios, tendremos que ir seleccionando cada
uno de los proveedores asociados a dicho oficio, para ello se selecciona la línea de oficio y desde
la línea de edición del campo Proveedor * e intro saldrá la ventana de selección para asociar uno
a uno cada proveedor.
*
También clicando dos veces sobre el oficio nos saldrá la ficha de oficio de proveedores en obra,
desde la cual podemos asociar el proveedor a través de la ventana de selección.
Postventa Página 28 de 81

Guía de usuario Sigrid – Portal Postventa
Asociación masiva de oficios de obra
Mediante la acción de obra Agregar Oficios de Proveedores de Contratos, presionando sobre
el icono de la obra vamos al epígrafe Acciones y pulsamos sobre la acción:
Esta acción sirve para dar de alta Oficios en la Obra desde los Contratos de compra. Lee los
contratos de compra y lee el oficio del proveedor del contrato.
Comprueba si existe para la obra un registro de oficio para ese proveedor y oficio. Si no existe lo
crea, asociando el oficio que tenga indicado el proveedor en su ficha de propiedades en la pestaña
Comercial en el campo Oficio.
Si lo tenemos en varios contratos sólo realizará la asociación una vez.
Postventa Página 29 de 81

Guía de usuario Sigrid – Portal Postventa
Este oficio es modificable para la obra en concreto y un mismo proveedor puede tener varios
oficios para la misma obra, por lo que tendremos que darle de alta para los distintos oficios que
tenga en nuestra obra:
Si un proveedor no tiene oficio asignado, lo pintará desde el contrato y deberemos asociarle el
oficio manualmente:
Seleccionando la línea y presionando * e intro en el campo de edición del oficio:
Propietarios
Los propietarios serán los dueños de los inmuebles, por lo que se darán de alta con cada inmue-
ble.
Postventa Página 30 de 81

Guía de usuario Sigrid – Portal Postventa
2. Contabilidad de Postventa y control de costes
Para el control de costes de la postventa se seguirá realizando de la misma manera que se lleva
actualmente.
Se dará de alta la obra como una partida de la obra de postventa, y se cargarán albaranes y
facturas contra dicha partida:
Postventa Página 31 de 81

Guía de usuario Sigrid – Portal Postventa
3. Inmuebles, propietarios y plazos de garantía
El siguiente punto será establecer todos los propietarios, sus inmuebles estableciendo sus tipo-
logías.
Los inmuebles definirán por sus estados en el proceso en el que se encuentran:
Fin periodo
garantía
3. EN
GARANTÍA
•Finalizado periodo garantías
•Proceso de alta de inmuebles
•Alta de Técnico de DF en el •Reclamación de deficiencias
constructivas por parte de los
portal
propietarios
1. EN 3. GARANTÍA
PREVENTA TERMINADA
Alta propietarios
en el Portal
Desde la pestaña de Postventa subpestaña Unidades Postventa se localizarán todos los inmuebles
del proyecto.
Postventa Página 32 de 81

Guía de usuario Sigrid – Portal Postventa
Se visualizarán las siguientesd columnas:
Código: Código que le asignemos a la unidad postventa.
Descripción: Nombre asignado a la unidad postventa.
Tipología: Código de la tipología que tiene asociada la unidad postventa.
Descripción tipología: Descripción de la tipología que tiene asociada la unidad postventa.
Inicio: Fecha de comienzo del periodo de garantías.
Fin: Fecha de finalización del periodo de garantía de la estructura.
Cliente-Referencia: Código de la entidad asociada a la propiedad. Podremos asignar el
concepto de cliente para emitirle facturas o referencia, previa configuración en parámetros
generales de con qué concepto se quiere trabajar.
Descripción: Descripción de cliente o referencia.
Código del contacto: Código de la persona de contacto, dentro de la referencia de la
unidad postventa. Será la que recibirá las comunicaciones para interactuar desde el Portal
de Postventa.
Descripción del contacto: Descripción de la persona de contacto.
Teléfono: Teléfono de comunicaciones con la persona de contacto de la entidad.
Correo Electrónico: Email de la persona de contacto, el cual será el usuario de login para
el Portal.
Estado: Código en el que se encuentra la unidad postventa.
Descripción del Estado: Descripción del que se encuentra la unidad postventa.
Y los siguientes botones:
Nuevo Registro: Botón para dar de alta manualmente una a una las unidades postventa.
Elimina Registro: Botón para eliminar una unidad postventa.
Actualiza lista: Botón para refrescar la vista de unidades postventa si se han realizado
modificaciones sobre la consulta.
Ficha de Registro: Abre la ficha de propiedades de la unidad postventa seleccionada.
Postventa Página 33 de 81

Guía de usuario Sigrid – Portal Postventa
Dentro de una ficha de unidad postventa se diferenciarán tres pestañas:
General
Llevará los datos que definen el inmueble y los datos de propietario y contacto.
Fechas relevantes
Se las fechas por las que se ve afectado el inmueble.
- Fecha de escrituración: Fecha de firma de la escrituración por parte del propietario.
- Fecha fin primer listado: Hace referencia al plazo marcado por la empresa para presentar
reclamaciones de postventa por parte de un propietario de tipo estético.
- Periodos de garantía: Los establecidos legalmente en la LOE.
Reclamaciones
Se visualizarán los periodos de garantía que afectan al inmueble y listadas todas las reclamacio-
nes asociadas a esta unidad de postventa.
Postventa Página 34 de 81

Guía de usuario Sigrid – Portal Postventa
Alta Unidad Post-venta
Existen diversas formas de dar de alta las unidades postventa.
Alta manual
Las unidades postventa podrán darse de alta manualmente desde la obra, subpestaña Unidades
Postventa, desde la ventana principal de sigrid en el menú concepto, con el botón rápido de altas
al final de la ventana o desde un acceso directo en la barra de botones.
O lo más lógico será desde la propia obra donde estamos ya ubicados y trabajando:
Postventa Página 35 de 81

Guía de usuario Sigrid – Portal Postventa
Alta masiva
Para dar de alta unidades postventa de forma masivo se hará con Excel, mediante la acción de
obra Generar Plantilla Excel de Unidades Postventa, se generará una plantilla protegida para
cada obra, donde los únicos campos editables serán de color verde y posteriormente cuando la
plantilla esté completa se importarán los datos a Sigrid mediante la acción de obra Importación
de Unidades Postventa (MS-Excel).
Generar Plantilla Excel de Unidades Postventa
Esta acción crea un Archivo Excel con los siguientes datos:
DDDaaaDtttoooassst o sccc aaa -- -
catttaaatasssttstrrrtaaarallleeelsses s DDDDaaaattttoooossss PPPPeeeerrrr---- Datos otra persona de
ssssoooonnnnaaaa ddddeeee contacto (sin acceso al
Tipología de CCoommppoossiicciióónn DDaattooss ddeell ccccoooonnnnttttaaaaccccttttoooo yyyy portal)
inmueble ddee uunniiddaadd PPrrooppiieettaarriioo aaaacccccccceeeessssoooo aaaallll
ppoossttvveennttaa
ppppoooorrrrttttaaaallll
Postventa Página 36 de 81

Guía de usuario Sigrid – Portal Postventa
Esta exportación permitirá generar una plantilla para dar de alta los inmuebles y propietarios, si
ya existen datos de Unidades postventa y propietarios la plantilla saldrá con los datos de ya
registrados, y se podrán dar de alta nuevos inmuebles o sobre los existentes modificar los datos
de los propietarios o añadir propietarios.
Composición unidad: Estos campos se emplearán para componer los códigos y descripción de
cada unidad postventa que se dará de alta en la obra. Para establecer los tipos se hará desde la
tabla auxiliar Obras: Identificación de superficies (auxobrsup).
Unidad: Composición de código y descripción a través del código de la obra, tipología y datos
catastrales, campos no editables.
Propietario: Datos con los que se darán de alta en Sigrid la entidad de tipo cliente o referencia
según tengamos definido en parámetros generales. Nombre y NIF/CIF para no repetir la misma
entidad en Sigrid, si ya existe el NIF toma la entidad existente y no la crea nueva.
Contacto1: Datos de la persona de contacto que se dará de alta en el portal de postventa, para
ello es imprescindible el email, además al igual que con el propietario se requiere de un NIF/CIF
para no dar de alta de forma duplicada esta persona de contacto y quedará asociada en Sigrid
como contacto de la entidad a la que se corresponde.
Contacto 2: Segundo contacto de la propiedad, con los mismos datos que el contacto 1, pero no
accede al portal de postventa.
Importación de Unidades Postventa (MS-Excel)
Acción para importar desde un archivo Excel, generado mediante la acción ObrAcc_Generar_Plan-
tilla_UPV.xjs.
Postventa Página 37 de 81

Guía de usuario Sigrid – Portal Postventa
Importa las Unidades Postventa del archivo Excel asociándolas a la Obra sobre la que se ejecuta
la Acción, en la plantilla figurará la obra que debe coincidir con el de la Obra desde la que lanza-
mos la acción, sino no permitirá la importación.
Al lanzar la acción aparecerá una ventana de diálogo donde nos solicita la plantilla de datos a
importar:
Las filas con los datos de los Unidades Post-Venta a importar comienzan en la fila 8.
Tras terminar la acción, quedarán los datos asociados en Sigrid a falta de establecer las tipologías
y periodos de garantía.
Si no disponemos de todos los propietarios se podrán dar de alta posteriormente de forma manual
o reimportando el fichero de Excel completado.
Postventa Página 38 de 81

Guía de usuario Sigrid – Portal Postventa
Estableces Tipologías
Las tipologías definirán las diferentes unidades postventa que tenemos para la obra concreta. Se
especificarán para cada obra y se asociarán a las unidades postventa para definirlas, estable-
ciendo las ubicaciones (estancias), así como asociarles su plano tipo a cada una, este plano tipo
servirá para que desde la web el propietario pueda seleccionar la estancia más fácilmente. Por
ejemplo,
TIPO A de 3 dormitorios tendrá Salón;Cocina;Tendedero;Baño Ppal;Baño 2;Dormitorio Ppal;Dor-
mitorio2;Dormitorio3;Entrada;Pasillo, mientras que una
TIPO B de dos dormitorios tendrá Salón;Cocina;Tendedero;Baño Ppal;Baño 2;Dormitorio
Ppal;Dormitorio2;Entrada;Pasillo.
Para definir una tipología se dará un código y descripción, y en ubicación se definirán todas
las estancias que tiene esta propiedad separadas por punto y coma. Además, se podrá dejar un
comentario aclaratorio para la misma.
Para asociar el Plano Tipo primero se tiene que tener definido un tipo de gráfico específico para
ellos en la tabla auxiliar Documental: Tipo de gráfico (auxgra) en este caso PV005 y ese mismo
código debe estar indicado en parámetros generales en el apartado de postventa en el campo
Código del tipo de gráfico para las tipologías de la obra.
Postventa Página 39 de 81

Guía de usuario Sigrid – Portal Postventa
Una vez configurado el Tipo de gráfico/documento solo habrá que importar las imágenes en
la ventana de gráficos y documentos asociados al concepto de la obra con ese mismo código:
Finalmente, para que el programa haga la asociación con las tipologías de obra se debe introducir
como Código el código de la Tipología que hemos dado de alta, en caso de trabajar con reposi-
torio externo este código se genera de forma automática y no es editable, el nombre del archivo
que se visualiza como Descripción deberá ser el mismo que el de la tipología.
Al clicar sobre el icono que aparecerá tras la asociación podremos abrir el plano.
En caso de tener varios planos asociados a la misma tipología, al clicar sobre el icono nos abrirá
una ventana de dialogo para seleccionar qué grafico queremos abrir:
Postventa Página 40 de 81

Guía de usuario Sigrid – Portal Postventa
Presionando en Sí, abrirá la ventana de selección de los planos
disponibles; en No cerrará el diálogo:
Pudiendo seleccio-
nar cual queremos previsualizar.
Una vez tengamos las tipologías definidas las podremos establecer dentro de la ficha de propie-
dades de las Unidades Postventa:
La asociación de tipologías se podrá realizar de forma masiva desde la pestaña de Unidades Post-
Venta de la obra mediante la acción Establecer Tipología de Unidad Postventa, para ello
haciendo multiselección de aquellas UPVs a las que queramos asignar tipología y pinchando con
el botón derecho sobre el icono de una de las UPV seleccionadas se abrirá la ventana de propie-
dades y en el epígrafe acciones seleccionaremos la acción.
Postventa Página 41 de 81

Guía de usuario Sigrid – Portal Postventa
Esta acción lanzará una ventana de dialogo donde se seleccionará una de las tipologías definidas
en la subpestaña de tipologías de la obra que queramos establecer a la selección:
Presionando en el campo tipología * e intro abriremos el
menu de selección, aceptando se realizará la asociación.
Postventa Página 42 de 81

Guía de usuario Sigrid – Portal Postventa
Fechas relevantes
Comprenderá todas aquellas fechas por las que se ven afectadas las unidades de postventa (in-
muebles).
Fechas
Fecha de escrituración: Fecha que indica cuando escrituró el propietario su inmueble, y
sirve como referencia del inicio del periodo de reclamaciones por fallos estéticos.
Fecha fin primer listado: Para indicar la fecha de fin del periodo de reclamaciones por
fallos estéticos.
Fecha Visita Técnico: Para indicar la fecha de visita de cortesía por parte del técnico de
postventa con el propietario para revisar los fallos estéticos, limitaría la fecha de fin de
primer listado.
La introducción de estas fechas son manuales por parte del usuario en Sigrid.
Periodos de Garantía
Los periodos de Garantía se fijan 3 periodos según la legislación Vigente, pero pueden configu-
rarse desde parámetros generales.
Vicios o defecto (1 año): Para indicar la fecha de inicio y fin para este periodo de garan-
tía.
Habitabilidad/Instalaciones (3 años): Para indicar la fecha de inicio y fin para este
periodo de garantía.
Estructura (10 años): Para indicar la fecha de inicio y fin para este periodo de garantía.
Se podrá establecer los periodos de garantía de forma masiva desde la pestaña de Unidades Post-
Venta de la obra mediante una acción Establecer Periodos de Garantía a toda la promoción.
Postventa Página 43 de 81

Guía de usuario Sigrid – Portal Postventa
Esta acción permite rellenar de manera masiva los periodos de garantía sobre las unidades post-
venta seleccionadas. Sobre el dialogo se solicita una fecha, esta fecha será la de inicio de los
periodos y automáticamente calculará todos los periodos, en caso de dejar el campo en blanco
tomará la fecha de trabajo:
Postventa Página 44 de 81

Guía de usuario Sigrid – Portal Postventa
Notificar alta de usuarios en el portal
Una vez firmado el acta de fin de obra y comiencen los periodos de garantía o se hayan escritu-
rado las viviendas se pueden dar de alta a los usuarios en el portal, para ello desde la obra
situándose en la subpestaña de unidades postventa y se seleccionan todas las unidades de post-
venta y con un cambio de estado se mandará el correo de alta en el portal:
Este proceso enviará el email de bienvenida a los nue-
vos usuarios y el de nueva promoción a los usuarios
dados de alta previamente en el portal (tienen contra-
seña de acceso al portal)
Con este email se podrán introducir la ficha del inmue-
ble y los documentos que estén ubicados en una loca-
lización determinada (por ejemplo, el manual de usua-
rio del portal) a todos los propietarios de las unidades
postventa seleccionadas de forma masiva.
Si no se desea mandar el correo, porque la promoción
no va a emplear el portal, con desmarcar el check de
Enviar por email será suficiente.
Postventa Página 45 de 81

 Guía de usuario Sigrid – Portal Postventa
4. Cobertura del Servicio
Será labor de la empresa definir los plazos ideales de atención y control de su cumplimiento.
Cuáles serán los casos de urgencia y cuáles son los casos de emergencia y método de actuación,
plazos fechas, etc.
Estandarizar las respuestas de los diagnósticos de visitas de inspección y definir las condiciones
para la recepción de los trabajos, dejando establecido a qué Manuales, Normativa o Práctica
habitual se ajustarán.
Atendiendo al siguiente flujo de reclamaciones:
Flujo de Reclamaciones
| PROPIETARIO                             | SIGRID              | PROVEEDOR |
| --------------------------------------- | ------------------- | --------- |
| Registro                                | Registro            |           |
| Usuarioincidencia Portal                | PCincidencia Sigrid |           |
| senoicamalceR ed ortsigeR Solicitud de  | 1                   |           |
SIN ATENDER
información
|                       | Solicita Doc                 | Diagnóstico  |
| --------------------- | ---------------------------- | ------------ |
| INFORMACION SOLICITA  | ¿Necesita más   información? | inicial      |
No
¿Evaluación?
Devuelve Documentación
NO PROCEDENTE
Envía correo
con motivo
de rechazo PROCEDENTE
| 7          | 3             |             |
| ---------- | ------------- | ----------- |
|            | Confirmación  | Asignación  |
| NO PROCEDE | de  PENDIENTE | de Oficios  |
tramitación
sojabart ed nóicaraperP
|     | PEDIDOS | Pedidos |
| --- | ------- | ------- |
|     | SI      | SI      |
P E D ID O  D E
| PEDIDO DE VENTA | ¿Necesita?                  | C O M P R A |
| --------------- | --------------------------- | ----------- |
|                 | Acepta pedido Devuelve Cita |             |
NO
|     | SI  | SI  |
| --- | --- | --- |
REPA R A C ION/
| CITAS REPARACION | C IT A S                    | REPARACION |
| ---------------- | --------------------------- | ---------- |
|                  | Devuelve cita Devuelve Cita |            |
¿Firmada?
Coordinar citas de
Reparación
NO
| nóicarapeR | 5   |     |
| ---------- | --- | --- |
TERMINADA
|     | SI NO |     |
| --- | ----- | --- |
¿Firmada?
SI
9
CERRADA

Postventa  Página 46 de 81

Guía de usuario Sigrid – Portal Postventa
Alta de Partes de Reclamaciones
Reclamaciones web
Las reclamaciones web las podrán dar de alta las personas de contacto de los propietarios asig-
nados a tal fin durante el periodo de postventa, atendiendo a las fechas de inicio y fin de garan-
tías. Y las personas de contacto de la dirección facultativa asignados a tal fin durante antes del
comienzo de periodo de garantías, siguiendo las indicaciones del manual de portal postventa.
Estas reclamaciones se darán de alta con la serie establecida en parámetros generales.
El registro siempre se realizará atendiendo al inmueble al que tienen acceso desde el portal. Los
datos de Registro que tendrán disponibilidad de rellenar desde el portal serán:
Correo y teléfonos adicionales para avisos, clase de reclamación, urgencia y motivo de la urgen-
cia, así como la descripción corta y larga del problema.
De forma automática al dar de alta una reclamación desde el portal se grabarán los datos relativos
a la obra, unidad de postventa, tipo de reclamación (si se trabaja con tipos) y fecha y hora de
registro.
Postventa Página 47 de 81

Guía de usuario Sigrid – Portal Postventa
Importador de Reclamaciones
Cuando se trabaje con las reclamaciones que envía el promotor directamente, mandarán un lis-
tado Excel, y éste lo podremos importar directamente en Sigrid para su gestión.
Para ello desde la obra, se seleccionará el botón inferior Archivo->importar y se seleccionará la
acción Importación de Partes de reclamación desde Excel:
Esta acción abre un cuadro de dialogo para configurar las opciones de importación:
Se seleccionará el fichero de Excel que
tenga el usuario en el ordenador.
La serie con la que se dará de alta la
reclamación para componer los códi-
gos.
Para diferenciar preventas o postven-
tas.
Postventa Página 48 de 81

Guía de usuario Sigrid – Portal Postventa
Si son preventas se marcará el chek de preventa y se indicará la tipología a grabar y quien es la
promotora para grabar todas las reclamaciones a la referencia que indiquemos y la persona de
contacto que seleccionemos de dicho promotor:
Si son postventas, indicaremos la serie de postventa, el check de postventa y el tipo de reclama-
ción, el propietario se grabará automáticamente con los propietarios y personas de contacto que
tengan indicadas la unidad de postventa:
Postventa Página 49 de 81

Guía de usuario Sigrid – Portal Postventa
El formato de Excel siempre tendrá que ser el mismo:
- La primera columna deberá ser el portal, la segunda el piso, la tercera la letra, al importar
crearán la vivienda, si no está dada de alta.
- La columna D se corresponderá con la estancia a la cual pertenece la reclamación.
- La columna E ser corresponderá con la descripción de la reclamación que interpone el
propietario/promotora.
- La columna F se corresponderá al oficio, ojo, que dará de alta todos aquellos oficios que
no figuren en base de datos, por lo que si tenemos Carpintería de madera y carpintero
madera, son los mismos, pero el sistema al no llamarse igual dará de alta nuevos oficios.
Si ya tenemos rellena la pestaña de oficios de la obra, en la reclamación en la pestaña
intervinientes se visualizará el oficio y proveedor. Si no está realizada esta labor, asig-
nado el proveedor al oficio en la obra ya se visualizará en la reclamación, añadiéndolo
únicamente en la obra.
Hay que tener en cuenta, que si tenemos el mismo oficio varias veces en la obra con
distintos proveedores colocará el primer oficio encontrado y deberemos modificar ma-
nualmente el proveedor en la reclamación.
- Nº de Referencia Externo, solo se rellenará esta columna cuando el listado incluya el
código de reclamación que nos envía el promotor para coordinar las codificaciones del
cliente con las nuestras internas.
Portal
Oficio
Piso
Ubicación de la
reclamación
Letra
Nº Referencia
Externo
Descripción de la
reclamación
Postventa Página 50 de 81

Guía de usuario Sigrid – Portal Postventa
Reclamaciones manuales
Las reclamaciones también se podrán dar de alta manualmente desde Sigrid. Para introducir una
reclamación se puede realizar desde la ventana principal de Sigrid al igual que con las unidades
postventa explicado anteriormente en el manual, pero no conviene puesto que deberíamos intro-
ducir una serie de datos que si realizamos el alta desde la unidad postventa no serán necesarios
y evitaremos errores.
Para ello, desde la pestaña de reclamaciones de la unidad postventa donde queramos introducir
la reclamación, presionamos en Nueva:
Y se selecciona la serie con la que se quiere dar de alta, la serie define la codificación que llevará
la reclamación:
Y finalmente iintroducimos la descripción de
la reclamación y aceptamos.
Postventa Página 51 de 81

Guía de usuario Sigrid – Portal Postventa
De esta manera por defecto al dar de alta el parte viene relleno los campos indicados, obra y
unidad postventa de la que procede la reclamación, propietario y persona de contacto indicada
en la Unidad Postventa, fecha y hora de registro de la reclamación y la descripción del problema
(descripción de la reclamación), todos estos datos podrán ser modificados, salvo la obra que no
será editable.
Habrá que indicar el tipo de reclamación, clase, forma de comunicación, urgencia y descripción
del problema.
Postventa Página 52 de 81

Guía de usuario Sigrid – Portal Postventa
Diagnóstico
Para poder evaluar las acciones a realizar para cerrar una reclamación se deberá realizar un
diagnóstico de la reclamación recibida, para ello, desde cada reclamación se analizará los datos
recibidos de propietarios/dirección facultativa, valorando la urgencia, clase de reclamación y el
problema por parte de la persona designada por la empresa a tal fin.
Este diagnóstico es preliminar, para admitir la reclamación a trámite o rechazarla, atendiendo a
los criterios de la empresa para este propósito. Mediante carpetas de consulta se podrán atender
a incidencias registradas y filtrar por urgencias.
El resto de consultas de reclamaciones nos servirán para seguir la evolución de las mismas.
Una vez estudiado el problema podemos dar con tres casos:
- Necesitar más información para su valoración, para lo cual emplearemos tareas para
registrar las solicitudes con el propietario/dirección facultativa que se explicará en el
apartado de seguimiento de reclamaciones en el punto 5 del presente documento.
- Rechazar la reclamación por no procedente mediante cambio de estado.
- Admitir la reclamación a trámite mediante cambio de estado.
En el caso de rechazar una reclamación se mandará un correo al propietatio/DF donde les indicará
el motivo de rechazo y quedará grabado en la ventana de conversaciones del concepto y se
visualizará desde el portal.
Para ello previamente hemos debido rellenar la pestaña de motivos de rechazo:
Postventa Página 53 de 81

Guía de usuario Sigrid – Portal Postventa
Existen tres posibilidades:
- O bien seleccionar un motivo por defecto definido por la empresa (se pueden seleccionar
varios a la vez)
Presionando en seleccionar, nos abrirá la ventana para añadir los motivos predefinidos:
Estos motivos se pueden ampliar, si habitualmente hay que escribir a mano un motivo
que no está en la lista, se le comunica al responsable de postventa para que los añada a
la lista de motivos.
- escribir manualmente el motivo del rechazo, es un campo de texto libre donde el técnico
puede escribir tanto como quiera.
- O mezclar el motivo por defecto con algún comentario manual
Postventa Página 54 de 81

Guía de usuario Sigrid – Portal Postventa
No es necesario ir reclamación por reclamación, rechazando, es importante dejar previamente
indicados los motivos de rechazo y empleando la consulta:
Nos listará todas las reclamaciones con motivos de rechazo, para poder seleccionarlas todas y
realizar el cambio de estado de forma masiva:
Se abrirá una ventana de configuración del
envío de correo, donde se podrá seleccionar
si enviar el correo o no, para simplemente
hacer un cambio de estado a No procedente.
Si se realiza el cambio de estado para una
única reclamación, se podrá indicar el motivo
de rechazo en esta ventana, si es masivo no
se rellenará puesto que tomará los definidos
dentro de la reclamación.
Se podrán adjuntar archivos a enviar (ojo de
forma masiva los mandará a todos los
propietarios seleccionados y se podrán
mandar con copia a otros usuarios.
Los envíos se realizarán a la persona de
contacto de la reclamación y correos
alternativos.
Postventa Página 55 de 81

Guía de usuario Sigrid – Portal Postventa
Al pasar a pendiente estaremos admitiendo la incidencia a trámite, y forma automática el pro-
grama generará una tarea de reparación por cada proveedor interviniente en la reclamación, por
lo que es importante antes de pasar a pendiente una reclamación observar que en la pestaña
intervinientes están todos los oficios que van a intervenir en la reparación:
Al realizar el cambio de estado buscará a los proveedores subcontratistas de esta pestaña y nos
indicará las tareas que va a crear:
Presionamos en Aceptar, generará las tareas que veremos en la pestaña de seguimiento.
Postventa Página 56 de 81

Guía de usuario Sigrid – Portal Postventa
Asignación de oficios
La asignación de oficios se realizará sólo para aquellas reclamaciones que vayan a ser admitidas
a trámite, es decir pasarán a Pendientes. Para establecer los intervinientes para dicha reclama-
ción.
Desde esta pestaña se visualizará los oficios y proveedores seleccionados que existan en la obra,
si se quiere añadir un nuevo oficio/proveedor habrá que hacerlo primero en la obra.
Oficio: Código del oficio.
Descripción Oficio: Descripción del oficio.
Proveedor: Código del proveedor que hemos asociado para este oficio en la obra.
Nombre Proveedor: Descripción del proveedor que hemos asociado para este oficio en
la obra.
Causante de la avería: Marca informativa para determinar el proveedor causante de la
avería para después obtener estadísticas y establecer cargos.
Añadir: Botón que abre una ventana de multiselección con todos los oficios que figuran en la
obra que lleva en cabecera la reclamación. Para filtrar con el campo autofiltro se introducirán los
datos de descripción del proveedor desde el campo autofiltro.
Eliminar: Elimina la línea/s seleccionada/s de oficio del parte de reclamación.
Postventa Página 57 de 81

Guía de usuario Sigrid – Portal Postventa
Creación de Tareas
Las tareas servirán como herramienta para coordinar las distintas necesidades para resolver la
reclamación, diferenciando entre tareas para propietarios (se visualizarán desde el portal para la
interacción con el propietario/DF), tareas para proveedores o incluso tareas internas para realizar
por trabajadores propios de la empresa.
Estas tareas vendrán predefinidas por la empresa con cuales se van a trabajar, cada tarea será
para un único proveedor/propietario/recurso.
Desde la pestaña de Seguimiento de la reclamación, será desde donde se visualice el avance de
la misma hasta su resolución.
Desde aquí podremos seguir la estadística de avance de cada reclamación:
Árbol de tareas: Mostrará cada Tarea que tiene grabada la reclamación.
Fec.ini.est: Mostrará la fecha en la que se ha comunicado la tarea al propietario/proveedor
o recurso.
Fec.fin est: Mostrará la fecha en la que se ha completado la tarea por parte del propieta-
rio/proveedor o recurso.
Duración: Tiempo en días que se ha tardado en completar la tarea
%Completado: Indica la situación de la tarea, un 0% indica que está pendiente, entre
1%-99% indica que está en curso (en proceso), y un 100% indica que está completada.
Fecha límite: Sirve para poner plazos para comprobar que las tareas se van gestionando
en plazos. Existen consultas de tareas que han superado la fecha límite, para saber cuáles
deberían estar terminadas para que comiencen otras o para ver que se cumplen los plazos.
Empleado: Identifica que empleado de Ruesma es el responsable de gestionar la Tarea.
Estado: Indica el estado de la Tarea.
Postventa Página 58 de 81

Guía de usuario Sigrid – Portal Postventa
Los campos de trabajo en postventa serán los siguientes en general para todo tipo de tareas:
Tarea Padre: Tarea de la que depende.
Empleado responsable: Persona a la que se ha asignado la responsabilidad de la ejecución de la
tarea. El empleado responsable de un empleado puede pertenecer a otra empresa.
Contrato de compra asociado: Contrato asociado a esta tarea.
Pedido de compra asociado: Pedido asociado a esta tarea.
Pedido de venta asociado: Pedido asociado a esta tarea.
Parte de reclamación asociado: Parte de reclamación al que pertenece la tarea.
Clasificación de la tarea: Clasificaciones con las que se pueden determinar las tareas definidas en la
tabla auxiliar Clasificación de tareas, dentro del apartado Obras.
Duración (Ejemplo: 5, 5d, 5d3h...): Especifica la cantidad de tiempo necesaria para completar la
tarea seleccionada. Puede indicar la duración en unidades, días u horas.
Fecha de comienzo: Especifica la fecha de comienzo programada de la tarea.
Bloquear fecha: Para que al re-calcular precedencias no se pierdan las fechas introducidas
por el usuario.
Fecha de finalización: Especifica la fecha de fin programada de la tarea.
Postventa Página 59 de 81

Guía de usuario Sigrid – Portal Postventa
Bloquear fecha: Para que al re-calcular precedencias no se pierdan las fechas introducidas
por el usuario.
Fecha límite: Fecha que especifica que la tarea no debe finalizar después de la misma.
Prioridad (1-100, 50=prioridad normal): Cuanto mayor sea el número, mayor será la prioridad de la
tarea y con más atención se intentará evitar su demora.
% Completada (0-100%): Porcentaje para indicar 0 si no se ha iniciado la tarea y 100% si está com-
pletada.
Para aquellas tareas que sean especificas para proveedor o recurso de la empresa:
Es importante aclarar que una tarea solo se empleará para un único Oficio y proveedor, si el
proveedor no está dado de alta en la Subpestaña de oficios de la obra, no se podrá seleccionar y
se tendrá que ir a dicha pestaña para darlo de alta y poder seleccionarlo desde esta ventana.
Oficio: Código del oficio asociado, permite seleccionar aquellos oficios definidos en la subpestaña
de Oficios de la obra a la que pertenece el parte de reclamación y por ende la tarea.
Descripción Oficio: Descripción del oficio asociado, permite seleccionar aquellos oficios definidos
en la subpestaña de Oficios de la obra a la que pertenece el parte de reclamación y por ende la
tarea.
Proveedor: Código del proveedor asociado al oficio seleccionado.
Descripción Proveedor: Descripción del proveedor asociado al oficio seleccionado.
Recurso: Código del recurso que va a realizar la tarea.
Nombre Recurso: Nombre del recurso que va a realizar la tarea.
Postventa Página 60 de 81

Guía de usuario Sigrid – Portal Postventa
Para tareas de tipo cita o reparación ya sean de propietario, proveedor o Recurso:
Fechaacordada: Campo para indicar la fecha acordada de las citas asociadas a proveedor o propie-
tario.
:
Hora acordada Campo para indicar la hora acordada de las citas asociadas a proveedor o propie-
tario.
En principio en Ruesma, los trabajadores propios serán también un proveedor llamado Ruesma,
por lo que no se emplearán Conceptos de tipo recurso.
Postventa Página 61 de 81

Guía de usuario Sigrid – Portal Postventa
Creación de Tareas manuales
Para crear las tareas se podrá realizar de forma manual en la línea de edición en la parte inferior
de la ventana, escribiendo el resumen de como se llamará la tarea, al saltar de campo pedirá la
serie para especificar la tarea que se da de alta:
Quedando registrada la tarea la ventana de seguimiento.
El concepto creado llevará código, descripción, parte de reclamación asociado y estado nada más.
Postventa Página 62 de 81

Guía de usuario Sigrid – Portal Postventa
Creación masiva de tareas
Para facilitar la labor de los técnicos de postventa, mediante el botón de acciones de la ventana
de seguimiento de la reclamación podremos dar de alta las tareas de forma masiva para los
intervinientes de la reclamación (propietarios, proveedores), se darán varias tareas de alta según
las selecciones que el usuario tome, pero solo se pueden utilizar estas acciones por reclamación,
no varias reclamaciones simultáneas.
Estas acciones están previamente configuradas para atender al tipo de tarea que voy a emplear
con cada interviniente.
En el caso de proveedores será tan sencillo como lanzar la acción y aparecerá una ventana de
dialogo para seleccionar que tareas se quieren dar de alta de forma masiva para la reclamación
clicando sobre el cuadro junto a la tarea:
Creando una tarea de cada tipo que quedarán asociadas a la ventana de seguimiento.
Y dichas tareas ya tendrán asociados el empleado responsable de la tarea, que será quien lanza
la acción.
Postventa Página 63 de 81

Guía de usuario Sigrid – Portal Postventa
En el caso de tareas para proveedores haremos lo mismo, pero en este caso la ventana de dialogo
nos muestra la lista de proveedores que figuran en la pestaña intervinientes de la reclamación y
las tareas predefinidas para proveedores que marcaremos con una S en aquellas que se quieran
dar de alta:
Las nuevas tareas dadas de alta grabarán la misma información que las tareas de propietarios,
añadiendo en la pestaña de Desglose Recursos/Trabajos de la tarea el oficio y proveedor de cada
tarea.
Añadiendo al nombre de la tarea el del proveedor para localizarlas fácilmente.
NOTA: Como ya se ha visto anteriormente, las reparaciones están configuradas para que se
creen de forma automática cuando una reclamación pasa a Pendiente, por lo que solo será
necesario añadir nuevas tareas cuando queramos ampliar el seguimiento.
Postventa Página 64 de 81

Guía de usuario Sigrid – Portal Postventa
5. Método de seguimiento de reclamaciones
En este apartado se explican las diversas tareas a emplear para resolver reclamaciones en su
cronología temporal atendiendo al siguiente diagrama:
Diagnóstico
El flujo de trabajo atenderá a estudiar las necesidades de la reclamación, atendiendo a la infor-
mación facilitada por el propietario/DF.
Disponer de la información necesaria para emitir un juicio o evaluación para poder admitir a
trámite una reclamación.
Registro de Reclamaciones, revisión inicial
En este punto las reclamaciones se encuentran en un estado inicial ya bien sean registradas a
través del portal, introducidas manualmente o importadas en Sigrid.
Mediante carpetas de consulta se podrá atendiendo a su urgencia y siempre veremos organizadas
por fechas las reclamaciones, visualizando las más antiguas primero.
Urgencias registradas: Cualquier urgencia en estado inicial, han sido registradas a través
de Sigrid o el portal y no han sido atendidas.
Reclamaciones registradas urgentes: Cualquier urgencia en estado inicial, han sido
registradas a través de Sigrid o el portal, atendiendo a las clases de urgencia definidas por
la empresa y no han sido atendidas.
Reclamaciones registradas urgentes Críticas: Cualquier urgencia en estado inicial,
han sido registradas a través de Sigrid o el portal, atendiendo a las clases de urgencia
definidas por la empresa y no han sido atendidas en el plazo de días que la empresa quiere
que estas reclamaciones sean tratadas.
Postventa Página 65 de 81

Guía de usuario Sigrid – Portal Postventa
El primer paso será revisar la información registrada en Sigrid. Habrá que prestar atención a los
datos de la reclamación:
La clase de reclamación nos indicará a que periodo pertenece, y tiene que estar bien
categorizada como filtro atendiendo a las fechas de garantía para aceptar o rechazar la misma.
La urgencia tiene que revisarse para saber si es veraz, y darle prioridad a la reclamación.
La descripción del problema nos indicará cual es el motivo de la reclamación a atender.
Solicitud de más información
Tras revisar la reclamación será el filtro para admitir a trámite o rechazar una reclamación y
alcanzamos la primera pregunta ¿Necesito más información? Analizando los datos recibidos
se entrará en un bucle de toma de decisiones.
En caso de no necesitar más información y estar claro el problema se procederá a emitir la
evaluación de la reclamación.
Si necesito información se creará la primera tarea para solicitar más información al propietario
bien manualmente o bien mediante la creación masiva de tareas al propietario explicado en el
apartado de Creación de Tareas del punto 4.
Postventa Página 66 de 81

Guía de usuario Sigrid – Portal Postventa
El flujo a seguir por este tipo de tareas será el siguiente:
Será una comunicación entre el usuario de Sigrid y
el propietario a través del portal de postventa.
Tras la creación de la tarea, el propietario no la
visualizará para ello se realizará un cambio de
estado para grabar la fecha de cuando se ha
solicitado la información.
Solicitada la información el desde Sigrid constará
como información solicitada y en el portal será
información solicitada, donde tomará las acciones
necesarias hasta enviar la información requerida,
quedando en el portal como Información enviada e
inforamción recibida en Sigrid. Si el propietario no
contesta se le podrá volver a solicitar la
información para volver a enviarle un email de
aviso.
La descripción de la tarea nos servirá para definir que le solicitamos al propietario, o darle
recomendaciones para no agravar el daño.
Postventa Página 67 de 81

Guía de usuario Sigrid – Portal Postventa
Para hacer llegar esta petición al propietario solo tendremos que realizar un cambio de estado:
Que lanzará una ventana de diálogo para confirmar el envío de correo al propietario para avisarle
de que se le está solicitando información, si no se quiere enviar el correo, desmarcando el check
de envíos no se realizará la notificación vía email, pero si visualizará en el portal que le estamos
solicitando.
Postventa Página 68 de 81

Guía de usuario Sigrid – Portal Postventa
Se podrán adjuntar documentos, hacer envíos con copia oculta, etc. los parámetos de envío tales
como direcciones de email, asunto, cuerpo y demás vendrán especificados en la parte inferior de
la ventana.
Es importante recalcar, que el envío se realiza a la persona de contacto de la reclamación y a lo
correos adicionales facilitados por el propietario que figuren en dicha reclamación. Además, esta
acción grabará la fecha de envío de la solicitud al propietario:
Si se desee indicar una fecha límite, por ejemplo días se puede dejar indicado en el campo Fecha
límite de la tarea para advertir al propietario que la reclamación no se puede dejar abierta
indefinidamente si no hay respuesta por su parte. Mediante carpetas de consulta o autoejecución
se podrá controlar si un propietario contesta o no en plazos o hay que insistir en la solicitud.
Postventa Página 69 de 81

Guía de usuario Sigrid – Portal Postventa
Desde el portal el propietario podrá visualizar la tarea con las directrices solicitadas:
Reconocerá las tareas pendientes donde tiene que aportar información porque tendrán un círculo
rojo y al desplegar la misma verá que se le solicita y el botón para mandar la información.
El detalle coincidirá con la descripción larga de la tarea, podrá ampliar la descripción del problema
del parte de reclamación, quedando registrado a continuación del texto ya existente en este
campo y podrá asociar nuevas fotos (esta opción siempre estará habilitada desde la pestaña de
datos de la reclamación).
Una vez presione en Enviar Información, esto grabará los datos en Sigrid y cambiará de estado
la tarea y grabará la fecha de fin de la tarea y
Si el propietario no contesta en un plazo fijado por la empresa, desde La consulta tareas que han
supertado la fecha límite podremos ver que tareas se han solicitado y no han sido contestadas
para volver a solicitarlas. Esto se realizará mediante un cambio de estado de las tareas.
Cuando un propietario conteste desde el portal, mediante carpeta de consulta podremos
visualizar las tareas recibidas:
Obviamente este paso se puede saltar atendiendo a una llamada telefónica que no dejará registro
y el tiempo de respuesta no estará justificado en el sistema.
Postventa Página 70 de 81

Guía de usuario Sigrid – Portal Postventa
Asignación de Oficios
En este apartado se introducirán los oficios necesarios en la reclamación como se explica en el
apartado 4 del presente documento y se crearán las tareas necesarias por cualquiera de los
métodos explicados en el mismo.
Confirmación de la tramitación
En este apartado teniendo toda la información disponible se establecerá si se admite a trámite la
reclamación o se rechaza:
En este punto se tomarán decisiones para saber si se necesita una visita técnica para profundizar
en la raíz del problema y posterior peritaje para explicar al propietario los pasos a seguir y repa-
raciones a realizar, o no es necesario y se manda a los oficios las reparaciones a realizar con un
parte a rellenar que devolverán firmado tras la reparación, y la necesidad de realizar pedidos de
compra a oficios y valorar las reclamaciones o presentar precios de venta por peticiones adicio-
nales a la reparación que no cubre la garantía.
Para ello mediante cambio de estado tomaremos uno de los dos caminos, en caso de rechazar
está reclamación quedará cerrada y no se podrán tomar más medidas sobre ella y en caso de
admitir a trámite se pasará a la siguiente tarea. Previo a admitir incidencias a trámite se indicaras
los oficios intervinientes para subsanar dichas reclamaciones.
Al rechazar se podrá omitir enviar el email como ya se ha explicado con anterioridad o al aceptar
y pasar a pendiente se crearán las tareas de reparación necesarias por cada oficio para cerrar el
parte.
Postventa Página 71 de 81

Guía de usuario Sigrid – Portal Postventa
Coordinación de Citas
En función del camino escogido para resolver la reclamación, si se ha valorado la necesidad de
realizar citas se emplearán las tareas de tipo CITA para establecer citas con propietarios, pro-
veedores o peritos en caso de ser necesario, una por cada interviniente.
El flujo de las citas responderá al siguiente esquema:
Donde se establecerá una cita, pactada con el proveedor.
En principio no hay interacción con el proveedor ni desde
Sigrid ni desde el portal postventa, por lo que se realizará
por fuera del sistema pudiendo registrar los avances en Si-
grid para controlar los tiempos de respuesta.
Por este motivo, en el caso de citas con proveedores se
podrá saltar directamente a la confirmación de la cita desde
su estado inicial.
En el caso de propietarios si se interactuará a través del
portal de postventa atendiendo a un flujo similar:
Desde la creación de la tarea se enviará al propietario un
correo para que visualice la cita y de su conformidad con la
misma.
Aceptadas las citas por parte de proveedores y propietarios se confirmará la cita a ambos.
En caso de no acudir o pedir cancelar la cita por alguno de ellos quedará registro del retraso y
volverá a comenzar el proceso.
Si la cita se realiza se pasa a la siguiente tarea y dejamos constancia de la realización de la
misma.
Postventa Página 72 de 81

Guía de usuario Sigrid – Portal Postventa
Desde la reclamación en la pestaña de seguimiento desde el botón Acciones con la acción
Establecer Cita se podrá poner esta fecha de forma masiva en todas las tareas que
seleccionemos de forma simultánea:
O bien desde un listado en la ventana principal a través de una consulta con la misma acción:
Esta acción abrirá una ventana de dialogo para introducir la fecha y hora para la cita de forma
masiva a todas las tareas seleccionadas:
El siguiente paso tras asociar las citas será comunicarlo a las partes intervininetes. Para realizar
el envío se podrá hacer desde la tarea y de forma masiva seleccionando las tareas desde la
pestaña de seguimiento de la reclamación o una consulta desde la ventana principal de Sigrid y
ejecutando un cambio de estado:
Postventa Página 73 de 81

Guía de usuario Sigrid – Portal Postventa
Este proceso lanzará una ventana de diálogo para enviar un email en caso de propietario a la
persona de contacto de la reclamación y emails alternativos de la reclamación en caso de existir,
y en el caso de proveedor a la persona de contacto del mismo que tenga como cargo el de
responsable de postventa o en caso de no tener al correo indicado en envío de correos de la ficha
del proveedor.
Además, grabará la fecha de envío en el campo Fec. Ini. est de la tarea
Postventa Página 74 de 81

Guía de usuario Sigrid – Portal Postventa
En el caso de citas con propietarios emplearán el portal y confirmarán o cancelarán la cita desde
el portal:
En el caso de proveedores se realizará manualmente desde Sigrid, mediante cambio de estado,
que grabará el proceso de avance, para conocer su situación.
En este punto cualquiera de los intervinientes puede cancelar la cita, desde el portal lo realizará
el propietario, o manualmente al proveedor desde Sigrid.
En este caso volveríamos a concretar citas volviendo a seguir los pasos iniciales.
Postventa Página 75 de 81

Guía de usuario Sigrid – Portal Postventa
Si la cita se realiza, lo indicaremos en Sigrid mediante cambio de estado para dejar la cita como
realizada, y quedará grabada la fecha de la cita y la tarea en situación completada.
Postventa Página 76 de 81

Guía de usuario Sigrid – Portal Postventa
Preparación de Trabajos
Coordinación de Equipos y Necesidades (Partes de Trabajo)
En este punto se procederá a dividir los trabajos a realizar por cada oficio o recurso interno, para
ello se deberá generar una tarea para cada uno de ellos atendiendo al siguiente flujo:
Este será un apartado de las tareas de Reparación, donde informaremos a cada proveedor de la
reparación a realizar enviando un parte de trabajo y cuando la reparación esté completada nos
devolverán el parte relleno y firmado.
Con las tareas ya creadas, se introducirá en cada tarea la labor a realizar por el proveedor y se
podrán enviar desde la propia tarea realizando un cambio de estado:
Postventa Página 77 de 81

Guía de usuario Sigrid – Portal Postventa
En la ventana de dialogo de envío del parte se verán los siguientes datos:
El informe de Parte a seleccionar para realizar el envío, el remitente será el usuario que lanza el
proceso y el destinatario la persona de contacto del proveedor con el cargo especificado de
postventa.
Así como el asunto y plantilla HTML para el envío.
En caso de querer hacer un envío masivo, se filtrarán las tareas a enviar desde la ventana
principal de Sigrid con una consulta:
En este caso, se generará un único email para el proveedor seleccionado generando un parte de
trabajo único para dicho proveedor con todas las reclamaciones que tiene que atender,
desglosadas primero por obra, vivienda y reclamación que quedará asociado en cada tarea:
Postventa Página 78 de 81

Guía de usuario Sigrid – Portal Postventa
Cuando la reparación haya sido realizada por parte del proveedor devolverá el parte firmado por
el propietario y el encargado de realizar la reparación, se asociará con cada reclamación y se
darán por terminadas mediante cambio de estado las tareas mediante cambio de estado.
Postventa Página 79 de 81

Guía de usuario Sigrid – Portal Postventa
Pedidos
Los pedidos podrán ser tanto de compra para proveedores como de venta para propietarios, para
ello las tareas llevan asociado el pedido de compra o venta relacionado.
Se gestionará desde el propio documento de compra o venta y simplemente se relacionará con
la tarea.
Postventa Página 80 de 81

Guía de usuario Sigrid – Portal Postventa
Reparación
Coordinar Citas de Reparación
Las citas de reparación funcionarán exactamente igual que las citas de visita técnica, pero para
coordinar los trabajos de reparación.
Informes de Reparación – Recepción de Partes de Trabajo
Una vez se reciban los partes de trabajo realizados por los proveedores se asociarán al concepto
de la tarea, cerrando la tarea indicando que está terminada:
Cuando todas las tareas de reparación estén completadas se cerrará la reclamación.
Tendremos 3 opciones:
-Si nos hemos equivocado y hemos pasado a pendiente una reclamación para rechazar, nos
permitirá rechazarla comportandose como anteriormente se ha explicado.
-Si la reclamación tiene todas las reparaciones realizadas, deberá tener los partes firmados
asociados, en caso de no estar firmados se cambiará de estado a Pasar a terminada, y hasta que
el parte no esté firmado no se cerrará
-En caso de tener todas las reparaciones firmadas por parte del cliente la reclamación se dará
por cerrada.
Una vez cerrada la reclamación habrá terminado la labor del técnico.
Postventa Página 81 de 81