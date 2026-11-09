"""Request and response models: the API's JSON with snake_case attributes.

A request model (`NewChargeCard`, `ChargeSearch`, ...) takes keyword arguments and rejects unknown ones; the
fields you leave as `None` are not sent, so the API applies its defaults. A response model (`ChargeData`, ...) has
every field optional, and keeps fields this version of the SDK doesn't know in `model_extra`. An enum field of a
response is the enum, or the plain string when the API sends a value added after this version.

Amounts are `Decimal`, and sent as JSON numbers.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part.capitalize() for part in rest)


# A JSON number, not the string Pydantic writes for a Decimal: the API reads amounts as numbers.
Amount = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]

E = TypeVar("E", bound=StrEnum)
# The enum member, or the plain string for a value the API added after this version of the SDK.
OpenEnum = Annotated[E | str, Field(union_mode="left_to_right")]


class _Model(BaseModel):
    model_config = ConfigDict(alias_generator=_camel, validate_by_name=True, validate_by_alias=True)


class _Request(_Model):
    model_config = ConfigDict(extra="forbid")


class _Response(_Model):
    model_config = ConfigDict(extra="allow")


class CallToAction(StrEnum):
    """A payment link's button."""

    PAY = "Pay"
    DONATE = "Donate"


class Initiator(StrEnum):
    """Who started a charge: the customer at checkout, or the merchant (a stored card, a subscription)."""

    CUSTOMER = "CUSTOMER"
    MERCHANT = "MERCHANT"


class PaymentType(StrEnum):
    """A payment method's type."""

    CARD = "CARD"
    PAY_PAL = "PAYPAL"
    PAY_TO = "PAYTO"
    PAY_ID = "PAYID"
    OPTTY = "OPTTY"
    GOOGLE_PAY = "GOOGLEPAY"
    APPLE_PAY = "APPLEPAY"
    VIS = "VIS"
    SHIFT = "SHIFT"
    PESAPAL = "PESAPAL"
    PAY_BY_ACCOUNT = "PAYBYACCOUNT"
    CLICK_TO_PAY = "CLICK2PAY"
    UPI = "UPI"
    PAY_GLOCAL = "PAYGLOCAL"
    BANK_PAYMENT = "BANKPAYMENT"
    PAYMENT_METHOD = "PAYMENT_METHOD"
    ZIP = "ZIP"


class SubscriptionInterval(StrEnum):
    """How often a subscription charges, with its frequency."""

    DAY = "Day"
    WEEK = "Week"
    MONTH = "Month"
    YEAR = "Year"


class SubscriptionRetryInterval(StrEnum):
    """The unit of a subscription's retry frequency."""

    HOUR = "Hour"
    DAY = "Day"


class SubscriptionStatus(StrEnum):
    """A subscription's status."""

    UNKNOWN = "Unknown"
    COMPLETE = "Complete"
    ACTIVE = "Active"
    CANCELLED = "Cancelled"
    SUSPENDED = "Suspended"


class TransactionStatus(StrEnum):
    """A charge's status (`ChargeData.status`)."""

    PENDING = "PENDING"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"
    PARTIAL_REFUND = "PARTIAL_REFUND"
    REFUND = "REFUND"
    PENDING_CHECKOUT = "PENDING_CHECKOUT"
    AUTHORISE = "AUTHORISE"
    AUTHORISE_CANCELLED = "AUTHORISE_CANCELLED"


class WebhookType(StrEnum):
    """What a webhook subscription receives."""

    TRANSACTION = "Transaction"
    BATCH = "Batch"
    SUBSCRIPTION = "Subscription"
    CUSTOMER = "Customer"
    PAYMENT_METHOD = "PaymentMethod"
    DISPUTE = "Dispute"


class Address(_Response):
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    country: str | None = None
    postal_code: str | None = None
    state: str | None = None


class ApplePayProviderInfo(_Response):
    line_item_label: str | None = None
    merchant_identifier: str | None = None
    domain_name: str | None = None
    display_name: str | None = None
    country_code: str | None = None
    provider_id: str | None = None
    provider_type: str | None = None
    client_parameters: dict[str, str] | None = None


class ApplicationVersion(_Response):
    version: str | None = None
    released: datetime | None = None
    region: str | None = None


class BankPaymentData(_Response):
    bank_code: str | None = None
    account_number: str | None = None
    account_name: str | None = None


class BatchData(_Response):
    batch_id: str | None = None
    count: int | None = None
    success: int | None = None
    failure: int | None = None
    description: str | None = None
    status: str | None = None
    progress: Amount | None = None
    results: str | None = None
    date_added: datetime | None = None
    metadata: dict[str, str] | None = None


