"""
This module is to handle everything related to data collection (historical
or real-time). The command-line utility can call these functions for doing 
things such as getting the most recent price/volume data (spot prices or OHLC).
Requests to the CoinGecko API that take longer than 8 seconds are cancelled. 
"""
import ast
from datetime import datetime, timedelta
from cryptocmd import CmcScraper
from html.parser import HTMLParser
import json
import numpy as np
import os
import re
import requests
import time
from typing import List

url_prefixes = {"coingecko": "https://api.coingecko.com/api/v3/{}", 
                "kraken" : "https://api.kraken.com/0/public/{}"}
sources_list = ["coingecko", "kraken", "cmc"]
max_api_timeout = 8

class KrakenCurrencyTableParser(HTMLParser):
    """
    This class is for the get_ids_kraken() function, which needs to parse a 
    specific HTML document from Kraken's website when the update_cache flag is
    passed for retrieving the coin list from the server.
    
    Attributes: 
        coins               A list to contain the symbols located on the webpage
        ignore_currencies   Currencies to ignore when parsing
    """
    def __init__(self):
        super().__init__()
        self.coins = []
        self.ignore_currencies = ["USD", "EUR", "CAD", "JPY", "GBP", "CHF", 
                                "AUD", "USDT"]
        self.current = False
    def handle_starttag(self, tag, attrs):
        if tag == "strong":
            self.current = True
    def handle_endtag(self, tag):
        pass
    def handle_data(self, data):
        if bool(re.search(r"[A-Z][A-Z][A-Z][A-Z]*", data)) and self.current \
                and data not in self.ignore_currencies:
            self.coins.append(data)
        self.current = False
    def get_coins(self):
        return self.coins

class CMCCurrencyTableParser(KrakenCurrencyTableParser):
    """
    This goes to the CoinMarketCap website and tries to find a list of
    available symbols. This is a temporary solution, since it only return a 
    small subset of available coins.
    """
    def __init__(self):
        super().__init__()
    def handle_starttag(self, tag, attrs):
        if tag == "a" and ('class', 'cmc-table__column-name--symbol cmc-link') in attrs:
            self.current = True
    def handle_endtag(self, tag):
        pass
    def handle_data(self, data):
        if self.current:
            self.coins.append(data)
        self.current = False

class APIInterface:
    def __init__(self):
        pass
    def search_symbols(self, symbol):
        """
        Tries to locate the given symbol in the list of valid input symbols
        :param str symbol: A string to compare with each ID 
        :return: a list symbols matching the input parameter
        """
        found = []
        for sym in list(set(self.get_ids(update_cache = False))):
            if symbol.upper() == sym.upper():
                found.append(sym.upper())
        return found
    def get_ids(self, update_cache = False):
        """
        :return: a list of useable IDs for the specific API
        :rtype: list
        """
        pass
    def get_intervals(self):
        """
        :return: a list of integers for each available interval (in minutes)
        """
        pass
    def is_valid_id(self, id):
        """
        :return: whether a given coin ID is in the list of available IDs
        :rtype: boolean
        """
        ids = self.get_ids()
        return id in ids

class CMC(APIInterface):
    """
    CMC API... Similar to the other two
    """
    def __init__(self):
        super().__init__()
        self.url_prefix = "https://coinmarketcap.com/all/views/all/"
        self.file_name = "data/cmc_id_list.json"
    def get_ids(self, update_cache = False) -> List[str]:
        """
        To get IDs for the CoinMarketCap API, a page on their website is scraped
        for available symbols. Unfortunately, this only returns a small portion 
        of the symbols that are actually available through the API, since the 
        webpage is resistant to scraping (i.e. the web page wants a browser to
        make the requests).

        :return: A list of symbols for available cryptocurrencies on CMC
        :rtype: a list of strings
        """
        if update_cache or not os.path.isfile(self.file_name):
            parser = CMCCurrencyTableParser()
            r = requests.get(self.url_prefix)
            parser.feed(r.text)
            coin_list = parser.get_coins()
            with open(self.file_name, "w") as f:
                json.dump(coin_list, f)
        with open(self.file_name, "r") as f:
            coin_list = json.load(f)
        return coin_list
    def get_intervals(self) -> List[int]:
        return [60 * 24]
    def get_opening_price(self, id):
        """
        Query CMC Scraper API to get the cryptocurrency price data

        :param cryptocurrency_name: String specifying the cryptocurrency symbol to query the CMC scraper with
        :return: 
        """
        assert type(id) is str, "Cryptocurrency name must be a string"
        scraper = CmcScraper(id)
        json_data = ast.literal_eval(scraper.get_data("json"))
        json_data.reverse()
        data = []
        for a in json_data:
            data.append(a["Open"])
        return data
    
