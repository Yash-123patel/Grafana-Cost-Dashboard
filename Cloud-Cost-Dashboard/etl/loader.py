from psycopg.types.json import Json

from common.logger import logger
from etl.database import get_connection


class BillingLoader:

    def load(self, records):

        if not records:
            logger.warning("No billing records to load.")
            return

        conn = None

        try:

            conn = get_connection()

            query = """
            INSERT INTO cloud_billing
            (
                billing_date,
                cloud_provider,

                account_id,
                account_name,

                service,
                region,

                usage_quantity,
                usage_unit,

                cost,
                currency,

                scope_type,

                operation,
                usage_type,
                availability_zone,

                resource_id,
                resource_name,

                environment,
                project,
                owner,

                tags
            )
            VALUES
            (
                %s,%s,
                %s,%s,
                %s,%s,
                %s,%s,
                %s,%s,
                %s,
                %s,%s,%s,
                %s,%s,
                %s,%s,%s,
                %s
            )
            ON CONFLICT
            (
                billing_date,
                cloud_provider,
                account_id,
                service,
                region,
                resource_id,
                operation
            )
            DO UPDATE SET

                usage_quantity     = EXCLUDED.usage_quantity,
                usage_unit         = EXCLUDED.usage_unit,
                cost               = EXCLUDED.cost,
                currency           = EXCLUDED.currency,

                environment        = EXCLUDED.environment,
                project            = EXCLUDED.project,
                owner              = EXCLUDED.owner,

                tags               = EXCLUDED.tags;
            """

            values = [

                (

                    r.billing_date,
                    r.cloud_provider,

                    r.account_id,
                    r.account_name,

                    r.service,
                    r.region,

                    r.usage_quantity,
                    r.usage_unit,

                    r.cost,
                    r.currency,

                    r.scope_type,

                    r.operation,
                    r.usage_type,
                    r.availability_zone,

                    r.resource_id,
                    r.resource_name,

                    r.environment,
                    r.project,
                    r.owner,

                    Json(r.tags),

                )

                for r in records

            ]

            logger.info("Loading %s billing records...", len(records))

            with conn.cursor() as cur:
                cur.executemany(query, values)

            conn.commit()

            logger.info(
                "Successfully loaded %s billing records.",
                len(records),
            )

        except Exception:

            if conn:
                conn.rollback()

            logger.exception("Failed to load billing records.")

            raise

        finally:

            if conn:
                conn.close()