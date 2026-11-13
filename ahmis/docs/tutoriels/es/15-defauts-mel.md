# 15. Defectos y aplazamientos (MEL / CDL)

**Cuentas: `meca`, `b2`, `planif`**

## 1. Notificar un defecto

1. Cuenta `meca` → abra **F-HDMA** → **Notificar un defecto**.
2. Fuente «Informe de tripulación (techlog)», ref. techlog `CRM MA-150`, ATA `33`, descripción `Feu anticollision inférieur inopérant`.
3. **Guardar**: el defecto recibe un número `DEF-AAAA-NNNN`, en el estado **Abierto**.

## 2. Aplazar según la MEL

El aplazamiento exige una **autorización certificadora** en el tipo.

1. Cuenta `b2` → menú **Defectos y aplazamientos** → abra el defecto.
2. Marco **Aplazar según la MEL / CDL**:
    - Referencia MEL `MEL 33-40-01 (DEMO)`
    - Categoría `C (10 jours)`; deje el límite vacío para el plazo estándar
    - Procedimientos `Placard INOP apposé, vol de jour uniquement`
    - Contraseña → **Firmar el aplazamiento**

**Resultado**:

- el defecto queda **Aplazado**, límite = hoy + 10 días;
- aparece en los **Vencimientos** de F-HDMA (naturaleza «Defecto aplazado») y en la planificación;
- si sigue aplazado en el momento de un CRS, queda **citado en la declaración del CRS**.

Plazos estándar: B = 3 días, C = 10 días, D = 120 días. Para la categoría A o fuera de MEL, introduzca el límite (fecha, horas o ciclos).

**Comprobaciones**: sin referencia MEL, o sin ningún límite, se rechaza el aplazamiento. El formulario de aplazamiento no se ofrece a un mecánico no certificador.

Una **prórroga única** del plazo (RIE) puede aprobarla después la CAMO, antes del vencimiento: véase el tutorial 31.

## 3. Rectificar

1. Cuenta `planif` → abra el defecto → **Crear la task card de rectificación** en un WP existente o «+ Nuevo WP de reparación de averías».
2. Ejecute la task card (tutorial 12). Al cerrarla, el defecto pasa a **Rectificado**.

## Ejemplo ya cargado

F-HDMC (H135) tiene un defecto **aplazado** de categoría C (iluminación de cabina): véalo en sus vencimientos y en su ficha.
