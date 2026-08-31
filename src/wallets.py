import json
from dataclasses import dataclass

SELLER_KEYWORDS = ("jual", "jualan", "sell", "seller", "dump")


@dataclass
class Entity:
    label: str
    addresses: list  # list of strings
    track_accumulation: bool = True

    def get_addresses(self) -> list:
        return [addr.lower() for addr in self.addresses]


def load_wallets(path: str = "wallets.json") -> list:
    """Load wallet entities from a JSON file."""
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    entities = []
    for entry in data.get("entities", []):
        label = entry["label"]
        if "track_accumulation" in entry:
            track_acc = bool(entry["track_accumulation"])
        else:
            # Auto-detect seller from keywords in label
            track_acc = not any(k in label.lower() for k in SELLER_KEYWORDS)

        entities.append(Entity(
            label=label,
            addresses=entry.get("addresses", []),
            track_accumulation=track_acc,
        ))
    return entities
