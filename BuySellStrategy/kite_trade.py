import requests
from dateutil.parser import parse


class KiteAPI:
    # Products
    PRODUCT_MIS = "MIS"
    PRODUCT_CNC = "CNC"
    PRODUCT_NRML = "NRML"
    PRODUCT_CO = "CO"

    # Order types
    ORDER_TYPE_MARKET = "MARKET"
    ORDER_TYPE_LIMIT = "LIMIT"
    ORDER_TYPE_SLM = "SL-M"
    ORDER_TYPE_SL = "SL"

    # Varieties
    VARIETY_REGULAR = "regular"
    VARIETY_CO = "co"
    VARIETY_AMO = "amo"

    # Transaction type
    TRANSACTION_TYPE_BUY = "BUY"
    TRANSACTION_TYPE_SELL = "SELL"

    # Validity
    VALIDITY_DAY = "DAY"
    VALIDITY_IOC = "IOC"

    # Exchanges
    EXCHANGE_NSE = "NSE"
    EXCHANGE_BSE = "BSE"
    EXCHANGE_NFO = "NFO"
    EXCHANGE_CDS = "CDS"
    EXCHANGE_BFO = "BFO"
    EXCHANGE_MCX = "MCX"

    def __init__(self, enctoken):
        self.headers = {"Authorization": f"enctoken {enctoken}"}
        self.session = requests.Session()
        self.root_url = "https://api.kite.trade"

    def _make_request(self, method, endpoint, params=None, data=None):
        url = f"{self.root_url}{endpoint}"
        response = self.session.request(method, url, params=params, data=data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def _parse_candles(self, candles):
        parsed_candles = []
        for candle in candles:
            parsed_candle = {
                "date": parse(candle[0]),
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5],
            }
            if len(candle) == 7:
                parsed_candle["oi"] = candle[6]
            parsed_candles.append(parsed_candle)
        return parsed_candles

    def instruments(self, exchange=None):
        response = self._make_request("GET", "/instruments")
        instruments = []
        for row in response:
            if exchange is None or exchange == row["exchange"]:
                instruments.append({
                    "instrument_token": int(row["instrument_token"]),
                    "exchange_token": row["exchange_token"],
                    "tradingsymbol": row["tradingsymbol"],
                    "name": row["name"],
                    "last_price": float(row["last_price"]),
                    "expiry": parse(row["expiry"]).date() if row["expiry"] else None,
                    "strike": float(row["strike"]),
                    "tick_size": float(row["tick_size"]),
                    "lot_size": int(row["lot_size"]),
                    "instrument_type": row["instrument_type"],
                    "segment": row["segment"],
                    "exchange": row["exchange"]
                })
        return instruments

    def quote(self, instruments):
        response = self._make_request("GET", "/quote", params={"i": instruments})
        return response["data"]

    def ltp(self, instruments):
        response = self._make_request("GET", "/quote/ltp", params={"i": instruments})
        return response["data"]

    def historical_data(self, instrument_token, from_date, to_date, interval, continuous=False, oi=False):
        params = {
            "from": from_date,
            "to": to_date,
            "interval": interval,
            "continuous": int(continuous),
            "oi": int(oi)
        }
        response = self._make_request("GET", f"/instruments/historical/{instrument_token}/{interval}", params=params)
        return self._parse_candles(response["data"]["candles"])

    def holdings(self):
        response = self._make_request("GET", "/oms/portfolio/holdings")
        return response["data"]

    def margins(self):
        response = self._make_request("GET", "/user/margins")
        return response["data"]

    def orders(self):
        response = self._make_request("GET", "/orders")
        return response["data"]

    def positions(self):
        response = self._make_request("GET", "/portfolio/positions")
        return response["data"]

    def place_order(self, variety, **params):
        response = self._make_request("POST", f"/orders/{variety}", data=params)
        return response["data"]["order_id"]

    def modify_order(self, variety, order_id, **params):
        response = self._make_request("PUT", f"/orders/{variety}/{order_id}", data=params)
        return response["data"]["order_id"]

    def cancel_order(self, variety, order_id, parent_order_id=None):
        data = {"parent_order_id": parent_order_id} if parent_order_id else {}
        response = self._make_request("DELETE", f"/orders/{variety}/{order_id}", data=data)
        return response["data"]["order_id"]


def get_enctoken(userid, password, twofa):
    session = requests.Session()
    response = session.post('https://kite.zerodha.com/api/login', data={"user_id": userid, "password": password})
    response = session.post('https://kite.zerodha.com/api/twofa', data={
        "request_id": response.json()['data']['request_id'],
        "twofa_value": twofa,
        "user_id": response.json()['data']['user_id']
    })
    enctoken = response.cookies.get('enctoken')
    if enctoken:
        return enctoken
    else:
        raise Exception("Enter valid details !!!!")