class BatchSummary(_Response):
    batch_id: str | None = None
    count: int | None = None
    success: int | None = None
    failure: int | None = None
    description: str | None = None
    status: str | None = None
    progress: Amount | None = None
    date_added: datetime | None = None
    metadata: dict[str, str] | None = None


class BatchList(_Response):
    limit: int | None = None
    skip: int | None = None
    count: int | None = None
    batches: list[BatchSummary] | None = None


class BatchSearch(_Request):
    """The query of `GET /batch`. Filters are optional; `limit` and `skip` page through the results."""

    description: str | None = None
    added_after: datetime | None = None
    added_before: datetime | None = None
    status: str | None = None
    limit: int | None = None
    skip: int | None = None


class BatchStatus(_Response):
    batch_id: str | None = None
    count: int | None = None
    success: int | None = None
    failure: int | None = None
    description: str | None = None
    status: str | None = None
    progress: Amount | None = None
    date_added: datetime | None = None
    metadata: dict[str, str] | None = None


class BnplOptions(_Response):
    provider_id: str | None = None
    provider_type: str | None = None
    options: dict[str, str] | None = None
    client_parameters: dict[str, str] | None = None


class IinData(_Response):
    scheme: str | None = None
    country: str | None = None
    issuer: str | None = None
    country_code: str | None = None
    card_type: str | None = None


class CardData(_Response):
    card_number: str | None = None
    expiry_date: str | None = None
    cardholder: str | None = None
    type: str | None = None
    card_type: str | None = None
    card_iin: str | None = None
    ccv_check: bool | None = None
    three_ds_server_trans_id: str | None = Field(None, alias="threeDSServerTransID")
    iin_data: IinData | None = None


class CardRequestInformation(_Request):
    card_number: str
    expiry_date: str
    ccv: str | None = None
    cardholder: str | None = None
    three_ds_server_trans_id: str | None = Field(None, alias="threeDSServerTransID")
    external_three_ds_data: dict[str, str] | None = None


class PaymentData(_Response):
    payment_method_id: str | None = None
    card: CardData | None = None
    type: OpenEnum[PaymentType] | None = None
    display_type: str | None = None
    email: str | None = None
    bank_payment: BankPaymentData | None = None


class Refund(_Response):
    amount: Amount | None = None
    comment: str | None = None
    user_id: str | None = None
    date_added: datetime | None = None
    gateway_refund_id: str | None = None


class ProcessorResult(_Response):
    authorization_code: str | None = None
    response_code: str | None = None
    response_text: str | None = None
    cvv_result: str | None = None
    avs_street_result: str | None = None
    avs_zip_result: str | None = None
    avs_name_result: str | None = None
    avs_full_result: str | None = None
    network_transaction_id: str | None = None


class FailureData(_Response):
    provider_id: str | None = None
    date_attempted: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None
    gateway_code: str | None = None
    gateway_message: str | None = None
    processor_result: ProcessorResult | None = None
    is_retryable: bool | None = None


class CustomerDataSummary(_Response):
    customer_id: str | None = None
    reference: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    date_added: datetime | None = None
    date_removed: datetime | None = None


class ProviderSummary(_Response):
    provider_id: str | None = None
    type: str | None = None
    name: str | None = None


class GeolocationInfo(_Response):
    ip: str | None = None
    hostname: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    loc: str | None = None
    org: str | None = None
    postal: str | None = None
    timezone: str | None = None


class VisaInstallmentsTermsAndConditions(_Response):
    url: str | None = None
    version: int | None = None
    text: str | None = None
    language_code: str | None = None


class VisaInstallmentsInfo(_Response):
    provider_id: str | None = None
    vis_plan_id: str | None = None
    vis_accepted_t_and_c_version: int | None = None
    vis_plan_id_ref: str | None = None
    vis_plan_name: str | None = None
    vis_number_of_installments: int | None = None
    vis_total_fees: Amount | None = None
    vis_total_plan_cost: Amount | None = None
    vis_installment_frequency: str | None = None
    vis_terms_and_conditions: list[VisaInstallmentsTermsAndConditions] | None = None


class ChargeData(_Response):
    charge_id: str | None = None
    provider_charge_id: str | None = None
    amount: Amount | None = None
    provider_id: str | None = None
    reference: str | None = None
    payment_information: PaymentData | None = None
    customer_id: str | None = None
    status: OpenEnum[TransactionStatus] | None = None
    date_added: datetime | None = None
    success_date: datetime | None = None
    void_date: datetime | None = None
    refunded_amount: Amount | None = None
    estimated_cost: Amount | None = None
    estimated_cost_currency: str | None = None
    currency: str | None = None
    refunds: list[Refund] | None = None
    failed_attempts: list[FailureData] | None = None
    customer: CustomerDataSummary | None = None
    provider: ProviderSummary | None = None
    three_ds_verified: bool | None = None
    authorisation_amount: Amount | None = None
    initiator: str | None = None
    ip: str | None = None
    ip_info: GeolocationInfo | None = None
    visa_installments: VisaInstallmentsInfo | None = None
    descriptor: str | None = None
    three_ds_redirect_url: str | None = None
    payment_token_id: str | None = None
    subscription_id: str | None = None
    metadata: dict[str, str] | None = None


