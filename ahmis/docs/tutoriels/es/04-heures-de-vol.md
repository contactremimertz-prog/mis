# 4. Registrar las horas de vuelo y los ciclos

**Cuenta: `planif` (o `b1`)**

Las horas y los aterrizajes (ciclos) proceden de los informes de material (techlog / CRM).

## Registro

1. Panel de control → **Registrar horas de vuelo** (o menú **Horas de vuelo** → **+ Crear**).
2. Aeronave `F-HDMA`, fecha de hoy, horas `1.8`, ciclos `5`, referencia `CRM MA-TEST`.
3. **Guardar**.

Un mensaje muestra los nuevos totales.

## Qué hace AHMIS

- Incrementa los contadores de la **célula**.
- Incrementa los contadores de **todos los componentes instalados**: TSN/CSN (desde nuevo) y TSO/CSO (desde revisión general).
- Recalcula inmediatamente los vencimientos.

**A comprobar**:

1. Abra F-HDMA: las horas totales han aumentado 1,8.
2. En «Configuración instalada», el TSO de la BTP también ha aumentado 1,8 y su «TBO restante» ha disminuido en la misma medida.
3. En los vencimientos, el «Restante FH» de la revisión de 100 h ha bajado 1,8.

## Comprobaciones de registro

- Se rechaza más de 24 h en un día.
- Se rechaza una fecha futura.
- Un registro nunca es modificable: un error se corrige mediante un nuevo registro justificado, y el historial permanece completo (menú **Horas de vuelo**).

## Utilización prevista y fechas previstas

En la ficha de la aeronave, la «utilización prevista» (FH/día, ciclos/día) sirve para convertir las horas restantes en **fecha prevista**. Ejemplo: 12 FH restantes a 1,6 FH/día dan un vencimiento dentro de 7 días. Modifique este valor (botón **Modificar** de la aeronave, cuenta `camo`) para ver cómo se desplazan las fechas previstas.
