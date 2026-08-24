from dataclasses import dataclass


@dataclass
class Chain:
    id: str
    name: str
    explorer_base_url: str
    explorer_tx_url: str


CHAINS: list = [
    Chain(
        id="ethereum",
        name="Ethereum",
        explorer_base_url="https://api.etherscan.io/api",
        explorer_tx_url="https://etherscan.io/tx/",
    ),
    Chain(
        id="arbitrum",
        name="Arbitrum",
        explorer_base_url="https://api.arbiscan.io/api",
        explorer_tx_url="https://arbiscan.io/tx/",
    ),
    Chain(
        id="bsc",
        name="BSC",
        explorer_base_url="https://api.bscscan.com/api",
        explorer_tx_url="https://bscscan.com/tx/",
    ),
    Chain(
        id="optimism",
        name="Optimism",
        explorer_base_url="https://api-optimistic.etherscan.io/api",
        explorer_tx_url="https://optimistic.etherscan.io/tx/",
    ),
    Chain(
        id="base",
        name="Base",
        explorer_base_url="https://api.basescan.org/api",
        explorer_tx_url="https://basescan.org/tx/",
    ),
]