class ChargeList(_Response):
    limit: int | None = None
    skip: int | None = None
    count: int | None = None
    charges: list[ChargeData] | None = None


class ChargeSearch(_Request):
    """The query of `GET /charge`. Filters are optional; `limit` and `skip` page through the results."""

    reference: str | None = None
    provider_id: str | None = None
    amount_greater_than: Amount | None = None
    amount_less_than: Amount | None = None
    customer_id: str | None = None
    status: TransactionStatus | None = None
    added_after: datetime | None = None
    added_before: datetime | None = None
    payment_method_id: str | None = None
    payment_type: PaymentType | None = None
    card_type: str | None = None
    currency: str | None = None
    card_number: str | None = None
    cardholder: str | None = None
    batch_id: str | None = None
    subscription_id: str | None = None
    sort_by: str | None = None
    sort_order: str | None = None
    limit: int | None = None
    skip: int | None = None


class CheckoutTransfer(_Request):
    amount: Amount
    account: str | None = None


class ClickToPayCardData(_Response):
    pan_bin: str | None = None
    pan_last_four: str | None = None
    scheme: str | None = None
    payment_card_type: str | None = None


class ClickToPayData(_Response):
    billing_address: Address | None = None
    card_data: ClickToPayCardData | None = None


class ClickToPayOptions(_Response):
    dpa_id: str | None = None
    dpa_name: str | None = None
    use_fpan: bool | None = None


class CreatePaymentLink(_Request):
    title: str
    amount: Amount | None = None
    currency: str | None = None
    allowed_payment_types: list[PaymentType] | None = None
    description: str | None = None
    image: str | None = None
    confirmation_message: str | None = None
    redirect_url: str | None = None
    call_to_action: CallToAction | None = None
    limit_payments: int | None = None
    invoice_id: str | None = None
    metadata: dict[str, str] | None = None


class PaymentMethodSummary(_Response):
    payment_method_id: str | None = None
    customer_id: str | None = None
    type: OpenEnum[PaymentType] | None = None
    card: CardData | None = None
    provider_id: str | None = None
    provider_type: str | None = None
    date_added: datetime | None = None
    email: str | None = None
    vault_id: str | None = None
    date_removed: datetime | None = None
    provider_payment_method_id: str | None = None
    provider_payment_method_data: dict[str, str] | None = None
    token: str | None = None
    fallback_payment_method_id: str | None = None
    metadata: dict[str, str] | None = None
    network_token_id: str | None = None


class CustomerData(_Response):
    customer_id: str | None = None
    reference: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    date_added: datetime | None = None
    default_payment_method: PaymentMethodSummary | None = None
    ip: str | None = None
    date_removed: datetime | None = None
    address: Address | None = None


class CustomerList(_Response):
    limit: int | None = None
    skip: int | None = None
    count: int | None = None
    customers: list[CustomerData] | None = None


class CustomerSearch(_Request):
    """The query of `GET /customer`. Filters are optional; `limit` and `skip` page through the results."""

    reference: str | None = None
    email: str | None = None
    added_after: datetime | None = None
    added_before: datetime | None = None
    search: str | None = None
    sort_by: str | None = None
    include_removed: bool | None = None
    limit: int | None = None
    skip: int | None = None


class DirectDebitDetails(_Response):
    bsb: str | None = None
    account_number: str | None = None


class Dispute(_Response):
    dispute_id: str | None = None
    transaction_id: str | None = None
    provider_id: str | None = None
    type: str | None = None
    gateway_dispute_id: str | None = None
    amount: Amount | None = None
    currency: str | None = None
    fee: Amount | None = None
    status: str | None = None
    stage: str | None = None
    reason_category: str | None = None
    reason: str | None = None
    network_reason_code: str | None = None
    card_brand: str | None = None
    dispute_date: datetime | None = None
    evidence_due_by: datetime | None = None
    submission_count: int | None = None
    is_charge_refundable: bool | None = None
    date_added: datetime | None = None
    date_updated: datetime | None = None


class DisputeList(_Response):
    limit: int | None = None
    skip: int | None = None
    count: int | None = None
    disputes: list[Dispute] | None = None


