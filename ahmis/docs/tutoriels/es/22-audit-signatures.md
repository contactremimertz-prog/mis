# 22. Registro de auditoría y firmas electrónicas

**Cuenta: `qualite`**

## Registro de auditoría

Menú **Registro de auditoría**: cada creación, modificación o eliminación técnica se registra con:

- la marca de tiempo y el usuario;
- el registro afectado;
- **cada campo modificado**, con su valor anterior y su nuevo valor.

El registro es de **solo escritura**: ninguna entrada puede modificarse ni eliminarse, ni siquiera por el administrador.

**Ejercicios**

1. Búsqueda `F-HDMA`: todas las operaciones sobre esta aeronave, incluidos los incrementos de contadores.
2. Filtro «Tipo de registro = tarea de mantenimiento»: el historial de revisiones del programa.
3. En una ficha (aeronave, componente, task card, WP, defecto), el botón **Historial** muestra las modificaciones **y** las firmas de ese registro.

## Firmas electrónicas

Menú **Firmas electrónicas**: todas las firmas, filtrables por acción (ejecución, inspección, CRS, aplazamiento…).

Cada firma contiene el nombre, la licencia en el momento de la firma, la declaración firmada, la marca de tiempo y una **huella SHA-256** calculada sobre el conjunto.

La insignia **«✓ íntegra»** significa que la huella recalculada coincide. Si un dato se modificara directamente en la base de datos, fuera de AHMIS, la insignia pasaría a **«⚠ alterada»**. La prueba automática `test_signature_is_immutable_and_tamper_evident` lo demuestra.

## Qué se conserva

- Ningún registro de aeronavegabilidad puede eliminarse: aeronaves, componentes, tareas, realizaciones, task cards, WP, defectos, certificados, registros de horas…
- Se utilizan estados: anulado, retirado, dado de baja, inactivo.
- Los periodos de conservación reglamentarios dependen de sus procedimientos (CAME / MOE) y de la copia de seguridad de la base de datos (tutorial 23).
