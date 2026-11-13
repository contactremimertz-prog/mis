# 30. Conservación y transferencia de expedientes

**Cuentas: `qualite`, `camo`**

## Parte A: conservación de los registros

Los registros tienen periodos mínimos de conservación:

| Registros | Periodo mínimo | Referencia |
|---|---|---|
| Paquetes de trabajo, task cards, CRS, defectos | 36 meses tras la puesta en servicio | 145.A.55(c), M.A.305(h) |
| Realizaciones de tareas | 36 meses, y hasta su sustitución por una realización más reciente | M.A.305(h) |
| Tiempos totales, estado de las AD, LLP, modificaciones, montajes / desmontajes | 12 meses tras la retirada definitiva de la aeronave (o del componente) | M.A.305(h)(1) |
| Expediente del personal | 3 años tras la salida | 145.A.35(j) |
| ARC, revisiones del programa, calibraciones, notificaciones de sucesos | 36 meses | CAMO.A.220, 145.A.55 |

**AHMIS nunca elimina nada automáticamente.** Rechaza toda eliminación individual y rechaza también una eliminación masiva (administración, script) de un registro que aún esté sujeto a obligación de conservación.

### 1. Informe de conservación

Cuenta `qualite` → menú **Conservación de los registros**. Para cada naturaleza de registro, el informe muestra el total y, a continuación, tres recuentos:

- **sin vencimiento**: a conservar, por ejemplo para una aeronave aún en explotación;
- **en curso**: periodo mínimo no alcanzado;
- **vencidos**: archivables, mediante decisión documentada según la MOE o la CAME.

Hay disponible una exportación CSV por línea. En la demo, están vencidos: el helicóptero **F-HDMZ** (retirado hace 20 meses) y sus horas de vuelo, así como el antiguo empleado **Paul ANCIEN** (salió hace 4 años).

### 2. Retirar una aeronave del servicio

Ficha de la aeronave → **Modificar** → estado «Retirada» y **retirada definitiva del servicio el**. La fecha es obligatoria para una aeronave retirada y está prohibida en los demás casos. Hace que comience a contar el plazo de 12 meses. La aeronave sale de los vencimientos y del panel de control, y su ficha muestra la fecha de fin de conservación.

Para una salida de personal: ficha de personal → desmarque «activo» e indique **salida de la organización el**.

## Parte B: transferencia del expediente de una aeronave (M.A.307)

Cuando una aeronave cambia de CAMO o de propietario, sus registros de aeronavegabilidad se transfieren a la nueva organización.

### 3. Transferencia saliente

1. Cuenta `camo` → ficha **F-HDMA** → **Exportar el expediente**.
2. Sentido «Transferencia saliente (nueva organización / propietario)», organización `CAMO Héli Nord (DEMO)`, aprobación `FR.CAMO.0999`, motivo `Changement de gestionnaire de navigabilité` → **Guardar**.

**Resultado**: AHMIS genera el archivo `dossier-F-HDMA-TR-....zip` y lo conserva con su huella SHA-256:

- `synthese.html`: estado de aeronavegabilidad imprimible (tiempos totales, vencimientos, componentes, LLP y TBO, AD, modificaciones, defectos aplazados);
- `dossier.json` y `csv/`: todos los datos (horas, realizaciones, montajes / desmontajes, certificados, paquetes de trabajo, task cards, firmas con su huella);
- `manifest.json`: huella de cada archivo.

Cuando la nueva organización confirme la recepción, utilice **Registrar el acuse de recibo** en la ficha de la transferencia. La demo contiene la transferencia de F-HDMZ al adquirente de la célula, ya con acuse de recibo.

### 4. Transferencia entrante

Menú **Transferencias de expedientes** → **+ Crear** → sentido «Transferencia entrante (expediente recibido)» y, a continuación, adjunte el archivo recibido. AHMIS comprueba las huellas del manifiesto:

- archivo íntegro: aviso verde;
- archivo modificado, ausente o añadido, o expediente de otro MSN: aviso **ANOMALÍA** con el detalle.

La toma de datos se realiza después mediante el registro manual (tutorial 3).

Los archivos de transferencia solo pueden descargarse con el derecho «ver las transferencias» (CAMO, calidad), nunca mediante el enlace genérico de archivos adjuntos.