class Kraken(APIInterface):
    def __init__(self):
        super().__init__()
    def get_ids(self, update_cache = False):
        """
        If update_cache is true pull the html from a table on Kraken's website 
        and parse it for the available base currencies.

        :return: a list of available symbol pairs offered by Kraken. The base 
            currency will always be USD. (ETHUSD, BTCUSD, LTCUSD, etc.)
        """
        support_url = "https://support.kraken.com/hc/en-us/articles/201893658-Currency-pairs-available-for-trading-on-Kraken"
        file_name = "data/kraken_pairs_list.json"
        if not os.path.isdir("data"): 
            os.mkdir("data")
        if update_cache or not os.path.isfile(file_name):
            r = requests.get(support_url, headers = {"User-Agent" : "Mozilla/5.0"})
            parser = KrakenCurrencyTableParser()
            parser.feed(r.text)
            pairs_list = parser.get_coins()
            for i, coin in enumerate(pairs_list):
                pairs_list[i] = coin
            with open(file_name, "w") as f:
                json.dump(pairs_list, f)
        assert(os.path.isfile(file_name))
        with open(file_name, "r") as f:
            pairs_list = list(set(json.load(f)))
        return pairs_list
    def get_intervals(self):
        """
        :return: The valid intervals (in minutes) for Kraken API 
        """
        return [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]
    def get_ohlc(self, id, vs_currency, days, interval):
        """
        Retrieve OHLC that ranges from a specified date to current. The granularity 
        can be supplied as well. This one might be preferable to the user since it 
        is quite a bit more flexible with time step intervals.

        :param str id: This is a ticker, such as ETH, XRP, BTC, etc.
        :param int days: Number of days to go back to 
        :type days: integer
        :param int interval: An integer which specifies the OHLC time interval in 
            minutes. Valid values are 1, 5, 15, 30, 60, 240, 1440, 10080, 21600
        :type interval: integer or None
        :param str kraken: The external source of the data
        :return: a numpy array of volume (USD) and OHLC data; or None if the request
            cannot be completed either because an invalid symbol pair was passed or
            for some other reason. All fields are converted to np.float32 type
        """
        id = id.upper()
        assert self.is_valid_id(id), "Symbol not found."
        assert interval in self.get_intervals()
        since = time.time() - days * 24 * 60 * 60
        url_suffix = "OHLC?pair={}&since={}&interval={}".format(id.upper() + \
            vs_currency, since, interval)
        url = url_prefixes['kraken'].format(url_suffix)
        response = requests.get(url)
        data = response.json()
        assert len(data['error']) == 0, "Kraken server returned {}.".format(data['error'][0])
        return np.array(data['result'][list(data['result'])[0]], dtype = np.float64)
    def get_opening_price(self, id, vs_currency, days):
        data = self.get_ohlc(id, vs_currency, days, 1440).transpose()
        assert len(data) > 1
        return data[1]

