# 32. Matriz de cumplimiento reglamentario

Esta matriz relaciona los principales requisitos de EASA con las funciones de AHMIS. Sirve de base para el expediente de presentación a la autoridad.

> **Importante**: un software no es «conforme» por sí solo. Es la organización (CAMO, Part-145) la que demuestra su cumplimiento ante la autoridad (en Francia, la DSAC; en España, la AESA). Lo hace describiendo la herramienta y su uso en sus procedimientos (CAME, MOE), validándola y auditándola. La columna «A realizar por la organización» enumera lo que queda a su cargo. Las referencias reglamentarias que figuran a continuación son orientativas: verifíquelas en los textos en vigor.

## Aeronavegabilidad (Part-CAMO / Part-M)

| Requisito | Función AHMIS | Cobertura | A realizar por la organización |
|---|---|---|---|
| Programa de mantenimiento aprobado | Programa por tipo, intervalos FH/ciclos/calendario, umbrales, tolerancias, efectividad, revisión AMP, historial de revisiones | ✅ | Introducir el programa aprobado (MSM/MPD), verificación de la introducción por una 2.ª persona |
| Tolerancias no acumulativas | Realización en tolerancia: siguiente vencimiento contado desde el límite teórico; fuera de tolerancia registrado; tolerancia prohibida en ALS/CMR, referenciada en AD (tutorial 25) | ✅ | Definir las tolerancias autorizadas en el programa |
| Revisión periódica del programa (M.A.302(g)) | Revisión por tipo al menos cada 12 meses, examen de fiabilidad y nuevas instrucciones, enmienda aprobada, alerta en el panel de control, historial (tutorial 27) | ✅ | Procedimiento de revisión y de aprobación indirecta en la CAME |
| Seguimiento de las directivas de aeronavegabilidad | Registro AD/SB, evaluación por aeronave con justificación, tareas de seguimiento, plazo a partir de la entrada en vigor, estado actualizado al realizarse | ✅ | Vigilancia de AD (EASA, FAA, fabricante) e introducción |
| Limitaciones de aeronavegabilidad, LLP | Límites de vida FH/ciclos/días, trazabilidad «back-to-birth», vencimientos LLP, rechazo del montaje en el límite | ✅ | Tomar el historial completo de las LLP al incorporar a la flota |
| Potenciales (TBO) | Vencimientos TBO, contadores TSO/CSO | ✅ | — |
| Registros de aeronavegabilidad | Horas/ciclos registrados, realizaciones, configuración, componentes, CRS, ninguna eliminación posible | ✅ | Copias de seguridad |
| Periodos de conservación (M.A.305(h), 145.A.55(c)) | Reglas de conservación por naturaleza, fecha de retirada de la aeronave, informe de los registros vencidos, eliminación masiva bloqueada mientras no se alcance el periodo (tutorial 30) | ✅ | Procedimiento de archivo / depuración documentado |
| Estado de las modificaciones y reparaciones (M.A.305) | Registro específico: clasificación, base de aprobación, incorporación, ICA e integración en el programa, pesada y manual de vuelo, alertas en los vencimientos (tutorial 26) | ✅ | Clasificación y aprobación de las modificaciones (Part-21) |
| Transferencia de los registros (M.A.307) | Archivo completo del expediente (resumen HTML, JSON, CSV, manifiesto SHA-256), acuse de recibo, control de integridad de un expediente recibido (tutorial 30) | ✅ | Procedimiento de transferencia con la nueva organización |
| Revisión de aeronavegabilidad / ARC | Registro ARC, alerta de caducidad, ficha de aeronave sintética | ✅ | Procedimiento de revisión, personal ARS habilitado |
| Defectos aplazados | Aplazamiento MEL/CDL firmado, límites, integrado en los vencimientos | ✅ | Introducir la MEL del operador |
| Prórroga de aplazamientos (RIE) | Una sola prórroga, categorías B y C, aprobada y firmada por la CAMO antes del vencimiento, duración ≤ intervalo inicial, autoridad informada (tutorial 31) | ✅ | Procedimiento RIE aceptado por la autoridad |

## Mantenimiento (Part-145)

