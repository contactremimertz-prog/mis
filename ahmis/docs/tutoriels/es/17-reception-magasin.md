# 17. Recepción en almacén y certificados de aptitud

**Cuenta: `magasin`**

Toda pieza entra en AHMIS mediante la **recepción**, con su certificado de aptitud.

## 1. Recibir un consumible

Menú **Recepción**:

- P/N `DEMO-OIL-T2` (aceite de turbina), n.º de lote `LOT-OIL-2701`, cantidad `24`, ubicación `MAG-PRINC`, fecha de caducidad dentro de 2 años (obligatoria para este artículo);
- certificado: tipo «Certificado de conformidad», n.º `COC-5521`, emisor `Distributeur agréé démo`, fecha del día;
- marque las **3 comprobaciones en la recepción** → **Guardar**.

**Resultado**: el lote aparece en **Almacén de consumibles**, «Utilizable», con un movimiento de entrada.

## 2. Recibir una pieza con número de serie

- P/N `DEMO-SG-150` (arrancador-generador), S/N `DEMO-G1700`, cantidad 1, estado «Reparado», TSN `850`, CSN `2400`, TSO `0`, CSO `0`;
- certificado: EASA Form 1, n.º `F1-778`, emisor `Atelier équipements agréé`, n.º de aprobación `FR.145.DEMO-Y`, estado «Reparado»;
- 3 comprobaciones marcadas → **Guardar**.

**Resultado**: se abre la ficha del componente, con su certificado aceptado. La pieza puede entregarse y montarse.

## 3. Recepción no conforme → cuarentena automática

Repita una recepción (S/N `DEMO-G1701`) **sin marcar** «Certificado completo, firmado, emisor aprobado».

**Resultado**: «colocado en CUARENTENA». La pieza se almacena en `QUAR`, su certificado se marca como rechazado y no puede entregarse ni montarse.

## Comprobaciones en el registro

- S/N obligatorio para una pieza con número de serie; cantidad 1.
- Se rechaza un par P/N + S/N ya conocido: «duplicado o pieza sospechosa».
- Fecha de caducidad obligatoria para los artículos de vida de almacenamiento limitada.
- Se rechaza una fecha de certificado futura.
- **Clase del artículo** (ficha P/N, 145.A.42): un **elemento** (component) exige un certificado de aptitud autorizado (EASA Form 1, FAA 8130-3, doble liberación, TCCA Form One). Un certificado de conformidad (CoC) solo se acepta para una pieza estándar, una materia prima o un consumible. Véase el tutorial 31.

## Certificados

Menú **Certificados de aptitud**: todos los Form 1, 8130-3 y CoC. El escaneado del certificado puede adjuntarse (campo «Escaneado del certificado»).
