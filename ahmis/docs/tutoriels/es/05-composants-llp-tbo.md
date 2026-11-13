# 5. Componentes, piezas de vida limitada (LLP) y TBO

**Cuenta: `camo`**

## Referencias de artículos (P/N)

Menú **Referencias P/N** → haga clic en `DEMO-350STR-01` (cubo del rotor principal NH90). Una referencia incluye:

- el seguimiento por número de serie (obligatorio para una LLP o una pieza con TBO);
- los **límites de vida** (LLP), desde nuevo: horas, ciclos y/o días;
- el **TBO**, potencial entre revisiones generales: horas, ciclos y/o días;
- los tipos de aeronave aplicables (se rechaza el montaje en otro tipo);
- los P/N intercambiables (aceptados en una solicitud de pieza).

AHMIS rechaza una LLP sin límite, y una LLP o pieza con TBO sin número de serie.

## Ficha de componente: el cubo del rotor de F-HDMB

1. Búsqueda global: `DEMO-S3502`.
2. La ficha muestra:
    - los contadores TSN / CSN / TSO / CSO;
    - **Potenciales y límites de vida**: límite, consumido, restante y una barra que pasa a naranja al 90 %;
    - los certificados de aptitud;
    - la **trazabilidad «back-to-birth»**: cada montaje (aeronave, posición, contadores en el montaje y en el desmontaje, motivo, task card).

**A comprobar**: quedan aproximadamente 40 FH sobre el límite de 5 000 FH. En **Vencimientos**, la línea «LLP» de F-HDMB está «Por planificar».

## Lectura de la configuración de una aeronave

Abra F-HDMA, sección **Configuración instalada**: para cada posición (MOT 1, MOT 2, BTP, BTA, MRH, PALE 1-4…), el componente, sus contadores y lo que le queda en cada límite.

## LLP y TBO en los vencimientos

AHMIS genera automáticamente un vencimiento:

- **LLP** para cada pieza de vida limitada instalada (primer criterio alcanzado entre horas, ciclos y calendario);
- **TBO** para cada pieza con potencial.

Aparecen en los vencimientos, la previsión y la planificación, y pueden añadirse a un paquete de trabajo: se genera entonces una task card de «desmontaje/montaje».

## Una pieza en su límite es inutilizable

Una pieza que ha alcanzado un límite no puede montarse, entregarse ni volver a declararse «utilizable». La prueba automática `test_expired_life_part_refused` lo verifica.
