---
name: matriz-doc-fise
description: Llena automáticamente la Matriz Excel FISE de Carrigas Perú extrayendo datos del SCANFILE 1 (PDF con Checklist + TIV SUNARP + DNI). Usar SIEMPRE que el usuario presente un PDF de SCANFILE 1 junto con un Excel MATRIZ_A_RELLENAR.xlsx, o mencione "MATRIZ DOC FISE", "llenar la matriz", "procesar SCANFILE", "expediente FISE", "conversión GNV", "conversión GLP" o cualquier combinación de estos términos. Este proceso es frecuente y debe ejecutarse de forma rígida siguiendo todas las reglas sin excepción.
---

# MATRIZ DOC FISE — Carrigas Perú E.I.R.L.

Llenar la Matriz Excel FISE a partir del SCANFILE 1. Proceso rígido: sigue TODAS las
reglas sin excepción. La hoja `DATOS` es la hoja maestra — casi todas las demás hojas
(PROF., DECLARACIÒN., COND. DE DEVOLUCION, CHECK, CARTILLA GNV, GARANTIA) se llenan
solas mediante fórmulas que apuntan a `DATOS`.

> **PLANTILLA v2 (julio 2026).** En esta versión la celda `G46` de
> **COND. DE DEVOLUCION PN** ya NO es una fecha fija: ahora es la fórmula `=DATOS!B25`
> (igual que en COND. DE DEVOLUCION PJ). Por eso es OBLIGATORIO llenar `DATOS!B25`
> con la fecha de ingreso del vehículo y NO tocar la celda G46 de ninguna de las dos
> hojas de condiciones de devolución.

## Entradas requeridas

1. **SCANFILE 1** — un solo PDF que contiene, en cualquier orden:
   - **CHECKLIST COMERCIAL GNV/GLP**: celular, correo, kilometraje, cantidad de
     cilindros, ubicación y capacidad de cada cilindro (galones y litros), kit
     GNV/marca (5TA), precio de conversión, descuento GLP, fecha de ingreso del vehículo.
   - **TIV SUNARP** (Tarjeta de Identificación Vehicular): placa, marca, modelo, año
     modelo, color, categoría, cilindrada, combustible, número de VIN/serie, partida registral.
   - **DNI del solicitante** (ambas caras): apellidos y prenombres, número de DNI (CUI),
     dirección, distrito/provincia/departamento.
2. **MATRIZ_A_RELLENAR.xlsx** — la plantilla vigente (v2). El usuario la adjunta en
   cada conversación junto con el SCANFILE 1. Si NO la adjunta, usa la copia incluida
   en `assets/MATRIZ_A_RELLENAR_v2.xlsx` y avísale que usaste la plantilla embebida.
3. **Correlativo** (opcional) — número de 4 dígitos del expediente (ej. `0354`). Si el
   usuario no lo indica, pregúntalo UNA sola vez; si no lo da, deja el que trae la plantilla
   y adviértelo al final.

## Procedimiento (siempre en este orden)

1. **Lee el PDF completo** (las 3 secciones). Si falta alguna de las 3 secciones,
   detente y dilo — no inventes datos.
2. **Extrae los datos** y construye el JSON con el formato exacto de
   `references/mapeo_celdas.md` (sección "Formato del JSON").
3. **Ejecuta el script determinista** — NUNCA edites el Excel a mano celda por celda:
   ```
   python scripts/llenar_matriz.py MATRIZ_A_RELLENAR.xlsx datos.json salida.xlsx
   ```
   El script llena `DATOS`, el correlativo, las fechas literales y la DECLARACIÒN,
   valida los campos obligatorios y edita el XML interno del xlsx directamente, de
   modo que los logos, firmas e imágenes de la plantilla se conservan intactos
   (NUNCA abrir y re-guardar la plantilla con openpyxl: borra las imágenes).
4. **Nombra el archivo de salida**: `MATRIZ_<PLACA-sin-guion>_<correlativo>.xlsx`
   (ej. `MATRIZ_A5O309_0354.xlsx`).
5. **Verifica** (el script lo reporta): placa, DNI de 8 dígitos, fecha en B25,
   correlativo aplicado. Entrega el archivo y resume en 3-4 líneas qué se llenó.

## Reglas de datos (sin excepción)

- **DNI**: SIEMPRE texto de 8 dígitos, conservando ceros a la izquierda (ej. `06998954`,
  nunca `6998954`).
- **Placa**: en formato del TIV con guion (ej. `A5O-309`) para las celdas; sin guion
  solo en el nombre del archivo.
- **Nombre del solicitante**: apellidos + prenombres tal como figuran en el DNI, en
  MAYÚSCULAS (ej. `VALENZUELA BRUNO MARIA DEL ROSARIO`).
- **Distrito/Provincia/Departamento**: formato `DEPARTAMENTO / PROVINCIA / DISTRITO`
  según el DNI (ej. `LIMA / LIMA / SAN LUIS`).
- **Fechas**: la fecha de ingreso viene del checklist en `DD/MM/YYYY`. `DATOS!B25` se
  escribe como fecha real de Excel; las demás fechas literales van como texto `DD/MM/YYYY`.
- **Garantía** (`DATOS!B45`): fecha de ingreso + 1 año, formato `DD/MM/YYYY`.
- **Capacidades con 2 cilindros**: usar el formato suma: galones `2+2`, litros `28+28`.
  Con 1 cilindro: valores simples (`4`, `55`).
- **Descuento GLP**: si el checklist lo deja vacío, escribir `0`.
- **Kilometraje y precio**: números sin comas ni símbolo de moneda.
- **Persona jurídica**: si el solicitante es una empresa (tiene RUC), llenar también
  `B9` (RUC), `B13` (representante legal) y `B14` (DNI del rep. legal); si es persona
  natural, dejarlos vacíos.
- **Datos del taller** (`B2:B5`) y **responsable de conversión** (`B36`): NO tocarlos,
  ya vienen en la plantilla.
- **NO tocar** `COND. DE DEVOLUCION PN!G46` ni `COND. DE DEVOLUCION PJ!G46` (fórmulas
  en la plantilla v2), ni ninguna otra celda con fórmula salvo las que el script
  sobreescribe expresamente.

## Referencias

- `references/mapeo_celdas.md` — mapeo completo celda ↔ dato, formato del JSON de
  entrada y lista de celdas literales fuera de DATOS. Léelo si necesitas verificar o
  corregir algo puntual.
