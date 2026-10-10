from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BillingRecord:

    billing_date: str

    cloud_provider: str

    account_id: str
    account_name: str

    service: str
    region: str

    cost: float
    currency: str

    usage_quantity: float
    usage_unit: str

    scope_type: str = "account"

    operation: str | None = None
    usage_type: str | None = None
    availability_zone: str | None = None

    resource_id: str | None = None
    resource_name: str | None = None

    environment: str | None = None
    project: str | None = None
    owner: str | None = None

    tags: dict = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)