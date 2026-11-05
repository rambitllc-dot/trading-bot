"""Black-Scholes price and Greeks, computed locally with the standard library only.

Inputs: spot S, strike K, years to expiry T, annual risk-free rate r, implied volatility sigma.
Outputs per share: delta, gamma, theta (per calendar day), vega (per 1 percentage point of IV).
"""
import math

SQRT_2PI = math.sqrt(2 * math.pi)


def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def norm_pdf(x):
    return math.exp(-0.5 * x * x) / SQRT_2PI


def bs_greeks(option_type, S, K, T, r, sigma):
    """Return dict(price, delta, gamma, theta, vega) or None when inputs can't be priced."""
    if not all(v is not None for v in (S, K, T, sigma)) or S <= 0 or K <= 0 or sigma <= 0:
        return None
    call = option_type == "call"
    if T <= 0:  # at or past expiry: intrinsic value only
        intrinsic = max(S - K, 0) if call else max(K - S, 0)
        itm = intrinsic > 0
        return {"price": intrinsic, "delta": (1.0 if call else -1.0) if itm else 0.0,
                "gamma": 0.0, "theta": 0.0, "vega": 0.0}
    sq = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / sq
    d2 = d1 - sq
    disc = math.exp(-r * T)
    pdf1 = norm_pdf(d1)
    if call:
        price = S * norm_cdf(d1) - K * disc * norm_cdf(d2)
        delta = norm_cdf(d1)
        theta_year = -S * pdf1 * sigma / (2 * math.sqrt(T)) - r * K * disc * norm_cdf(d2)
    else:
        price = K * disc * norm_cdf(-d2) - S * norm_cdf(-d1)
        delta = norm_cdf(d1) - 1
        theta_year = -S * pdf1 * sigma / (2 * math.sqrt(T)) + r * K * disc * norm_cdf(-d2)
    return {"price": price, "delta": delta, "gamma": pdf1 / (S * sq),
            "theta": theta_year / 365.0, "vega": S * pdf1 * math.sqrt(T) / 100.0}
