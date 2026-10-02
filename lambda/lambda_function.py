import csv
import io
import json
import os

import boto3
import psycopg2
from psycopg2.extras import execute_batch


def convertir_lista_json(valor):
    """Convierte texto separado por comas en una lista JSON."""
    if valor is None or valor.strip() == "":
        return json.dumps([])

    elementos = [item.strip() for item in valor.split(",") if item.strip()]
    return json.dumps(elementos)


def convertir_entero(valor):
    """Convierte valores vacíos a None y los demás a entero."""
    if valor is None or str(valor).strip() == "":
        return None

    return int(float(valor))


def lambda_handler(event, context):

    conn = None

    try:
        # ---------------------------------------
        # 1. Variables de entorno
        # ---------------------------------------
        bucket = os.environ["S3_BUCKET"]
        key = os.environ["S3_KEY"]

        rds_host = os.environ["RDS_HOST"]
        rds_port = int(os.environ.get("RDS_PORT", "5432"))
        rds_db = os.environ.get("RDS_DB", "postgres")
        rds_user = os.environ["RDS_USER"]
        rds_password = os.environ["RDS_PASSWORD"]

        # ---------------------------------------
        # 2. Leer CSV desde Amazon S3
        # ---------------------------------------
        s3 = boto3.client("s3")

        response = s3.get_object(
            Bucket=bucket,
            Key=key
        )

        contenido = response["Body"].read().decode("utf-8-sig")

        reader = csv.DictReader(io.StringIO(contenido))
        registros = list(reader)

        print(f"Registros leídos desde S3: {len(registros)}")

        # ---------------------------------------
        # 3. Transformar registros
        # ---------------------------------------
        datos_transformados = []

        for fila in registros:

            datos_transformados.append(
                (
                    fila["fsq_place_id"],
                    fila["name"],
                    float(fila["latitude"]),
                    float(fila["longitude"]),
                    convertir_entero(fila["distance"]),
                    fila["primary_category"],
                    fila["primary_category_id"],
                    convertir_lista_json(fila["categories"]),
                    convertir_lista_json(fila["category_ids"]),
                    fila["address"],
                    fila["LocNombre"]
                )
            )

        print(f"Registros transformados: {len(datos_transformados)}")

        # ---------------------------------------
        # 4. Conectar con PostgreSQL en RDS
        # ---------------------------------------
        conn = psycopg2.connect(
            host=rds_host,
            port=rds_port,
            dbname=rds_db,
            user=rds_user,
            password=rds_password,
            sslmode="require",
            connect_timeout=10
        )

        cursor = conn.cursor()

        # ---------------------------------------
        # 5. UPSERT idempotente
        # ---------------------------------------
        upsert_sql = """
            INSERT INTO cafeterias_teusaquillo (
                fsq_place_id,
                name,
                latitude,
                longitude,
                distance_m,
                primary_category,
                primary_category_id,
                categories,
                category_ids,
                address,
                localidad
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s::jsonb, %s::jsonb, %s, %s
            )
            ON CONFLICT (fsq_place_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                distance_m = EXCLUDED.distance_m,
                primary_category = EXCLUDED.primary_category,
                primary_category_id = EXCLUDED.primary_category_id,
                categories = EXCLUDED.categories,
                category_ids = EXCLUDED.category_ids,
                address = EXCLUDED.address,
                localidad = EXCLUDED.localidad,
                fecha_carga = CURRENT_TIMESTAMP;
        """

        execute_batch(
            cursor,
            upsert_sql,
            datos_transformados,
            page_size=100
        )

        conn.commit()

        # ---------------------------------------
        # 6. Verificar conteo
        # ---------------------------------------
        cursor.execute(
            "SELECT COUNT(*) FROM cafeterias_teusaquillo;"
        )

        total = cursor.fetchone()[0]

        print(f"Total de registros en RDS: {total}")

        cursor.close()
        conn.close()

        return {
            "statusCode": 200,
            "registros_leidos": len(registros),
            "registros_procesados": len(datos_transformados),
            "total_registros_rds": total
        }

    except Exception as e:

        if conn is not None:
            conn.rollback()
            conn.close()

        print(f"ERROR: {str(e)}")

        return {
            "statusCode": 500,
            "error": str(e)
        }