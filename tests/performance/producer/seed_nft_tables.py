import boto3

dynamodb = boto3.client("dynamodb")
resource = boto3.resource("dynamodb")

logger.setLevel("ERROR")

# DOC_REF_TEMPLATE = load_document_reference("NFT-template")

CHECKSUM_WEIGHTS = [i for i in range(10, 1, -1)]

# These are based on the Nov 7th 2025 pointer stats report
DEFAULT_TYPE_DISTRIBUTIONS = {
    "736253002": 65,  # mental health crisis plan
    "1382601000000107": 5,  # respect form
    "887701000000100": 15,  # emergency healthcare plan
    "861421000000109": 5,  # eol care coordination summary
    "735324008": 5,  # treatment escalation plan
    "824321000000109": 5,  # summary record
}

DEFAULT_CUSTODIAN_DISTRIBUTIONS = {
    "736253002": {
        "TRPG": 9,
        "TRHA": 1,
        "TRRE": 20,
        "TRAT": 10,
        "TWR4": 4,
        "TRKL": 9,
        "TRW1": 5,
        "TRH5": 1,
        "TRP7": 13,
        "TRWK": 8,
        "TRQY": 3,
        "TRV5": 3,
        "TRJ8": 2,
        "TRXA": 4,
        "T11X": 1,
        "TG6V": 2,
    },
    "1382601000000107": {"T8GX8": 3, "TQUY": 2},  # respect form
    "887701000000100": {
        "TV1": 1,
        "TV2": 2,
        "TV3": 1,
        "TV4": 1,
        "TV5": 3,
        "TV6": 1,
    },  # emergency healthcare plan
    "861421000000109": {
        "TV1": 2,
        "TV2": 2,
        "TV3": 1,
        "TV4": 1,
        "TV5": 3,
        "TV6": 1,
    },  # eol care coordination summary
    "735324008": {
        "TV1": 1,
        "TV2": 1,
        "TV3": 1,
        "TV4": 2,
        "TV5": 2,
        "TV6": 1,
    },  # treatment escalation plan
    "824321000000109": {
        "TRXT": 1,
    },  # summary record currently has only one supplier
}
