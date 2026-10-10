import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from common.logger import logger
from etl.models import BillingRecord


class AWSExtractor:

    def __init__(
        self,
        profile,
        account_name,
        region="us-east-1",
        account_type="standalone",
    ):

        self.profile = profile
        self.account_name = account_name
        self.region = region
        self.account_type = account_type

        session = boto3.Session(
            profile_name=profile,
        )

        self.ce = session.client(
            "ce",
            region_name=region,
        )

        self.sts = session.client(
            "sts",
        )

        self.account_id = self.sts.get_caller_identity()[
            "Account"
        ]

    def extract(
        self,
        start_date,
        end_date,
    ):

        logger.info("=" * 70)
        logger.info("AWS Profile      : %s", self.profile)
        logger.info("Account          : %s", self.account_name)
        logger.info("Account ID       : %s", self.account_id)
        logger.info("Account Type     : %s", self.account_type)
        logger.info("Start Date       : %s", start_date)
        logger.info("End Date         : %s", end_date)
        logger.info("=" * 70)

        if self.account_type == "organization":

            return self.extract_organization(
                start_date=start_date,
                end_date=end_date,
            )

        return self.extract_standalone(
            start_date=start_date,
            end_date=end_date,
        )

    def extract_standalone(
        self,
        start_date,
        end_date,
    ):

        merged_days = self._fetch_cost_data(
            start_date=start_date,
            end_date=end_date,
            group_by=[
                {
                    "Type": "DIMENSION",
                    "Key": "SERVICE",
                },
                {
                    "Type": "DIMENSION",
                    "Key": "REGION",
                },
            ],
        )

        records = []

        for day in merged_days.values():

            billing_date = day["TimePeriod"]["Start"]

            for group in day.get("Groups", []):

                service = group["Keys"][0]

                region = (
                    group["Keys"][1]
                    if len(group["Keys"]) > 1
                    else "Global"
                )

                cost = group["Metrics"]["UnblendedCost"]
                usage = group["Metrics"]["UsageQuantity"]

                records.append(
                    BillingRecord(
                        billing_date=billing_date,
                        cloud_provider="AWS",
                        account_id=self.account_id,
                        account_name=self.account_name,
                        service=service,
                        region=region,
                        cost=float(cost["Amount"]),
                        currency=cost["Unit"],
                        usage_quantity=float(
                            usage["Amount"]
                        ),
                        usage_unit=usage["Unit"],
                    )
                )

        logger.info(
            "Successfully extracted %s standalone billing records",
            len(records),
        )

        return records

    def extract_organization(
        self,
        start_date,
        end_date,
    ):

        logger.info(
            "Fetching billing data for AWS Organization"
        )

        merged_days = self._fetch_cost_data(
            start_date=start_date,
            end_date=end_date,
            group_by=[
                {
                    "Type": "DIMENSION",
                    "Key": "LINKED_ACCOUNT",
                },
                {
                    "Type": "DIMENSION",
                    "Key": "SERVICE",
                },
            ],
        )

        records = []

        for day in merged_days.values():

            billing_date = day["TimePeriod"]["Start"]

            for group in day.get("Groups", []):

                keys = group["Keys"]

                linked_account_id = (
                    keys[0]
                    if len(keys) > 0
                    else "unknown"
                )

                service = (
                    keys[1]
                    if len(keys) > 1
                    else "Unknown"
                )

                cost = group["Metrics"]["UnblendedCost"]
                usage = group["Metrics"]["UsageQuantity"]

                records.append(
                    BillingRecord(
                        billing_date=billing_date,
                        cloud_provider="AWS",
                        account_id=linked_account_id,
                        account_name=linked_account_id,
                        service=service,
                        region="Global",
                        cost=float(cost["Amount"]),
                        currency=cost["Unit"],
                        usage_quantity=float(
                            usage["Amount"]
                        ),
                        usage_unit=usage["Unit"],
                    )
                )

        logger.info(
            "Successfully extracted %s organization billing records",
            len(records),
        )

        return records

    def _fetch_cost_data(
        self,
        start_date,
        end_date,
        group_by,
    ):

        merged_days = {}

        next_token = None
        page = 1

        while True:

            request = {
                "TimePeriod": {
                    "Start": start_date,
                    "End": end_date,
                },
                "Granularity": "DAILY",
                "Metrics": [
                    "UnblendedCost",
                    "UsageQuantity",
                ],
                "GroupBy": group_by,
            }

            if next_token:

                request["NextPageToken"] = next_token

            response = self.__call_ce(
                request,
            )

            logger.info(
                "Fetched AWS Cost Explorer page %s",
                page,
            )

            for day in response.get(
                "ResultsByTime",
                [],
            ):

                billing_date = day[
                    "TimePeriod"
                ]["Start"]

                if billing_date not in merged_days:

                    merged_days[billing_date] = day

                else:

                    merged_days[
                        billing_date
                    ]["Groups"].extend(
                        day.get(
                            "Groups",
                            [],
                        )
                    )

            next_token = response.get(
                "NextPageToken"
            )

            if not next_token:
                break

            page += 1

        return merged_days

    def __call_ce(
        self,
        request,
        retries=3,
    ):

        for attempt in range(
            1,
            retries + 1,
        ):

            try:

                return self.ce.get_cost_and_usage(
                    **request
                )

            except (
                ClientError,
                BotoCoreError,
            ) as ex:

                logger.warning(
                    "AWS API retry %s/%s : %s",
                    attempt,
                    retries,
                    ex,
                )

                if attempt == retries:
                    raise

                time.sleep(
                    attempt * 2
                )