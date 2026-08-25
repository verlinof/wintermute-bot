from dataclasses import dataclass


@dataclass
class Chain:
    id: str
    name: str
    chain_id: int
    explorer_tx_url: str
    defillama_prefix: str


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
    Chain(
        id="bsc",
        name="BSC",
        chain_id=56,
        explorer_tx_url="https://bscscan.com/tx/",
        defillama_prefix="bsc",
    ),
    Chain(
        id="optimism",
        name="Optimism",
        chain_id=10,
        explorer_tx_url="https://optimistic.etherscan.io/tx/",
        defillama_prefix="optimism",
    ),
    Chain(
        id="base",
        name="Base",
        chain_id=8453,
        explorer_tx_url="https://basescan.org/tx/",
        defillama_prefix="base",
    ),
]
