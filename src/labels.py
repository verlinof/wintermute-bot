"""
Known EVM Addresses Directory for Market Makers, Exchanges, and Routers.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

# Built-in directory of verified exchange & market maker addresses across EVM chains
KNOWN_LABELS: dict[str, str] = {
    # --- Binance Main / Hot / Cold Wallets ---
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
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": "Binance: Hot Wallet 6",
    "0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67": "Binance: Hot Wallet 8",
    "0xab5c66752a9e8167967685f1450532fb96d5d24f": "Binance: Hot Wallet 14",
    "0x7b855566a504b2a3a14e96e05d0fa83a37cfc84c": "Binance: Hot Wallet 19",
    "0x3c783c21a0383057d128bae431894a5c19fceac0": "Binance: Hot Wallet 21",
    "0x7a6be30843cc1cf63d3c8c67c514800e84b8eb25": "Binance: Hot Wallet 22",
    "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503": "Binance: Hot Wallet",
    "0xe2fc31f816a9b94326492132018c3aecc4a93ae1": "Binance: Exchange Wallet",
    
    # --- Binance L2 / Arbitrum / BSC / Polygon / Base Wallets ---
    "0xb38e8c17e38363af6ebdcb3dae12e0243582891d": "Binance: Hot Wallet (Arbitrum)",
    "0x4c20794ec4dd83f4bba740ee428d0229337ba18a": "Binance: Hot Wallet 2 (Arbitrum)",
    "0xb2cb96ff864ab1a80be3577d6f51950e3ce18428": "Binance: Hot Wallet (Polygon)",
    "0x8894e0a0c962cb723c1976a4421c95949be2d4e3": "Binance: Cold Wallet (Multi-chain)",
    "0x0000000000000000000000000000000000001004": "Binance: System Deposit",

    # --- Binance Common Deposit & Aggregator Wallets ---
    "0x3356bf1608620b78426dafb9f6c7704df344f6f2": "Binance: Deposit Address",
    "0xf689c56b7db0248ad94943fcfd4fc68ef384d5c9": "Binance: Deposit Address 2",
    "0x98c412f1cf5877c8e9b673df7819ad77884d5eb6": "Binance: User Deposit",
    "0x647087612f0010baec9ec1e0ea2fa4df69924e39": "Binance: User Deposit 2",
    "0xbee71a74dcfc9a444a956104bc18e00e0feab790": "Binance: User Deposit 3",
    "0x001866ae5b3de6caa5a51543fd9fb64f524f5478": "Binance: User Deposit 4",
    "0x940c31be94511ef5b8dd2f0b0c6bbba34aa7dc49": "Binance: User Deposit 5",
    "0xa71b308be79893d56b0632a67e716181f88eb221": "Binance: User Deposit 6",

    # --- Coinbase ---
    "0xa1d8d972560c2f8144af871db508f0b0b10a3fbf": "Coinbase: Hot Wallet 1",
    "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase: Hot Wallet 2",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase: Hot Wallet 3",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Coinbase: Cold Storage",
    "0xdb3c617de0f511223033b907b88982e2ee929849": "Coinbase: Prime",
    "0x3cd751e6b0078be393132286c442345e5dc49699": "Coinbase: Commerce",
    "0xeb2629a2734e272bcc07bda959863f316f4bd4cf": "Coinbase: Hot Wallet 4",

    # --- Wintermute ---
    "0xdbf5e9c5206d0db70a90108bf936da60221dc080": "Wintermute: Trading 1",
    "0x00000000ae3479303288527fd4491a566627c244": "Wintermute: Trading 2",
    "0x4f860b019761d220e371a742802d0846501796ee": "Wintermute: Trading 3",
    "0x1cd0440b3f9f116010ff74cfc73752e89fa94639": "Wintermute: Market Maker",
    "0x15b2efeeae97926180556e4c7402094254c41496": "Wintermute: OTC",

    # --- OKX ---
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": "OKX: Hot Wallet 1",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "OKX: Hot Wallet 2",
    "0x5041ed759dd4afc3a72b8192c143f72f4724081a": "OKX: Hot Wallet 3",
    "0x23682d15de146deee086fb4b5952d4399c68a04b": "OKX: Deposit Address",

    # --- Bybit ---
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40": "Bybit: Hot Wallet 1",
    "0x1db3439a222c519ab44bb1144fc28167b4fa6ee6": "Bybit: Hot Wallet 2",
    "0xee5b5b9230e76fb871493070743fc3a817449bdc": "Bybit: Hot Wallet 3",

    # --- Kraken ---
    "0x2a0c0dbecc7e4d658f48e01e3fa353f44050c208": "Kraken: Hot Wallet 1",
    "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13": "Kraken: Hot Wallet 2",
    "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0": "Kraken: Hot Wallet 3",

    # --- Gate.io / KuCoin / Crypto.com / Bitfinex / Robinhood ---
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": "Gate.io: Hot Wallet 1",
    "0xd6216fc19db775df9774a6e33526131da7d19a2c": "KuCoin: Hot Wallet 1",
    "0x75e89d5979e4f6fba9f97c104c2f0afb3f1dcb88": "Crypto.com: Wallet",
    "0x876eabf441b2ee5b5b0554dd502a8e0600950cfa": "Bitfinex: Hot Wallet 1",
    "0x7356eb3e207e862ab039023410e53a25883d6a2a": "Robinhood: Hot Wallet",

    # --- Market Makers & Institutional (Jump, DWF, Cumberland, FalconX, GSR) ---
    "0x742d35cc6634c0532925a3b844bc454e4438f44e": "Bitfinex: Cold Storage",
    "0x9c43b3558fe0ca765eb26d2146cbbf0f7b57e754": "DWF Labs: Wallet",
    "0x1870679e1aa45f9b5522e8f85526549c40552b78": "Cumberland: Trading",
    "0xb888be62d645e99f0dc4e135541bbfb91d24c888": "FalconX: Hot Wallet",
    "0x98c3d3183c4b8a650614ad179a1a98be0a8d6b8e": "Jump Trading: Wallet",
    "0x2e2938a14b5f884f67c4e61376ce5b3b5581c7e9": "GSR Markets: Wallet",

    # --- Major DEX & Routers ---
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap: Router v3",
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": "Uniswap: Universal Router",
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b": "Uniswap: Universal Router 2",
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap: Router v2",
    "0x1111111254eeb25477b68fb85ed929f73a960582": "1inch: Aggregator v4",
    "0x111111125421ca6dc452d289314280a0f8842a65": "1inch: Aggregator v5",
    "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch: Aggregator v6",
    "0x00000000006c3852cbef3e08e8df289169ede581": "OpenSea: Seaport",
}

# Cache for file-based custom labels
_file_labels_cache: dict[str, str] | None = None


def load_file_labels(path: str = "labels.json") -> dict[str, str]:
    """Load custom labels from a JSON file (e.g. labels.json or data/labels.json)."""
    global _file_labels_cache
    if _file_labels_cache is not None:
        return _file_labels_cache

    labels: dict[str, str] = {}
    for p in (path, os.path.join("data", "labels.json")):
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for addr, lbl in data.items():
                        if not addr.startswith("_"):
                            labels[str(addr).lower()] = str(lbl)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "address" in item and "label" in item:
                            labels[str(item["address"]).lower()] = str(item["label"])
                logger.info("Loaded %d custom labels from %s", len(labels), p)
                break
            except Exception as e:
                logger.warning("Failed to parse custom labels file %s: %s", p, e)

    _file_labels_cache = labels
    return labels


def get_address_label(address: str, custom_labels: dict[str, str] | None = None) -> str:
    """Return a human-readable label for an address if known."""
    addr_lower = address.lower()
    
    # 1. Custom labels passed explicitly (e.g. from wallets.json)
    if custom_labels and addr_lower in custom_labels:
        return custom_labels[addr_lower]
        
    # 2. File-based custom labels (labels.json)
    file_labels = load_file_labels()
    if addr_lower in file_labels:
        return file_labels[addr_lower]
        
    # 3. Built-in known exchange/MM labels
    if addr_lower in KNOWN_LABELS:
        return KNOWN_LABELS[addr_lower]
        
    return "Unknown / External Wallet"

