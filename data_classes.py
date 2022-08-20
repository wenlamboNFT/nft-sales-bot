from dataclasses import dataclass, field
from datetime import datetime
import configs.constants as constants
import json
import logging
import logging.config

with open("configs/log_config.json", "r", encoding="UTF-8") as stream:
    config = json.load(stream)
logging.config.dictConfig(config)
logger = logging.getLogger("standard")


@dataclass
class TokenSale:
    """
    Data of given sale transaction
    """

    sort_index: int = field(init=False)
    avax_price_in_usd: float
    raw_sale: dict
    price_floor: float
    last_sales: list

    def __post_init__(self):
        self.sort_index = self.last_sales[0]["timestamp"]
        self.transactionID: str = self.raw_sale["id"]
        self.contractId: str = self.raw_sale["collection"]
        self.tokenID: int = self.raw_sale["tokenId"]
        self.verified: str = self.raw_sale["verified"]
        self.date: datetime = datetime.utcfromtimestamp(
            int(self.last_sales[0]["timestamp"])
        )
        self.priceAVAX = round(int(self.last_sales[0]["price"]) * 10 ** (-18), 3)
        self.priceUSD: float = round(float(self.avax_price_in_usd) * self.priceAVAX, 1)

        self.isTakerAsk: bool = self.last_sales[0]["isTakerAsk"]

        self.soldByFull = self.last_sales[0]["fromAddress"]
        self.boughtByFull = self.last_sales[0]["toAddress"]
        self.soldBy: str = self.soldByFull[:5] + "..." + self.soldByFull[-4:]
        self.boughtBy: str = self.boughtByFull[:5] + "..." + self.boughtByFull[-4:]

        if self.last_sales[0]["image"]:
            self.imgLink: str = self.last_sales[0]["image"].replace(" ", "%20")
        else:
            self.imgLink = ""
        self.collectionName: str = self.last_sales[0]["collectionName"]
        if len(self.last_sales) == 2:
            self.lastSale: float = round(
                int(self.last_sales[1]["price"]) * 10 ** (-18), 2
            )
        else:
            self.lastSale: float = None
        if self.last_sales[0]["name"] is not None:
            self.NFTname: str = self.last_sales[0]["name"]
        elif self.last_sales[0]["collectionSymbol"] is not None:
            self.NFTname: str = (
                str(self.last_sales[0]["collectionSymbol"]) + " #" + str(self.tokenID)
            )
        else:
            self.NFTname: str = str(self.collectionName) + " #" + str(self.tokenID)


@dataclass
class EmbedData:
    """
    Set values that will be used to create embed sent to Discord
    """

    token_sale: TokenSale

    def __post_init__(self):
        self.image_url = f"{constants.joepegs_cdn}{self.token_sale.imgLink}"
        self.joepegs_token_url = f"https://joepegs.com/item/{self.token_sale.contractId}/{self.token_sale.tokenID}"

        seller_url = f"https://joepegs.com/profile/{self.token_sale.soldByFull}"
        buyer_url = f"https://joepegs.com/profile/{self.token_sale.boughtByFull}"

        if self.token_sale.isTakerAsk:
            self.taker_value = (
                f"[{self.token_sale.soldBy}](<{seller_url}>) "
                f"accepted bid by [{self.token_sale.boughtBy}](<{buyer_url}>)"
            )
        else:
            self.taker_value = (
                f"[{self.token_sale.soldBy}](<{seller_url}>)'s "
                f"ask filled by [{self.token_sale.boughtBy}](<{buyer_url}>)"
            )

        self.embed_title_value = f"New sale on JOEPEGS - [{self.token_sale.NFTname}](<{self.joepegs_token_url}>) sold!"

        if self.token_sale.verified in ["verified", "verified_trusted"]:
            self.embed_title_name = f"{self.token_sale.collectionName}"
            self.embed_thumbnail_url = constants.thumbnail_urls["verified"]
        elif self.token_sale.verified == "blocklisted":
            self.embed_title_name = (
                f"{self.token_sale.collectionName} - {self.token_sale.verified}"
            )
            self.embed_thumbnail_url = constants.thumbnail_urls["blocklisted"]
        elif self.token_sale.verified == "unverified":
            self.embed_title_name = (
                f"{self.token_sale.collectionName} - {self.token_sale.verified}"
            )
            self.embed_thumbnail_url = constants.thumbnail_urls["unverified"]
        else:
            self.embed_title_name = ""
            self.embed_thumbnail_url = ""
            logger.warning(
                "verified parameter not in [verified, verified_trusted, blocklisted, unverified]"
            )

        self.sold_for_value = (
            f"{self.token_sale.priceAVAX} AVAX [{self.token_sale.priceUSD} USD]"
        )

        if self.token_sale.lastSale:
            self.last_sold_for = f"{self.token_sale.lastSale} AVAX"
        else:
            self.last_sold_for = "Never sold before!"

        self.floor_text = self.get_relation_with_floor()
        self.floor_value = f"{self.token_sale.price_floor} AVAX - {self.floor_text}\n{self.taker_value}"

        day = self.token_sale.date.strftime("%A")
        self.footer = f"Sold on {day[:3]}, {self.token_sale.date} UTC"

    def get_relation_with_floor(self) -> str:
        if self.token_sale.price_floor == 0:
            return ""
        elif self.token_sale.price_floor == self.token_sale.priceAVAX:
            return "Sold for floor price!"
        elif float(self.token_sale.price_floor) > self.token_sale.priceAVAX:
            return f"Sold {round(100 - 100 * self.token_sale.priceAVAX / self.token_sale.price_floor)}% below floor!"
        elif self.token_sale.price_floor < self.token_sale.priceAVAX:
            return f"Sold {round(100 * self.token_sale.priceAVAX / self.token_sale.price_floor - 100)}% over floor!"
        else:
            return ""