class DisputeSearch(_Request):
    """The query of `GET /dispute`. Filters are optional; `limit` and `skip` page through the results."""

    transaction_id: str | None = None
    provider_id: str | None = None
    status: str | None = None
    stage: str | None = None
    reason_category: str | None = None
    currency: str | None = None
    amount_greater_than: Amount | None = None
    amount_less_than: Amount | None = None
    added_after: datetime | None = None
    added_before: datetime | None = None
    due_before: datetime | None = None
    sort_by: str | None = None
    sort_order: str | None = None
    limit: int | None = None
    skip: int | None = None


class FraudOptions(_Response):
    provider_id: str | None = None
    provider_type: str | None = None
    enabled: bool | None = None
    stop_payment_on_failure: bool | None = None
    client_parameters: dict[str, str] | None = None


class Geolocation(_Request):
    longitude: Amount | None = None
    latitude: Amount | None = None


class GooglePayProviderInfo(_Response):
    gateway: str | None = None
    google_pay_gateway_merchant_id: str | None = None
    google_pay_merchant_id: str | None = None
    google_pay_merchant_name: str | None = None
    provider_id: str | None = None


class PayToProviderOptions(_Response):
    provider_id: str | None = None
    maximum_amount: Amount | None = None
    description: str | None = None


class ThreeDsOptions(_Response):
    provider_id: str | None = None
    provider_name: str | None = None
    provider_type: str | None = None
    client_parameters: dict[str, str] | None = None


class NetworkTokenProviderInfo(_Response):
    provider_id: str | None = None
    provider_type: str | None = None
    client_parameters: dict[str, str] | None = None


class InfoProviders(_Response):
    paypal_providers: list[str] | None = None
    has_card_providers: bool | None = None
    has_paypal_providers: bool | None = None
    required_3ds_provider: str | None = Field(None, alias="required3dsProvider")
    has_pay_to_providers: bool | None = None
    pay_to_providers: list[str] | None = None
    pay_to_providers_with_options: list[PayToProviderOptions] | None = None
    has_bnpl_providers: bool | None = None
    bnpl_providers: list[BnplOptions] | None = None
    has_visa_installments_providers: bool | None = None
    visa_installments_providers: list[str] | None = None
    has_fraud_providers: bool | None = None
    fraud_providers: list[FraudOptions] | None = None
    has_three_ds_providers: bool | None = None
    three_ds_providers: list[ThreeDsOptions] | None = None
    all_three_ds_providers: list[ThreeDsOptions] | None = None
    has_google_pay_providers: bool | None = None
    google_pay_providers: list[GooglePayProviderInfo] | None = None
    has_apple_pay_providers: bool | None = None
    apple_pay_providers: list[ApplePayProviderInfo] | None = None
    click_to_pay_enabled: bool | None = None
    click_to_pay_options: ClickToPayOptions | None = None
    has_network_token_providers: bool | None = None
    network_token_providers: list[NetworkTokenProviderInfo] | None = None


class UriData(_Response):
    uri: str | None = None
    uri_type: str | None = None


class NetworkTokenAuthenticationMethod(_Response):
    authentication_method_type: str | None = None
    authentication_subject: str | None = None
    uri_data: UriData | None = None


class NetworkTokenSummary(_Response):
    network_token_id: str | None = None
    scheme_token_id: str | None = None
    provider_id: str | None = None
    provider_type: str | None = None
    status: str | None = None
    date_added: datetime | None = None
    scheme_token_data: dict[str, str] | None = None
    authentication_method: NetworkTokenAuthenticationMethod | None = None


class NewBankPayment(_Request):
    bank_code: str
    account_number: str
    account_name: str


class ProductItem(_Request):
    product_code: str | None = None
    commodity_code: str | None = None
    description: str | None = None
    quantity: int | None = None
    unit_of_measure: str | None = None
    amount: Amount | None = None
    tax_amount: Amount | None = None


class Order(_Request):
    order_number: str | None = None
    freight_amount: Amount | None = None
    duty_amount: Amount | None = None
    items: list[ProductItem] | None = None


class WebhookConfig(_Response):
    url: str | None = None
    authorization: str | None = None


class NewChargeBankPayment(_Request):
    amount: Amount
    provider_id: str
    bank_payment_information: NewBankPayment
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    reference: str | None = None
    capture: bool | None = None
    ip: str | None = None
    address: Address | None = None
    order: Order | None = None
    customer_code: str | None = None
    invoice_number: str | None = None
    initiator: Initiator | None = None
    webhook: WebhookConfig | None = None
    first_name: str | None = None
    last_name: str | None = None
    metadata: dict[str, str] | None = None
    descriptor: str | None = None
    three_ds_notification_url: str | None = Field(None, alias="threeDSNotificationUrl")
    geolocation: Geolocation | None = None


