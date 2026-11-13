# 2. Primeros pasos: roles, navegación, firma electrónica

**Cuenta: `admin`, luego `meca`**

## El panel de control

1. Inicie sesión con `admin`.
2. El panel de control muestra 8 indicadores. Cada uno es clicable y abre la lista filtrada correspondiente:
    - vencimientos vencidos (incluidos los en tolerancia) y por planificar;
    - defectos abiertos y aplazamientos fuera de plazo;
    - AD/SB por evaluar;
    - paquetes de trabajo activos y task cards pendientes de inspección;
    - solicitudes de piezas, cuarentena, herramientas fuera de calibración y autorizaciones que caducan.
3. La tabla **Flota** indica para cada aeronave sus contadores, la validez del ARC y el número de vencimientos.

**A comprobar**: la línea F-HDMB muestra vencimientos vencidos; F-HDMD está «En mantenimiento».

## Navegación

- El menú de la izquierda está organizado por área de actividad: CAMO, Part-145, Logística, Calidad, Ayuda.
- La **búsqueda global** (en la parte superior) encuentra una matrícula, un P/N, un S/N, un WP, una task card, una AD. Pruebe `DEMO-S3502`: accederá directamente a la ficha del cubo del rotor de F-HDMB.
- Cada lista tiene un buscador y filtros.

## Los roles

1. Cierre la sesión e inicie sesión de nuevo con `meca`.
2. Abra **Flota** y, a continuación, F-HDMA: la ficha es consultable, pero los botones «Modificar» y «Toma de configuración» ya no aparecen.
3. Escriba en la barra de direcciones `/flotte/aeronefs/1/modifier/`: AHMIS responde «403 Prohibido».

Los roles limitan el acceso a las pantallas. El tutorial 21 muestra la segunda barrera: las autorizaciones individuales de firma.

## La firma electrónica

Toda acción reglamentaria (paso de task card, ejecución, inspección, aplazamiento de defecto, CRS) exige **volver a introducir la contraseña**. AHMIS registra entonces:

- la identidad y la licencia del firmante;
- la marca de tiempo;
- la declaración firmada;
- una **huella SHA-256**, que permite detectar cualquier alteración posterior (insignia «✓ íntegra»).

Una firma no puede modificarse ni eliminarse. Una contraseña incorrecta provoca el rechazo de la firma.

## Nada se borra

Los registros de aeronavegabilidad no pueden eliminarse, ni siquiera por el administrador. Se utilizan estados («anulado», «retirado», «dado de baja»). Cada modificación se registra campo por campo en el **registro de auditoría** (tutorial 22).
