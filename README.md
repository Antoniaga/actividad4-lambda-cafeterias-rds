# Actividad 4 - Transformación y carga automatizada con AWS Lambda

Proyecto desarrollado para la asignatura Herramientas de Computación en la Nube de la Maestría en Analítica Aplicada.

## Objetivo

Implementar un flujo Serverless que lea datos almacenados en Amazon S3, los transforme mediante AWS Lambda y los cargue en Amazon RDS PostgreSQL usando una estrategia UPSERT idempotente.

## Arquitectura

Amazon S3 → AWS Lambda → Amazon RDS PostgreSQL → CloudWatch Logs

## Fuente de datos

La función Lambda procesa el archivo:

`raw-zone/cafeterias/cafeterias_teusaquillo_limpio.csv`

correspondiente a 46 establecimientos ubicados en Teusaquillo, Bogotá.

## Transformación

Durante la ejecución se realizan las siguientes transformaciones:

- conversión de latitud y longitud a valores numéricos;
- conversión de distancia a entero;
- transformación de `categories` y `category_ids` a JSONB;
- adaptación de `distance` a `distance_m`;
- adaptación de `LocNombre` a `localidad`.

## Carga en RDS

Los datos se cargan en la tabla:

`cafeterias_teusaquillo`

utilizando sentencias parametrizadas y la estrategia:

`ON CONFLICT (fsq_place_id) DO UPDATE`

Esto permite que la función pueda ejecutarse varias veces sin generar registros duplicados.

## Validación de idempotencia

Estado inicial:

- 0 registros en RDS.

Primera ejecución:

- 46 registros leídos desde S3.
- 46 registros transformados.
- 46 registros almacenados en RDS.

Segunda ejecución:

- 46 registros leídos.
- 46 registros transformados.
- 46 registros en RDS.

Verificación adicional:

- 46 registros totales.
- 46 identificadores `fsq_place_id` únicos.

## Monitoreo

CloudWatch Logs registra cada invocación de Lambda, incluyendo:

- duración;
- memoria utilizada;
- estado de ejecución;
- registros procesados.

## Estructura del repositorio

```text
lambda/
    lambda_function.py

data/
docs/
evidencias/
notebooks/
src/

lambda_cafeterias.zip
requirements.txt
.gitignore
README.md