# Mapeo de celdas — MATRIZ FISE (plantilla v2, julio 2026)

La hoja `DATOS` es la maestra. Las hojas PROF., DECLARACIÒN., COND. DE DEVOLUCION
PN/PJ, CHECK, CARTILLA GNV, CARTILLA GNV (2) y GARANTIA se alimentan de `DATOS`
mediante fórmulas — no se tocan salvo las celdas literales listadas al final.

## Hoja DATOS (celdas a llenar)

| Celda | Dato | Fuente | Ejemplo |
|-------|------|--------|---------|
| B8  | Nombre del solicitante / razón social | DNI (apellidos + prenombres) | `VALENZUELA BRUNO MARIA DEL ROSARIO` |
| B9  | RUC (solo persona jurídica) | usuario/checklist | vacío para PN |
| B10 | Dirección | DNI | `RIO MOQUEGUA 272` |
| B11 | Distrito/Provincia/Departamento | DNI, formato `DEP / PROV / DIST` | `LIMA / LIMA / SAN LUIS` |
| B12 | DNI/CE — texto 8 dígitos, conserva cero inicial | DNI (CUI) | `06998954` |
| B13 | Representante legal (solo PJ) | usuario | vacío para PN |
| B14 | DNI rep. legal (solo PJ) | usuario | vacío para PN |
| B15 | Celular | Checklist | `991021538` |
| B16 | Marca y modelo | TIV (`MARCA MODELO`) | `NISSAN X-TRAIL` |
| B17 | Marca | TIV | `NISSAN` |
| B18 | Modelo | TIV | `X-TRAIL` |
| B19 | Año (año modelo) | TIV | `2010` |
| B20 | Placa (con guion) | TIV | `A5O-309` |
| B21 | Color | TIV | `PLATA METALICO` |
| B22 | Combustible actual | TIV | `GASOLINA` o `BI-COMBUSTIBLE GLP` |
| B23 | Cilindrada | TIV | `2.488` |
| B24 | Categoría | TIV | `M1` |
| B25 | **Fecha de ingreso — como FECHA Excel (obligatoria)** | Checklist | `13/07/2026` |
| B26 | Cantidad de cilindros | Checklist | `1` |
| B27 | Ubicación del cilindro | Checklist | `Maletera` |
| B28 | Capacidad de cilindro (litros; con 2: `28+28`) | Checklist | `55` |
| B29 | Galones (con 2: `2+2`) | Checklist | `4` |
| B30 | Litros (igual que B28) | Checklist | `55` |
| B31 | Kit GNV / Marca 5TA | Checklist | `TOMASETTO ACHILLE` |
| B32 | Precio de conversión (número, sin `S/` ni comas) | Checklist | `4000` |
| B33 | Descuento GLP (`0` si vacío) | Checklist | `0` |
| B34 | Kilometraje (número, sin comas) | Checklist | `158001` |
| B35 | Correo | Checklist | `correo@dominio.pe` |
| B37 | Fecha de ingreso como texto `DD/MM/YYYY` (uso interno) | Checklist | `13/07/2026` |
| B45 | Fecha vencimiento garantía = ingreso + 1 año, texto `DD/MM/YYYY` | calculada | `13/07/2027` |
| B46 | Serie VIN | TIV | `JN1TANT31AW000916` |
| B47 | Partida registral | TIV | `51077751` |

**No tocar en DATOS**: B2:B5 (taller), B36 (responsable de conversión), C25/D25/E25
(fórmulas día/mes/año de B25), D21/D22, B38-B44 (tanque/reductor, se llenan a mano
en taller).

**Limpieza**: si la plantilla trae residuos en `C35` (`º`), `E36` (`}`) o `F29`,
vaciarlos.

## Celdas literales fuera de DATOS (las escribe el script)

| Hoja | Celda | Valor |
|------|-------|-------|
| PROF. | J6 | fecha ingreso `DD/MM/YYYY` |
| PROF. | F17 | fórmula `=DATOS!B29` (corrige el `2+2` fijo de la plantilla) |
| PROF. | G22 | fecha ingreso `DD/MM/YYYY` |
| DECLARACIÒN. | C6 | `<NOMBRE>, ` |
| DECLARACIÒN. | K6 | `<DNI 8 dígitos>,` |
| DECLARACIÒN. | H7 | placa |
| DECLARACIÒN. | D11 | `Que el día <D> de <mes en español> de <AAAA>, he entregado correctamente el kit de conversión a GLP, financiado a través del` |
| DECLARACIÒN. | D12 | `Programa FISE, correspondiente al siguiente vehículo:` |
| DECLARACIÒN. | F14 | placa |
| DECLARACIÒN. | F15 | marca |
| DECLARACIÒN. | F16 | modelo |
| DECLARACIÒN. | F17 | año |
| DECLARACIÒN. | F43, F45, H43, H45 | vaciar (datos de tanque aún no existen) |
| COND. DE DEVOLUCION PN | I2 | correlativo 4 dígitos (ej. `0354`) |
| CHECK | C43 | fecha ingreso `DD/MM/YYYY` |
| GARANTIA | C12 | año del vehículo |
| GARANTIA | E20 | fecha ingreso `DD/MM/YYYY` |

**PROHIBIDO**: escribir en `COND. DE DEVOLUCION PN!G46` y `COND. DE DEVOLUCION PJ!G46`
— en la plantilla v2 son `=DATOS!B25` y se calculan solas.

## Formato del JSON de entrada del script

```json
{
  "correlativo": "0354",
  "solicitante": {
    "nombre": "VALENZUELA BRUNO MARIA DEL ROSARIO",
    "dni": "06998954",
    "direccion": "RIO MOQUEGUA 272",
    "dep_prov_dist": "LIMA / LIMA / SAN LUIS",
    "ruc": "", "rep_legal": "", "dni_rep_legal": ""
  },
  "vehiculo": {
    "placa": "A5O-309", "marca": "NISSAN", "modelo": "X-TRAIL",
    "anio": "2010", "color": "PLATA METALICO", "categoria": "M1",
    "cilindrada": "2.488", "combustible": "GASOLINA",
    "vin": "JN1TANT31AW000916", "partida": "51077751"
  },
  "checklist": {
    "celular": "991021538", "correo": "correo@dominio.pe",
    "kilometraje": "158001", "cant_cilindros": 1,
    "ubicacion_cilindro": "Maletera",
    "litros": "55", "galones": "4",
    "kit_marca": "TOMASETTO ACHILLE",
    "precio": "4000", "descuento_glp": "0",
    "fecha_ingreso": "13/07/2026"
  }
}
```

Con 2 cilindros: `"litros": "28+28"`, `"galones": "2+2"`, y en
`"ubicacion_cilindro"` la ubicación (normalmente `MALETERA`).