class NewChargeCard(_Request):
    amount: Amount
    provider_id: str
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    reference: str | None = None
    payment_information: CardRequestInformation | None = None
    capture: bool | None = None
    ip: str | None = None
    address: Address | None = None
    order: Order | None = None
    customer_code: str | None = None
    invoice_number: str | None = None
    initiator: Initiator | None = None
    webhook: WebhookConfig | None = None
    first_name: str | None = None
    last_name: str | None = None
    metadata: dict[str, str] | None = None
    descriptor: str | None = None
    three_ds_notification_url: str | None = Field(None, alias="threeDSNotificationUrl")
    geolocation: Geolocation | None = None


class NewChargeCardLeastCost(_Request):
    amount: Amount
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    reference: str | None = None
    payment_information: CardRequestInformation | None = None
    capture: bool | None = None
    ip: str | None = None
    order: Order | None = None
    address: Address | None = None
    customer_code: str | None = None
    invoice_number: str | None = None
    initiator: Initiator | None = None
    webhook: WebhookConfig | None = None
    metadata: dict[str, str] | None = None
    descriptor: str | None = None
    three_ds_notification_url: str | None = Field(None, alias="threeDSNotificationUrl")
    first_name: str | None = None
    last_name: str | None = None
    geolocation: Geolocation | None = None


class NewChargeCustomer(_Request):
    amount: Amount
    customer_id: str
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    reference: str | None = None
    capture: bool | None = None
    ip: str | None = None
    address: Address | None = None
    order: Order | None = None
    customer_code: str | None = None
    invoice_number: str | None = None
    initiator: Initiator | None = None
    webhook: WebhookConfig | None = None
    first_name: str | None = None
    last_name: str | None = None
    metadata: dict[str, str] | None = None
    descriptor: str | None = None
    three_ds_notification_url: str | None = Field(None, alias="threeDSNotificationUrl")
    geolocation: Geolocation | None = None
    recurring: bool | None = None


class NewChargeNetworkToken(_Request):
    network_token_id: str
    amount: Amount
    provider_id: str
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    reference: str | None = None
    capture: bool | None = None
    ip: str | None = None
    address: Address | None = None
    order: Order | None = None
    customer_code: str | None = None
    invoice_number: str | None = None
    initiator: Initiator | None = None
    webhook: WebhookConfig | None = None
    first_name: str | None = None
    last_name: str | None = None
    metadata: dict[str, str] | None = None
    descriptor: str | None = None
    three_ds_notification_url: str | None = Field(None, alias="threeDSNotificationUrl")


class NewChargePaymentMethod(_Request):
    amount: Amount
    payment_method_id: str
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    reference: str | None = None
    capture: bool | None = None
    ip: str | None = None
    address: Address | None = None
    order: Order | None = None
    customer_code: str | None = None
    invoice_number: str | None = None
    initiator: Initiator | None = None
    webhook: WebhookConfig | None = None
    first_name: str | None = None
    last_name: str | None = None
    metadata: dict[str, str] | None = None
    descriptor: str | None = None
    three_ds_notification_url: str | None = Field(None, alias="threeDSNotificationUrl")
    geolocation: Geolocation | None = None
    recurring: bool | None = None


class NewChargeToken(_Request):
    amount: Amount
    token: str
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    reference: str | None = None
    transfer: CheckoutTransfer | None = None
    capture: bool | None = None
    ip: str | None = None
    address: Address | None = None
    order: Order | None = None
    customer_code: str | None = None
    invoice_number: str | None = None
    initiator: Initiator | None = None
    webhook: WebhookConfig | None = None
    first_name: str | None = None
    last_name: str | None = None
    metadata: dict[str, str] | None = None
    descriptor: str | None = None
    three_ds_notification_url: str | None = Field(None, alias="threeDSNotificationUrl")
    geolocation: Geolocation | None = None


class NewCustomerBankPayment(_Request):
    provider_id: str
    bank_payment_information: NewBankPayment
    email: str | None = None
    phone: str | None = None
    reference: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    ip: str | None = None
    address: Address | None = None
    metadata: dict[str, str] | None = None
    webhook: WebhookConfig | None = None


class NewCustomerCard(_Request):
    provider_id: str
    payment_information: CardRequestInformation
    email: str | None = None
    phone: str | None = None
    reference: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    ip: str | None = None
    address: Address | None = None
    vault_card: bool | None = None
    vault_expire_date: datetime | None = None
    vault_expire_seconds: int | None = None
    skip_expiry_date_validation: bool | None = None
    metadata: dict[str, str] | None = None
    webhook: WebhookConfig | None = None
    create_network_token: bool | None = None
    verify: bool | None = None


class PayIdDetails(_Request):
    pay_id: str
    pay_id_type: str


class NewPayToAgreement(_Request):
    payer_name: str
    payer_pay_id_details: PayIdDetails
    description: str
    maximum_amount: int
    provider_id: str
    notification_url: str | None = None
    ip: str | None = None
    set_default: bool | None = None
    fallback_payment_method_id: str | None = None
    webhook: WebhookConfig | None = None
    metadata: dict[str, str] | None = None


