import time
import yaml

from aws.extractor import AWSExtractor
from common.logger import logger
from config.settings import (
    START_DATE,
    END_DATE,
    AWS_REGION,
)
from etl.loader import BillingLoader


def load_accounts():
    """
    Load cloud account configuration from accounts.yaml.
    """

    with open("config/accounts.yaml", "r") as file:
        return yaml.safe_load(file)


def run_aws():
    """
    Process all configured AWS accounts.

    Supports:
    - standalone AWS accounts
    - AWS Organization / Tower accounts
    """

    config = load_accounts()

    aws_accounts = config.get("aws", [])

    loader = BillingLoader()

    processed_accounts = 0
    failed_accounts = 0
    total_records = 0

    for account in aws_accounts:

        account_name = account.get("account_name")
        profile = account.get("profile")

        # Default account type is standalone
        account_type = account.get(
            "account_type",
            "standalone",
        )

        # Skip disabled accounts
        if not account.get("enabled", True):

            logger.info(
                "Skipping disabled AWS account : %s",
                account_name,
            )

            continue

        try:

            logger.info("=" * 80)

            logger.info(
                "Processing AWS Account : %s",
                account_name,
            )

            logger.info(
                "AWS Profile : %s",
                profile,
            )

            logger.info(
                "Account Type : %s",
                account_type,
            )

            logger.info("=" * 80)

            # Create AWS extractor
            extractor = AWSExtractor(
                profile=profile,
                account_name=account_name,
                region=AWS_REGION,
                account_type=account_type,
            )

            # Extract billing records
            records = extractor.extract(
                start_date=START_DATE,
                end_date=END_DATE,
            )

            # Load records into database
            if records:

                loader.load(records)

                total_records += len(records)

                logger.info(
                    "Records loaded for %s : %s",
                    account_name,
                    len(records),
                )

            else:

                logger.warning(
                    "No billing records found for : %s",
                    account_name,
                )

            processed_accounts += 1

            logger.info(
                "Completed AWS Account : %s",
                account_name,
            )

        except Exception:

            failed_accounts += 1

            logger.exception(
                "Failed processing AWS account : %s",
                account_name,
            )

    return (
        processed_accounts,
        failed_accounts,
        total_records,
    )


def main():

    start_time = time.time()

    logger.info("=" * 80)
    logger.info("Cloud Cost Dashboard ETL Started")
    logger.info("=" * 80)

    logger.info(
        "Billing Period : %s to %s",
        START_DATE,
        END_DATE,
    )

    # Run AWS ETL
    processed, failed, records = run_aws()

    execution_time = round(
        time.time() - start_time,
        2,
    )

    logger.info("=" * 80)
    logger.info("ETL Summary")
    logger.info("=" * 80)

    logger.info(
        "Accounts Processed : %s",
        processed,
    )

    logger.info(
        "Accounts Failed    : %s",
        failed,
    )

    logger.info(
        "Records Loaded     : %s",
        records,
    )

    logger.info(
        "Execution Time     : %s sec",
        execution_time,
    )

    logger.info("=" * 80)

    if failed > 0:

        logger.warning(
            "Cloud Cost Dashboard ETL Completed with failures"
        )

    else:

        logger.info(
            "Cloud Cost Dashboard ETL Completed Successfully"
        )


if __name__ == "__main__":
    main()