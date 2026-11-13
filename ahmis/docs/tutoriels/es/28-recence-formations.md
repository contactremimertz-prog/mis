# 28. Experiencia reciente y formaciones obligatorias

**Cuentas: `qualite`, `b1`**

145.A.35 impone al personal certificador al menos **6 meses de experiencia** de mantenimiento en los **últimos 24 meses**, así como una formación continua. Los factores humanos se exigen a todo el personal. AHMIS bloquea la firma si falta alguna de estas condiciones.

## 1. Panel «Aptitud para firmar»

Cuenta `qualite` → **Personal y autorizaciones** → **Claire DUBOIS**. El panel indica:

- **Experiencia reciente**: número de meses, de los últimos 24, con al menos una task card ejecutada o inspeccionada en AHMIS, o cubiertos por una experiencia declarada. Se necesitan al menos 6;
- **Formaciones (todo el personal)** y **Formaciones (certificador)**: al día, o la lista de lo que falta;
- para cada tipo autorizado: «puede firmar», o las razones del bloqueo.

## 2. Declarar una experiencia fuera de AHMIS

Para una persona que llega de otra organización, su experiencia pasada no está en AHMIS. Marco **Experiencias declaradas (fuera de AHMIS)**:

1. Del `01/01/2026` al `30/06/2026`, organización `Atelier précédent (DEMO)`, trabajos `Entretien en ligne NH90`, justificante `Attestation employeur`.
2. **Añadir**: los meses cubiertos cuentan en la experiencia reciente.

Se rechaza una experiencia en el futuro, o cuyo fin sea anterior al inicio.

## 3. Formaciones obligatorias

Cada formación tiene una **categoría**: factores humanos, formación continua (145.A.35), EWIS, seguridad de depósitos, formación de tipo, seguridad, otra. Por defecto:

| Personal | Categorías exigidas |
|---|---|
| Todo el personal | Factores humanos |
| Personal certificador | Factores humanos, formación continua |

Solo estas categorías bloquean. Las demás formaciones caducadas se señalan en rojo sin bloquear.

## 4. Verificar el bloqueo

1. Cuenta `qualite` → ficha **Claire DUBOIS** → formación «Formación continua (145.A.35)»: anote su fecha de caducidad.
2. Para probar, añada una ficha de personal de prueba con una autorización certificadora NH90 pero **sin** formación continua.
3. Vincúlela a una cuenta y, a continuación, abra una task card NH90 con esa cuenta: el marco «Firma imposible:» enumera «formación obligatoria ausente o caducada: Formación continua (145.A.35)».

## 5. Parametrización

En el archivo de configuración:

| Variable | Valor por defecto | Función |
|---|---|---|
| `AHMIS_RECENCY_ENFORCE` | `1` | `0` desactiva el control de experiencia reciente |
| `AHMIS_RECENCY_MONTHS` | `6` | Meses de experiencia exigidos |
| `AHMIS_RECENCY_WINDOW_MONTHS` | `24` | Ventana deslizante |
| `AHMIS_TRAINING_REQUIRED_ALL` | `human_factors` | Categorías exigidas a todos |
| `AHMIS_TRAINING_REQUIRED_CERTIFYING` | `human_factors,continuation` | Categorías exigidas al personal certificador |
