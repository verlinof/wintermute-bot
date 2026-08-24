import json
from dataclasses import dataclass


@dataclass
class Entity:
    label: str
    addresses: list  # list of strings now

    def get_addresses(self) -> list:
        return [addr.lower() for addr in self.addresses]


def load_wallets(path: str = "wallets.json") -> list:
    """Load wallet entities from a JSON file."""
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    entities = []
    for entry in data.get("entities", []):
        entities.append(Entity(
            label=entry["label"],
            addresses=entry.get("addresses", []),
        ))
    return entities
