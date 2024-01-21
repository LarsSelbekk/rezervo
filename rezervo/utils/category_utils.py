from pydantic.main import BaseModel


class RezervoBaseCategory(BaseModel):
    name: str
    color: str


class RezervoCategory(RezervoBaseCategory):
    keywords: list[str]


OTHER_ACTIVITY_CATEGORY = RezervoCategory(
    name="Annet",
    color="#FFFF66",
    keywords=["happening", "event"],
)

ACTIVITY_CATEGORIES = [
    OTHER_ACTIVITY_CATEGORY,
    RezervoCategory(
        name="Tilleggstjenester",
        color="#f4eded",
        keywords=["tilleggstjenester", "barnepass", "kroppsanalyse"],
    ),
    RezervoCategory(
        name="Vannaerobic",
        color="#0047ab",
        keywords=["vann"],
    ),
    RezervoCategory(
        name="Mosjon",
        color="#00B050",
        keywords=["mosjon", "godt voksen", "mamma", "mor og barn", "senior", "baby"],
    ),
    RezervoCategory(
        name="Dans",
        color="#E96179",
        keywords=["dans", "dance", "sh'bam", "zumba"],
    ),
    RezervoCategory(
        name="Body & Mind",
        color="#8BD4F0",
        keywords=[
            "body & mind",
            "yoga",
            "pilates",
            "smidig",
            "stretch",
            "mobilitet",
            "meditate",
            "flow",
            "yin",
            "soul",
            "breath",
            "grounding",
        ],
    ),
    RezervoCategory(
        name="Spinning",
        color="#4C2C7E",
        keywords=["spin", "sykkel", "ride"],
    ),
    RezervoCategory(
        name="Kondisjon",
        color="#6AD3B4",
        keywords=[
            "kondisjon",
            "step",
            "løp",
            "puls",
            "bodyattack",
            "cardio",
            "tredemølle",
            "hiit",
            "aerobic",
        ],
    ),
    RezervoCategory(
        name="Styrke & Utholdenhet",
        color="#F8A800",
        keywords=[
            "utholdenhet",
            "pump",
            "styrke",
            "core",
            "sterk",
            "tabata",
            "stærk",
            "strength",
            "hardhausen",
            "slynge",
            "crosstraining",
            "bodycross",
            "mrl",
        ],
    ),
]


def determine_activity_category(activity_name: str) -> RezervoCategory:
    for category in ACTIVITY_CATEGORIES:
        for keyword in category.keywords:
            if keyword in activity_name.lower():
                return category
    return OTHER_ACTIVITY_CATEGORY
