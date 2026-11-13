# 16. Certificado de aptitud para el servicio (CRS)

**Cuentas: `b1`, `b2`, `planif`**

El CRS se firma a nivel de **paquete de trabajo**, cuando todos los trabajos han terminado.

## 1. Ver qué lo bloquea

Abra el WP de F-HDMD («Visite 100 h + boroscopie moteurs») → marco **Certificado de aptitud para el servicio**. AHMIS enumera todo lo que impide el CRS, por ejemplo:

- task card no cerrada (y su estado);
- herramienta no devuelta;
- pieza reservada que no se ha montado ni devuelto al almacén.

El botón **Firmar el CRS** permanece desactivado mientras la lista no esté vacía.

## 2. Terminar los trabajos

Si ha seguido los tutoriales 12 a 14, quedan como máximo:

- **Contrôle capacité batterie** (cualificación B2): cuenta `b2` → iniciar, firmar los 3 pasos, firmar los trabajos;
- cualquier task card que haya creado como ejercicio: ciérrela o **aplácela** con un motivo (un aplazamiento no impide el CRS; se menciona en él).

## 3. Firmar el CRS

Cuenta `b1` → WP → contraseña → **Firmar el CRS**.

**Resultado**:

- el WP pasa a **Puesto en servicio (CRS firmado)** y queda **no modificable**;
- F-HDMD vuelve a **En explotación**;
- la declaración CRS se registra con el nombre, la licencia, la fecha, la aprobación de la organización, los contadores de la aeronave, los trabajos aplazados y los defectos aplazados en curso;
- **Imprimir el expediente** muestra el CRS con la referencia de su huella SHA-256.

## Reglas aplicadas

| Regla | Detalle |
|---|---|
| Autorización certificadora válida en el tipo | B1, B2, B3 o C, no suspendida, dentro de sus fechas |
| Licencia Part-66 válida | Fecha de validez no superada |
| Gran revisión («Gran revisión» como tipo de WP) | CRS reservado a la **categoría C** (pruebe con `b1` y luego con `certc`) |
| Mecánico no certificador | Acceso denegado (403) |