class NewCustomerPayTo(_Request):
    pay_to_agreement: NewPayToAgreement
    email: str | None = None
    phone: str | None = None
    reference: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    ip: str | None = None
    address: Address | None = None
    webhook: WebhookConfig | None = None


class NewCustomerProviderToken(_Request):
    provider_id: str
    provider_token: str
    email: str | None = None
    phone: str | None = None
    reference: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    ip: str | None = None
    address: Address | None = None
    provider_token_data: dict[str, str] | None = None
    verify: bool | None = None
    type: PaymentType | None = None
    metadata: dict[str, str] | None = None
    webhook: WebhookConfig | None = None


class NewCustomerToken(_Request):
    token: str
    email: str | None = None
    phone: str | None = None
    reference: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    ip: str | None = None
    address: Address | None = None
    metadata: dict[str, str] | None = None
    webhook: WebhookConfig | None = None


class NewPaymentMethodBankPayment(_Request):
    provider_id: str
    bank_payment_information: NewBankPayment
    first_name: str | None = None
    last_name: str | None = None
    metadata: dict[str, str] | None = None
    set_default: bool | None = None
    fallback_payment_method_id: str | None = None
    webhook: WebhookConfig | None = None


class NewPaymentMethodCard(_Request):
    provider_id: str
    payment_information: CardRequestInformation
    vault_card: bool | None = None
    vault_expire_date: datetime | None = None
    vault_expire_seconds: int | None = None
    ip: str | None = None
    set_default: bool | None = None
    skip_expiry_date_validation: bool | None = None
    metadata: dict[str, str] | None = None
    fallback_payment_method_id: str | None = None
    webhook: WebhookConfig | None = None
    create_network_token: bool | None = None
    verify: bool | None = None


class NewPaymentMethodToken(_Request):
    token: str
    ip: str | None = None
    set_default: bool | None = None
    metadata: dict[str, str] | None = None
    fallback_payment_method_id: str | None = None
    webhook: WebhookConfig | None = None


class NewPaymentMethodVault(_Request):
    provider_id: str
    payment_method_id: str
    ccv: str | None = None
    fallback_payment_method_id: str | None = None
    webhook: WebhookConfig | None = None


class NewProvider(_Request):
    type: str
    name: str
    environment: str
    authentication_parameters: dict[str, str]
    currency: str
    additional_parameters: dict[str, str] | None = None
    provider_country: str | None = None


class NewProviderToken(_Request):
    provider_id: str
    provider_token: str
    email: str | None = None
    provider_token_data: dict[str, str] | None = None
    metadata: dict[str, str] | None = None
    verify: bool | None = None
    type: PaymentType | None = None
    fallback_payment_method_id: str | None = None


class NewTransactionPaymentMethod(_Request):
    count: int
    description: str
    batch: str
    webhook: WebhookConfig | None = None
    metadata: dict[str, str] | None = None


class NewTransfer(_Request):
    account: str
    amount: Amount
    currency: str | None = None
    message: str | None = None
    reference: str | None = None


class NewTransferGroup(_Request):
    provider_id: str
    group_reference: str
    transfers: list[NewTransfer]
    charge_id: str | None = None


class NewVault(_Request):
    card_number: str
    ccv: str | None = None
    expire_date: datetime | None = None
    expire_seconds: int | None = None


class NewWebhookSubscription(_Request):
    url: str
    types: list[WebhookType]
    authorization: str | None = None


class PayerPayIdDetails(_Response):
    pay_id: str | None = None
    pay_id_type: str | None = None


class PayToSummary(_Response):
    pay_to_id: str | None = None
    status: str | None = None
    payer_name: str | None = None
    payer_pay_id_details: PayerPayIdDetails | None = None
    payer_direct_debit_details: DirectDebitDetails | None = None
    provider_id: str | None = None
    provider_type: str | None = None


class PaymentLink(_Response):
    url: str | None = None
    payment_link_id: str | None = None
    date_added: datetime | None = None
    account_id: str | None = None
    public_key: str | None = None
    title: str | None = None
    amount: Amount | None = None
    currency: str | None = None
    allowed_payment_types: list[OpenEnum[PaymentType]] | None = None
    description: str | None = None
    image: str | None = None
    confirmation_message: str | None = None
    redirect_url: str | None = None
    call_to_action: OpenEnum[CallToAction] | None = None
    limit_payments: int | None = None
    count_payments: int | None = None
    invoice_id: str | None = None
    metadata: dict[str, str] | None = None


class PaymentLinkList(_Response):
    payment_links: list[PaymentLink] | None = None
    count: int | None = None


