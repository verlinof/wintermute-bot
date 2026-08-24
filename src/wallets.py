import json
from dataclasses import dataclass


@dataclass
class Entity:
    label: str
    addresses: dict  # chain_id -> list[str]

    def get_addresses(self, chain_id: str) -> list:
        return [addr.lower() for addr in self.addresses.get(chain_id, [])]


def load_wallets(path: str = "wallets.json") -> list:
    """Load wallet entities from a JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    entities = []
    for entry in data.get("entities", []):
        entities.append(Entity(
            label=entry["label"],
            addresses=entry.get("addresses", {}),
        ))
    return entities
