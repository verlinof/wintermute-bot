from dataclasses import dataclass


@dataclass
class Chain:
    id: str
    name: str
    chain_id: int
    explorer_tx_url: str
    defillama_prefix: str


# Only keeping chains supported by Etherscan V2 Free Tier
CHAINS: list = [
    Chain(
        id="ethereum",
        name="Ethereum",
        chain_id=1,
        explorer_tx_url="https://etherscan.io/tx/",
        defillama_prefix="ethereum",
    ),
    Chain(
        id="arbitrum",
        name="Arbitrum",
        chain_id=42161,
        explorer_tx_url="https://arbiscan.io/tx/",
        defillama_prefix="arbitrum",
    ),
    Chain(
        id="polygon",
        name="Polygon",
        chain_id=137,
        explorer_tx_url="https://polygonscan.com/tx/",
        defillama_prefix="polygon",
    ),
]
