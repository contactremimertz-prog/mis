# 31. Prórroga de aplazamientos, piezas no recuperables, clases de artículos

## A. Prórroga única de un aplazamiento (RIE)

**Cuenta: `camo`**

La MEL permite, para las categorías **B y C**, **una sola** prórroga del intervalo de rectificación (RIE). La aprueba la CAMO **antes del vencimiento**, por una duración como máximo igual al intervalo inicial, y se informa a la autoridad.

1. Menú **Defectos y aplazamientos** → **DEF-...-0002** (F-HDMC, iluminación de cabina, cat. C, límite D+10).
2. Marco **Prorrogar el plazo (RIE)**: nuevo límite (fecha) D+20, referencia RIE `RIE-2026-001`, justificación `Ampoule en commande, livraison J+12`. Marque «autoridad informada» si se ha hecho. Contraseña → **Aprobar y firmar la prórroga**.

**Resultado**: el nuevo límite se utiliza en todas partes (vencimientos, planificación, panel de control). La ficha muestra el límite inicial, el aprobador y la referencia, y se añade una firma «Prórroga de aplazamiento (RIE)».

**Comprobaciones**:

| Caso | Resultado |
|---|---|
| Nuevo límite más allá de D+20 (intervalo inicial 10 d) | Rechazo: «Prórroga (fecha) superior al intervalo inicial» |
| Añadir un criterio ausente del aplazamiento inicial (p. ej., FH) | Rechazo |
| Segunda prórroga | Rechazo: «una segunda prórroga está prohibida» |
| Límite ya alcanzado | Rechazo: «debe aprobarse antes del vencimiento» |
| Categoría A, D o fuera de MEL | Rechazo |
| Usuario no CAMO (p. ej., `b2`) | Marco no mostrado, acción rechazada |

## B. Pieza no recuperable: baja

**Cuenta: `magasin`**

Una pieza no recuperable (LLP en su límite, no reparable, dañada, trazabilidad insuficiente) debe **mutilarse** para que nunca pueda volver al circuito de suministro (145.A.42(d), M.A.504(d)).

1. Menú **Componentes** → un componente desmontado, en estado «No utilizable» o «Cuarentena».
2. Marco **Dar de baja (pieza no recuperable)**: fecha, motivo, método de mutilación (`Découpe`), testigo (`Isabelle GARNIER (qualité)`), ref. del certificado de destrucción. Contraseña → **Firmar la baja definitiva**.

**Resultado**: estado **Dado de baja**, definitivo. El estado ya no puede cambiar, ni por la pantalla, ni por la administración, ni por la API. Ejemplo en la demo: el cubo del rotor `DEMO-S3399`, en su límite de vida.

Una pieza instalada o reservada no puede darse de baja.

## C. Clases de artículos (145.A.42(a))

**Cuenta: `magasin`**

Cada referencia P/N tiene una **clase**, que determina el justificante exigido en la recepción:

| Clase | Justificante aceptado | Ejemplo de la demo |
|---|---|---|
| Elemento (component) | EASA Form 1, FAA 8130-3, doble liberación, TCCA Form One | Motores, BTP, filtro de aceite, tapón magnético |
| Pieza estándar | Certificado de conformidad (CoC), norma obligatoria | Junta tórica `AS568-012` |
| Materia prima | CoC, especificación obligatoria | Alambre de frenado `MS20995C32` |
| Consumible | CoC | Aceite, grasa |

**Prueba**: menú **Recepción** → P/N `DEMO-350FLT-01` (filtro, elemento) con un certificado «Certificado de conformidad» → rechazo: «se exige un certificado de aptitud autorizado …». La misma prueba con `DEMO-OIL-T2` (consumible) se acepta.

Una referencia con número de serie, rotable o de vida limitada es necesariamente un elemento.