class PaymentLinkSearch(_Request):
    """The query of `GET /payment_link`. Filters are optional; `limit` and `skip` page through the results."""

    added_after: datetime | None = None
    added_before: datetime | None = None
    limit: int | None = None
    skip: int | None = None


class PaymentMethodData(_Response):
    payment_method_id: str | None = None
    customer_id: str | None = None
    type: OpenEnum[PaymentType] | None = None
    card: CardData | None = None
    bank_payment: BankPaymentData | None = None
    provider_id: str | None = None
    provider_type: str | None = None
    date_added: datetime | None = None
    email: str | None = None
    customer: CustomerDataSummary | None = None
    provider: ProviderSummary | None = None
    pay_to: PayToSummary | None = None
    network_token: NetworkTokenSummary | None = None
    vault_id: str | None = None
    pay_to_status: str | None = None
    ip: str | None = None
    date_removed: datetime | None = None
    provider_payment_method_id: str | None = None
    provider_payment_method_data: dict[str, str] | None = None
    token: str | None = None
    network_token_id: str | None = None
    fallback_payment_method_id: str | None = None
    metadata: dict[str, str] | None = None


class PaymentMethodList(_Response):
    limit: int | None = None
    skip: int | None = None
    count: int | None = None
    payment_methods: list[PaymentMethodData] | None = None


class PaymentMethodSearch(_Request):
    """The query of `GET /payment_method`. Filters are optional; `limit` and `skip` page through the results."""

    added_after: datetime | None = None
    added_before: datetime | None = None
    provider_id: str | None = None
    customer_id: str | None = None
    payment_type: PaymentType | None = None
    card_type: str | None = None
    search: str | None = None
    sort_by: str | None = None
    sort_order: str | None = None
    include_removed: bool | None = None
    limit: int | None = None
    skip: int | None = None


class ProviderCostData(_Response):
    is_international_card: bool | None = None
    card_scheme: str | None = None
    transaction_cost: Amount | None = None
    transaction_percentage: Amount | None = None


class ProviderVisibilityData(_Response):
    currency: str | None = None
    less_than_amount: Amount | None = None
    greater_than_amount: Amount | None = None
    apply_currency_conversion: bool | None = None


class ProviderInfo(_Response):
    id: str | None = None
    name: str | None = None
    type: str | None = None
    apply_currency_conversion: bool | None = None


class Provider(_Response):
    provider_id: str | None = None
    type: str | None = None
    name: str | None = None
    environment: str | None = None
    authentication_parameters: dict[str, str] | None = None
    additional_parameters: dict[str, str] | None = None
    provider_country: str | None = None
    cost_data: list[ProviderCostData] | None = None
    hide_configuration: list[ProviderVisibilityData] | None = None
    require_configuration: list[ProviderVisibilityData] | None = None
    fallback_provider_id: str | None = None
    currency: str | None = None
    max_capability: str | None = None
    has_partial_refund: bool | None = None
    fallback_provider: ProviderInfo | None = None
    has_three_ds_capability: bool | None = None


class RootStatus(_Response):
    status: str | None = None


class Settlement(_Response):
    settlement_id: str | None = None
    settlement_date: datetime | None = None
    created_date: datetime | None = None
    provider_id: str | None = None
    provider_name: str | None = None
    charge_id: str | None = None
    amount: Amount | None = None


class SingleUseToken(_Request):
    provider_id: str
    provider_token: str
    email: str | None = None
    phone: str | None = None
    reference: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    ip: str | None = None
    address: Address | None = None
    provider_token_data: dict[str, str] | None = None
    metadata: dict[str, str] | None = None
    fallback_payment_method_id: str | None = None
    webhook: WebhookConfig | None = None


class SubscriptionEnd(_Response):
    amount: Amount | None = None
    count: int | None = None
    date: datetime | None = None


class SubscriptionRetryPolicy(_Response):
    maximum: int | None = None
    interval: OpenEnum[SubscriptionRetryInterval] | None = None
    frequency: int | None = None


class Subscription(_Response):
    subscription_id: str | None = None
    payment_method_id: str | None = None
    amount: Amount | None = None
    currency: str | None = None
    interval: OpenEnum[SubscriptionInterval] | None = None
    frequency: int | None = None
    created_date: datetime | None = None
    start_date: datetime | None = None
    end_after: SubscriptionEnd | None = None
    retry: SubscriptionRetryPolicy | None = None
    webhook: WebhookConfig | None = None
    status: OpenEnum[SubscriptionStatus] | None = None
    metadata: dict[str, str] | None = None


class SubscriptionCreate(_Request):
    payment_method_id: str
    amount: Amount
    currency: str
    interval: SubscriptionInterval
    frequency: int
    start_date: datetime | None = None
    end_after: SubscriptionEnd | None = None
    retry: SubscriptionRetryPolicy | None = None
    webhook: WebhookConfig | None = None
    metadata: dict[str, str] | None = None


