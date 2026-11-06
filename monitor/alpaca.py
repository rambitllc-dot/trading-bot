"""Minimal Alpaca trading client for the autopilot (account, positions, market clock, market orders)."""
import requests

PAPER_URL = "https://paper-api.alpaca.markets"
LIVE_URL = "https://api.alpaca.markets"


class AlpacaError(Exception):
    pass


class Alpaca:
    def __init__(self, key, secret, live=False):
        self.url = LIVE_URL if live else PAPER_URL
        self.headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}

    def _req(self, method, path, **kw):
        r = requests.request(method, self.url + path, headers=self.headers, timeout=30, **kw)
        if r.status_code >= 400:
            raise AlpacaError(f"Alpaca {r.status_code}: {r.text[:300]}")
        return r.json() if r.text else {}

    def account(self):
        return self._req("GET", "/v2/account")

    def positions(self):
        return self._req("GET", "/v2/positions")

    def clock(self):
        return self._req("GET", "/v2/clock")

    def order(self, order_id):
        return self._req("GET", f"/v2/orders/{order_id}")

    def close(self, symbol):
        """Sell the whole position at market."""
        return self._req("DELETE", f"/v2/positions/{symbol}")

    def buy(self, symbol, dollars):
        return self._req("POST", "/v2/orders", json={"symbol": symbol, "notional": f"{dollars:.2f}", "side": "buy",
                                                     "type": "market", "time_in_force": "day"})
