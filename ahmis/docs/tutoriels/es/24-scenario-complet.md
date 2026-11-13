# 24. Escenario completo: de la AD vencida al CRS (F-HDMB)

Este escenario encadena los roles en un caso realista. Duración: unos 20 minutos. Parta de una demo restablecida.

**Situación**: en el NH90 F-HDMB, la AD `DEMO-AD-2026-0101` (barras de suspensión BTP) está **vencida** y la revisión de 100 h está **en tolerancia**.

## Paso 1 – CAMO: constatar e inmovilizar (`camo`)

1. Panel de control → línea F-HDMB → vencimientos vencidos.
2. **Vencimientos**, filtro F-HDMB: observe la AD vencida y la revisión de 100 h en tolerancia.
3. Una AD vencida prohíbe el vuelo: abra F-HDMB → **Modificar** → estado **AOG (en tierra)** → **Guardar**. La modificación queda registrada en el historial.

## Paso 2 – Planificación (`planif`)

1. **Vencimientos**, filtro F-HDMB.
2. Marque la AD, la revisión de 100 h y la lubricación `N90-62-050`.
3. Paquete de trabajo: el WP existente **Visite 100 h** → **Crear las task cards**.
4. En el WP → **Modificar**: inicio hoy, fin mañana, estado «Planificado».

## Paso 3 – Ejecución de la revisión (`meca`)

1. Task card **Visite 100 h / 12 mois** → **Iniciar**.
2. Firme los 6 pasos (contraseña cada vez).
3. Retire la herramienta `TENS-01` (tensiómetro) y, a continuación, devuélvala.
4. Informe `Visite 100 h effectuée, RAS`, 7 h.h → **Firmar los trabajos**: la task card queda cerrada.
5. Haga lo mismo con la **lubricación**.

## Paso 4 – Ejecución de la AD (`b1`)

1. Task card **Inspection des barres de suspension BTP (AD)** → **Iniciar** y, a continuación, firme los 4 pasos.
2. Durante la inspección, una anomalía: marco **Notificar un hallazgo**, `Trace de frottement sur barre avant gauche, dans les tolérances du manuel`. Se crean un defecto y una task card de rectificación.
3. Vuelva a la task card de la AD → informe `Inspection conforme à l'AD, constatation traitée sur task card dédiée` → **Firmar los trabajos**. Pasa a «pendiente de inspección»: la tarea es crítica.

## Paso 5 – Hallazgo (`b1`)

Abra la task card de rectificación → **Iniciar** → informe `Mesure de la trace : conforme, protection appliquée` → **Firmar los trabajos**. El defecto queda **rectificado**.

## Paso 6 – Inspección independiente (`certc`)

Task card de la AD → **Firmar la inspección** (observaciones `Conforme`). Queda cerrada.

**A comprobar** (cuenta `camo`):

- **AD / SB** → `DEMO-AD-2026-0101` → F-HDMB: estado **«Aplicable – repetitiva en curso»**, con la fecha y los contadores de cumplimiento;
- **Vencimientos** F-HDMB: la AD está «OK», próximo límite dentro de 110 FH; la revisión de 100 h está «OK».

## Paso 7 – CRS (`b1`)

WP → marco CRS: ya no hay bloqueos → contraseña → **Firmar el CRS**. El WP queda **Puesto en servicio** y bloqueado.

## Paso 8 – Regreso a la explotación (`camo`)

El CRS ha devuelto F-HDMB a **En explotación** automáticamente (lo hace para una aeronave «En mantenimiento» o «AOG»). Compruebe el **panel de control**: F-HDMB ya no tiene vencimientos vencidos, pero el cubo del rotor (LLP) sigue por planificar.

## Paso 9 – Control de calidad (`qualite`)

- **Firmas electrónicas**: todas las firmas del escenario, cada una «✓ íntegra».
- **Registro de auditoría**, búsqueda `F-HDMB`: la inmovilización en tierra, la creación del WP, las task cards, los estados…
- **Imprimir el expediente** del WP: el expediente completo en papel con el CRS.

Enhorabuena, ha recorrido toda la cadena CAMO → Part-145 → logística → calidad.
