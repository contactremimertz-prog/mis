# 18. Solicitudes de piezas

**Cuentas: `meca`, luego `magasin`**

## 1. Solicitar una pieza desde una task card

1. Cuenta `meca` → task card **Visite 100 h / 12 mois** de F-HDMD.
2. Marco **Piezas** → «Solicitar una pieza»: P/N `DEMO-ORING-12`, cantidad `2`, prioridad «Urgente» → **Solicitar**.

Se crea una solicitud `DP-AAAA-NNNN` en el estado **Solicitada**. Aparece en el panel de control («Solicitudes de piezas») y en el menú **Solicitudes de piezas**.

## 2. Entregar (almacén)

1. Cuenta `magasin` → menú **Solicitudes de piezas** → filtro «Solicitada».
2. Abra la solicitud de **tapón magnético** `DEMO-CHIP-01` (creada por la demo).
3. Lote a entregar: `LOT-CH-09` → **Entregar**.

**Resultado**:

- la solicitud queda **Entregada**;
- el stock del lote disminuye en 1, con un movimiento de salida vinculado a la task card;
- en la task card aparece la línea «Consumido» (trazabilidad pieza → trabajos).

Para una **pieza con número de serie**, el componente pasa a «Reservado (task card)». Solo puede montarse entonces mediante esa task card (tutorial 14).

## Comprobaciones en la entrega

Solo se proponen las piezas **utilizables** del P/N solicitado o de un P/N **intercambiable**. En la entrega, AHMIS vuelve a verificar:

- el certificado aceptado;
- la caducidad (se rechaza un lote caducado);
- el potencial restante (para una pieza con número de serie);
- la cantidad disponible.

## Anular

Una solicitud innecesaria se anula desde su ficha (**Anular la solicitud**). Una task card no puede firmarse mientras una solicitud permanezca «Solicitada».

## Stock mínimo

En **Almacén de consumibles**, una cantidad inferior o igual al stock mínimo se muestra en rojo (p. ej., juntas tóricas `LOT-OR-077`). **Inventario** permite un ajuste justificado (+/−), registrado como movimiento de stock.
