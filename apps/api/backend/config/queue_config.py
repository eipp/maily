from enum import Enum

class Queues(str, Enum):
    CAMPAIGN_PROCESSING = "campaign_processing"
    CAMPAIGN_SCHEDULING = "campaign_scheduling"
    EMAIL_HIGH_PRIORITY = "email_high_priority"
    EMAIL_REGULAR = "email_regular"
    EMAIL_BULK = "email_bulk"
