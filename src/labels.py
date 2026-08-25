"""
Known EVM Addresses Directory for Market Makers, Exchanges, and Routers.
"""

KNOWN_LABELS: dict[str, str] = {
    # Binance
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance: Hot Wallet 20",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance: Hot Wallet 15",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance: Hot Wallet 16",
    "0x56ed6164983c7923168b4317139f1715185123b4": "Binance: Hot Wallet 17",
    "0x9696e3794e2e28328c894236a9da0151121d5a7d": "Binance: Hot Wallet 18",
    "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8": "Binance: Hot Wallet 7",
    "0xf977814e90da44bfa03b6295a0616a897441acec": "Binance: Cold Wallet 8",
    "0x5a52e96bacdabb82fd05763e25335261b270efcb": "Binance: Cold Wallet 2",
    "0x8894e0a0c962cb723c1976a4421c95949be2d4e3": "Binance: Cold Wallet 1",
    "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": "Binance: Hot Wallet 1",
    "0xd551234ae421e3bcba99a0da6d73607403239e7a": "Binance: Hot Wallet 2",
    "0x0681d8db095565fe8a346fa0277bffde9c0edbbf": "Binance: Hot Wallet 3",
    "0xfe9e8709d3215310070467757d8403a742de8053": "Binance: Hot Wallet 4",
    "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503": "Binance: Hot Wallet",
    "0xe2fc31f816a9b94326492132018c3aecc4a93ae1": "Binance: Exchange Wallet",

    # Coinbase
    "0xa1d8d972560c2f8144af871db508f0b0b10a3fbf": "Coinbase: Hot Wallet 1",
    "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase: Hot Wallet 2",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase: Hot Wallet 3",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Coinbase: Cold Storage",
    "0xdb3c617de0f511223033b907b88982e2ee929849": "Coinbase: Prime",

    # Wintermute
    "0xdbf5e9c5206d0db70a90108bf936da60221dc080": "Wintermute: Trading 1",
    "0x00000000ae3479303288527fd4491a566627c244": "Wintermute: Trading 2",
    "0x4f860b019761d220e371a742802d0846501796ee": "Wintermute: Trading 3",
    "0x1cd0440b3f9f116010ff74cfc73752e89fa94639": "Wintermute: Market Maker",
    "0x15b2efeeae97926180556e4c7402094254c41496": "Wintermute: OTC",

    # OKX / Bybit / Kraken / Gate / KuCoin
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": "OKX: Hot Wallet",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "OKX: Hot Wallet 2",
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40": "Bybit: Hot Wallet 1",
    "0x1db3439a222c519ab44bb1144fc28167b4fa6ee6": "Bybit: Hot Wallet 2",
    "0x2a0c0dbecc7e4d658f48e01e3fa353f44050c208": "Kraken: Hot Wallet 1",
    "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13": "Kraken: Hot Wallet 2",
    "0x75e89d5979e4f6fba9f97c104c2f0afb3f1dcb88": "Crypto.com: Wallet",

    # Major DEX & Routers
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap: Router v3",
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": "Uniswap: Universal Router",
    "0x1111111254eeb25477b68fb85ed929f73a960582": "1inch: Aggregator v4",
    "0x111111125421ca6dc452d289314280a0f8842a65": "1inch: Aggregator v5",
    "0x00000000006c3852cbef3e08e8df289169ede581": "OpenSea: Seaport",
}


def get_address_label(address: str, custom_labels: dict[str, str] | None = None) -> str:
    """Return a human-readable label for an address if known."""
    addr_lower = address.lower()
    if custom_labels and addr_lower in custom_labels:
        return custom_labels[addr_lower]
    if addr_lower in KNOWN_LABELS:
        return KNOWN_LABELS[addr_lower]
    return "Unknown / External Wallet"
