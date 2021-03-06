import requests
from .util import logger, poolItem, generate_request
import time, json
from urllib.parse import quote
from decimal import *
from parsel import Selector

s = generate_request()

merchant = "genesis_mining"


@logger.catch
def getdata():
    url = "https://www.genesis-mining.com/pricing"
    logger.info(f"get contract list {url}")
    z1 = s.get(url, timeout=60)
    response = Selector(text=z1.text)
    ret = []
    bitcoin_list = [
        "bitcoin-mining",
        "bitcoin-mining-6month",
        "bitcoin-mining-radiant-zero",
        "bitcoin-mining-radiant-zero-6month",
        "ethereum-mining",
    ]

    for b in bitcoin_list:
        gmp_prices = (
            response.xpath(f'//div[@id="{b}"]')
            .xpath('.//li[@class="gmp-price"]/span/text()')
            .extract()
        )
        ths = (
            response.xpath(f'//div[@id="{b}"]')
            .xpath('.//li[@class="gmp-megaw"]/text()')
            .extract()
        )
        _sold_percent = (
            response.xpath(f'//div[@id="{b}"]').xpath('.//a[@title="已售罄"]').extract()
        )
        if _sold_percent:
            sold_percent = 100
        else:
            sold_percent = 10
        gmp_prices = [i.replace(",", "") for i in gmp_prices]
        ths = [x.split(" ")[0].strip() for x in [i for i in ths if i.strip() != ""]]
        if "bitcoin" in b:
            coin = "BTC"
        elif "ethereum" in b:
            coin = "ETH"
        if "6month" in b:
            duration = 6 * 30
        else:
            duration = 730
        if "zero" in b:
            zero = "00"
        else:
            zero = "006"
        for i in range(3):
            ret.append(
                {
                    "upfront_fee": float(gmp_prices[i]),
                    "contract_size": float(ths[i]),
                    "duration": duration,
                    "zero": zero,
                    "b": b,
                    "sold_percent": sold_percent,
                    "coin": coin,
                }
            )
    return ret


def parsedata():
    data = getdata()
    for i in data:
        contract = i
        _id = merchant + "_" + contract["b"] + "_" + str(contract["duration"])
        coin = contract["coin"]
        duration = contract["duration"]
        issuers = merchant
        contract_size = contract["contract_size"]
        electricity_fee = 0.06
        management_fee = 0.0

        ## buy url .5 fix
        if ".5" not in str(contract_size):
            contract_size_url = str(int(contract_size))
        else:
            contract_size_url = str(contract_size)
        if duration == 30 * 6:
            buy_url = f"https://www.genesis-mining.com/upgrade-hashpower?a=sha256_6month{contract['zero']}&p={contract_size_url}"
        else:
            buy_url = f"https://www.genesis-mining.com/upgrade-hashpower?a=sha256_2year{contract['zero']}&p={contract_size_url}"
        upfront_fee = contract["upfront_fee"]
        messari = 0.04
        sold_percent = contract["sold_percent"]
        p = poolItem(
            _id,
            coin,
            duration,
            issuers,
            contract_size,
            electricity_fee,
            management_fee,
            buy_url,
            upfront_fee,
            messari,
            sold_percent,
        )
        p.save2db()


if __name__ == "__main__":
    parsedata()