class CoinGecko(APIInterface):
    """
    Interacts with the Coingecko API and handles data retrieval tasks
    """
    def __init__(self):
        super().__init__()
    def search_symbols(self, symbol: str) -> List[str]:
        """
        This attempts to find a symbol in the available IDs list for the API.

        :return: 
        """
        found = []
        for coin_dict in self.get_dict_ids(update_cache = False):
            if symbol.upper() == coin_dict['symbol'].upper():
                found.append(coin_dict['id'])
        return found
    def get_dict_ids(self, update_cache = False):
        """
        If the cache is updated, then the data is saved to a json file first
        then loaded back from that file.

        :param bool update_cache: Whether to update the local JSON files
        :return: a list of dictionaries, each with keys 'id' 'name' 'symbol'
        """
        file_name = "data/coingecko_id_list.json"
        if not os.path.isdir("data"): os.mkdir("data")
        if update_cache or not os.path.isfile(file_name):
            r = requests.get(url_prefixes["coingecko"].format("coins/list"), timeout = max_api_timeout)
            data = r.json()
            with open(file_name, "w") as f:
                json.dump(data, f)
        with open(file_name, "r") as f:
            data = json.load(f)
        return data
    def get_ids(self, update_cache = False):
        """"""
        data = self.get_dict_ids(update_cache)
        ids = [data[i]['id'] for i in range(len(data))]
        return ids
    def get_intervals(self) -> List[int]:
        """
        Return the available intervals (in minutes) for CoinGecko

        :return: a list of integers representing OHLC time intervals in minutes
        """
        return [30, 60 * 4, 60 * 24 * 4]
    def get_range(self) -> np.ndarray:
        """
        :return: The allowed CG range (in days)
        :rtype: numpy array of integers
        """
        return np.array([1, 7, 14, 30, 90, 180, 365])
    def get_ohlc(self, id, vs_currency, days):
        """
        Coingecko's OHLC API for OHLC data. The time step intervals are 
        automatically set by Coingecko as follows:
            1-2 days: 30 minute intervals
            2 < days <= 30: 4 hour intervals
            days > 30: 4 day intervals
        Allowed days:
            1, 7, 14, 30, 90, 180, 365, max

        :param str id: The Coingecko coin ID (ethereum, litecoin, etc.)
        :param str vs_currency: The currency to weigh the coin against (usd, eur, etc.)
        :return: Timestamp (ms), Open, High, Low, Close in a numpy array
        """
        assert self.is_valid_id(id)
        url_suffix = "coins/{}/ohlc?vs_currency={}&days={}".format(id, vs_currency.lower(), days)
        alt_url_suffix = "coins/{}/ohlc?vs_currency={}&days=max".format(id, vs_currency.lower())
        url = url_prefixes['coingecko'].format(url_suffix)
        alt_url = url_prefixes['coingecko'].format(alt_url_suffix)
        response = requests.get(url, timeout = max_api_timeout)
        try:
            data = response.json()
        except Exception as e:
            response = requests.get(alt_url)
            data = response.json()
            print(f'Warning: {days} days is more than the allowed amount for this'
            f' api. Processing wil continue with {len(data)} as this is the max.')
        assert isinstance(data, list)
        return np.array(data)
    def get_opening_price(self, id: str, vs_currency: str, days: int) -> np.ndarray:
        """
        Remember, granularity is determined by the number of days specified. 
        1-2 days: 30 minute intervals
        3 < days < 30: 4 hour intervals
        days > 31: 4 day intervals

        :return: Coingecko's opening price for each time interval 
        :rtype: list
        """
        data = self.get_ohlc(id, vs_currency, days).transpose()
        assert len(data) > 1 
        return data[1]
    def get_market_range(self, id, vs_currency, days):
        """
        Granularity is automatically determined by Coingecko using the following 
        specifications: 
            5-minute intervals: 1 day from query time
            hourly intervals: 1-90 days from query time
            daily intervals: More than 90 days from query time
        Use unix UTC for start and end

        :param str id: A valid Coingecko symbol string
        :param str vs_currency: A valid quote currency (e.g. USD)
        :param int end: The ending time in the range (UTC Unix Timestamp)
        :return: Returns spot price/volume data in json format if coin_id is valid. 
        :rtype: json
        """
        end = time.time()
        start = end - days * 24 * 60 * 60
        assert start < end
        assert(self.is_valid_id(id))
        start = int(start); end = int(end)
        range_str = "coins/{}/market_chart/range?vs_currency={}&from={}&to={}".format(id, vs_currency, start, end)
        url = url_prefixes["coingecko"].format(range_str)
        data = requests.get(url).json()
        return data

def get_available_sources():
    """
    TODO Add CmcScraper 
    :return: list of available sources
    """
    return sources_list

def get_available_symbols_from_source(source: str, update_cache=False) -> List[str]:
    """
    Return the available cryptocurrency symbols from kraken and coingecko
    :return: A list of available symbols 
    :rtype: list
    """
    assert source in sources_list, "Source must be from the following %s" % sources_list
    if source == "coingecko":
        source_api = CoinGecko()
    elif source == "kraken":
        source_api = Kraken()
    elif source == "cmc":
        source_api = CMC()
    else:
        return "No symbols available for {source}"
    ids = source_api.get_ids(update_cache)
    return ids

def pull_CMC_scraper_data(cryptocurrency_name: str) -> np.ndarray:
	"""
	Query CMC Scraper API to get the cryptocurrency price data

	:param cryptocurrency_name: String specifying the cryptocurrency symbol to query the CMC scraper with
	"""
	assert type(cryptocurrency_name) is str, "Cryptocurrency name must be a string"
	scraper = CmcScraper(cryptocurrency_name)
	json_data = ast.literal_eval(scraper.get_data("json"))
	json_data.reverse()
	data = []
	for a in json_data:
		data.append(a["Open"])
	return data

def fifa(n):
    url_suffix = "coins/{}/ohlc?vs_currency={}&days={}"
    url = url_prefixes["coingecko"].format(url_suffix.format("ethereum", "usd", n))
    r = requests.get(url, timeout = 5)
    return r

### For Debugging CoinGecko API
if __name__ == "__main__":
    r = fifa(2)