| Requisito | Función AHMIS | Cobertura | A realizar por la organización |
|---|---|---|---|
| Datos de mantenimiento | Task cards generadas a partir del programa, con pasos y referencias | ✅ | Contenido técnico procedente de los datos del fabricante bajo licencia |
| Hojas de trabajo, firma de cada paso | Pasos firmados individualmente, valores medidos, N/A | ✅ | — |
| Personal certificador y autorizaciones | Licencia Part-66, autorizaciones por tipo, categoría y validez, suspensión, comprobación en cada firma | ✅ | Gestión de las autorizaciones (procedimiento MOE) |
| Inspección independiente (tareas críticas) | Segunda firma obligatoria por otra persona certificadora | ✅ | Identificar las tareas críticas en el programa |
| Certificado de aptitud para el servicio | CRS firmado electrónicamente, bloqueos automáticos, mención de los aplazamientos, categoría C para una gran revisión | ✅ | Texto del CRS que debe alinearse con la MOE |
| Herramientas calibradas | Calibración, retirada prohibida si está vencida, trazabilidad de los usos | ✅ | — |
| Aceptación de componentes | Recepción con certificado, comprobación en la recepción, cuarentena automática, piezas sospechosas | ✅ | — |
| Clases de artículos (145.A.42(a)) | Clase por P/N (elemento, pieza estándar, materia, consumible); Form 1 exigido para un elemento, norma exigida para una pieza estándar o una materia (tutorial 31) | ✅ | Clasificar el catálogo P/N |
| Piezas no recuperables (145.A.42(d)) | Baja firmada con mutilación y testigo, estado definitivo (tutorial 31) | ✅ | Procedimiento de mutilación |
| Experiencia reciente (145.A.35) | 6 meses de 24 calculados a partir de las firmas AHMIS y las experiencias declaradas, bloqueante para el personal certificador (tutorial 28) | ✅ | Declarar la experiencia anterior de los recién llegados |
| Factores humanos, formaciones | Formaciones por categoría, categorías obligatorias bloqueantes (factores humanos, formación continua), otras caducidades señaladas | ✅ | Programa de formación continua |
| Notificación de sucesos (376/2014, 145.A.60) | Notificación por todo el personal, confidencialidad, plazo de 72 h, seguimiento a 30 días, titular del diseño, cierre, alertas (tutorial 29) | ✅ | Notificación a la autoridad (ECCAIRS) y análisis; AHMIS no transmite automáticamente |

## Sistemas informáticos, registros electrónicos, seguridad de la información

| Requisito | Función AHMIS | Cobertura | A realizar por la organización |
|---|---|---|---|
| Integridad y trazabilidad de los registros | Registro de auditoría de solo escritura, campo por campo, eliminación prohibida | ✅ | — |
| Firma electrónica | Reintroducción de la contraseña, identidad y licencia, marca de tiempo, huella SHA-256, no modificable | ✅ | Hacer aceptar a la autoridad el procedimiento de firma |
| Control de acceso | Roles por área de actividad + autorizaciones individuales | ✅ | Cuentas nominativas, revisión periódica de los derechos |
| Seguridad de la información (Part-IS) | Base técnica: autenticación, trazabilidad | ⚠️ parcial | Análisis de riesgos, alojamiento seguro (HTTPS), copias de seguridad, plan de continuidad, gestión de incidentes |
| Validación del software | 89 pruebas automáticas sobre las reglas críticas | ⚠️ parcial | Plan de validación formal, aceptación por los expertos de aeronavegabilidad, gestión de versiones |

## Limitaciones conocidas de esta versión

- **Una sola unidad de ciclos** por aeronave (ciclos o aterrizajes). Los ciclos de motor específicos (NG/NF, arranques) no se controlan por separado.
- Sin registro vuelo a vuelo: las horas se introducen por informe (diario o por vuelo).
- Sin importación automática de los datos del fabricante (MSM, MRI, IPC) ni de las AD: la introducción es manual.
- Cualificación de categoría (A/B1/B2) de la task card: orientativa, no bloqueante para la ejecución. La autorización en el tipo y los derechos de certificación sí son bloqueantes.
- Sin módulo financiero (costes, facturación, compras a proveedores).
- Datos de demostración únicamente en francés (la interfaz y los tutoriales también están disponibles en inglés, español y alemán).

Estos puntos son vías de evolución, que se priorizarán según sus necesidades.