class SubscriptionList(_Response):
    count: int | None = None
    subscriptions: list[Subscription] | None = None


class SubscriptionSearch(_Request):
    """The query of `GET /subscription`. Filters are optional; `limit` and `skip` page through the results."""

    amount_greater_than: Amount | None = None
    amount_less_than: Amount | None = None
    added_after: datetime | None = None
    added_before: datetime | None = None
    currency: str | None = None
    status: SubscriptionStatus | None = None
    payment_method_id: str | None = None
    sort_by: str | None = None
    limit: int | None = None
    skip: int | None = None


class SubscriptionWebhookUpdate(_Request):
    url: str | None = None
    authorization: str | None = None


class SubscriptionUpdate(_Request):
    amount: Amount
    currency: str
    interval: SubscriptionInterval
    frequency: int
    end_after: SubscriptionEnd | None = None
    retry: SubscriptionRetryPolicy | None = None
    webhook: SubscriptionWebhookUpdate | None = None
    metadata: dict[str, str] | None = None


class TokenData(_Response):
    token_id: str | None = None
    account_id: str | None = None
    card: CardData | None = None
    provider: ProviderSummary | None = None
    date_added: datetime | None = None
    date_used: datetime | None = None
    pay_to_status: str | None = None
    metadata: dict[str, str] | None = None
    click_to_pay: ClickToPayData | None = None


class TokenList(_Response):
    limit: int | None = None
    skip: int | None = None
    count: int | None = None
    tokens: list[TokenData] | None = None


class TokenSearch(_Request):
    """The query of `GET /token`. Filters are optional; `limit` and `skip` page through the results."""

    provider_id: str | None = None
    added_after: datetime | None = None
    added_before: datetime | None = None
    status: str | None = None
    sort_by: str | None = None
    limit: int | None = None
    skip: int | None = None


class TransferData(_Response):
    transfer_id: str | None = None
    status: str | None = None
    reference: str | None = None
    group_reference: str | None = None
    date_added: datetime | None = None
    total_amount: Amount | None = None
    provider_id: str | None = None
    amount: Amount | None = None
    currency: str | None = None
    account: str | None = None
    charge_id: str | None = None


class TransferList(_Response):
    limit: int | None = None
    skip: int | None = None
    count: int | None = None
    transfers: list[TransferData] | None = None


class TransferSearch(_Request):
    """The query of `GET /transfer`. Filters are optional; `limit` and `skip` page through the results."""

    reference: str | None = None
    provider_id: str | None = None
    status: str | None = None
    added_after: datetime | None = None
    added_before: datetime | None = None
    sort_by: str | None = None
    limit: int | None = None
    skip: int | None = None


class UpdateCustomer(_Request):
    email: str | None = None
    phone: str | None = None
    address: Address | None = None
    default_payment_method_id: str | None = None


class UpdatePaymentMethodCardRequestInformation(_Request):
    expiry_date: str | None = None
    cardholder: str | None = None
    card_number: str | None = None


class UpdatePaymentMethod(_Request):
    card: UpdatePaymentMethodCardRequestInformation
    metadata: dict[str, str] | None = None


class UpdateProvider(_Request):
    name: str | None = None
    authentication_parameters: dict[str, str] | None = None
    additional_parameters: dict[str, str] | None = None
    provider_country: str | None = None
    currency: str | None = None


class UpdateSubscriptionStatus(_Request):
    status: SubscriptionStatus


class VaultData(_Response):
    vault_id: str | None = None
    created_date: datetime | None = None
    expire_date: datetime | None = None
    masked_card_number: str | None = None
    has_cvv: bool | None = None


class VaultDataWithPCI(_Response):
    vault_id: str | None = None
    created_date: datetime | None = None
    expire_date: datetime | None = None
    masked_card_number: str | None = None
    has_cvv: bool | None = None
    card_number: str | None = None
    ccv: str | None = None


class WebhookSubscription(_Response):
    webhook_subscription_id: str | None = None
    account_id: str | None = None
    url: str | None = None
    authorization: str | None = None
    types: list[OpenEnum[WebhookType]] | None = None
    created_date: datetime | None = None
    date_removed: datetime | None = None


class WebhookSubscriptionList(_Response):
    webhook_subscriptions: list[WebhookSubscription] | None = None
    count: int | None = None


class WebhookSubscriptionSearch(_Request):
    """The query of `GET /webhook/subscription`. Filters are optional; `limit` and `skip` page through the results."""

    added_after: datetime | None = None
    added_before: datetime | None = None
    id: str | None = None
    type: WebhookType | None = None
    sort_by: str | None = None
    limit: int | None = None
    skip: int | None = None
