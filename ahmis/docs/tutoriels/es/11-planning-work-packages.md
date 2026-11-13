# 11. Planificación y paquetes de trabajo

**Cuenta: `planif`**

Un **paquete de trabajo (WP)** agrupa los trabajos de una aeronave durante una inmovilización: fechas, estación, tipo de revisión y task cards.

## La planificación del hangar

Menú **Planificación**: una línea por aeronave, una columna por día (8 semanas).

- Las **barras** son los WP: azul = planificado, naranja = en curso, verde = puesto en servicio.
- Los **puntos** son los vencimientos: rojo = vencido, naranja = por planificar, gris = previsto.
- Pase el cursor sobre un punto o una barra para ver el detalle; haga clic para abrirlo.
- Botones «← 4 semanas / 4 semanas →» para navegar.

**Localice**: el WP en curso de F-HDMD, el WP planificado de F-HDMB dentro de 5 días y los puntos rojos de F-HDMB (AD vencida).

## Crear un paquete de trabajo

1. **Nuevo paquete de trabajo**.
2. Aeronave `F-HDMA`, título `Visite 100 h`, tipo «Revisión periódica», estación `Base Alpes`, del próximo lunes al martes, estado «Planificado».
3. **Guardar**: el número `WP-AAAA-NNNN` se asigna automáticamente.

## Rellenar el paquete de trabajo

En la ficha del WP:

1. **Añadir elementos vencidos**: la lista propone los vencimientos de la aeronave hasta 30 días después del fin del WP, salvo los ya planificados. Marque `N90-05-100`, `DEMO-AD-2026-0101` y `N90-24-365` → **Crear las task cards seleccionadas**.
2. **Añadir una tarea del programa**: elija una tarea no vencida, por ejemplo `N90-63-200`, para anticiparla.
3. **Trabajo adicional**: una task card fuera de programa, por ejemplo `Remplacement ampoule phare d'atterrissage`, ATA `33`, 0,5 h.h.

**Resultado**:

- cada task card recoge el título, la ATA, la zona, la cualificación, la carga y los **pasos** de la tarea;
- la tarjeta «Carga prevista» del WP totaliza las horas-hombre;
- los elementos añadidos desaparecen de la lista de «elementos vencidos» (sin duplicados).

## Imprimir

**Imprimir el expediente**: el resumen del WP y el CRS en formato papel. Cada task card tiene también su botón **Imprimir**, para los talleres que trabajan en papel.

## Estados de un WP

| Estado | Transición |
|---|---|
| Borrador / Planificado | En la creación |
| En curso | Automáticamente al iniciar la 1.ª task card (la aeronave pasa a «En mantenimiento») |
| Puesto en servicio | Al firmar el CRS (tutorial 16): el WP queda entonces **bloqueado** |
| Anulado | Manualmente, mediante «Modificar» |
