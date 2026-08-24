"""TSETMC Integration — Fetch live stock data from Tehran Stock Exchange (tsetmc.com).
Provides real-time market data, company profiles, and historical prices.
"""

import re
import httpx
from typing import Optional
from bs4 import BeautifulSoup

# TSETMC base URLs
TSETMC_BASE = "http://tsetmc.com/"
TSETMC_SEARCH_URL = "http://tsetmc.com/Loader.aspx?ParTree=151311&Search="
TSETMC_STOCK_URL = "http://tsetmc.com/Loader.aspx?Partree=15131T&c="
TSETMC_API_URL = "http://cdn.tsetmc.com/api/"

# Map common Iranian stock symbols to TSETMC instrument IDs
SYMBOL_MAP = {
    # Petrochemical
    "خپارس": "66125195175934508",
    "فپارسا": "53867185175934508",
    "شپارس": "13190807175934508",
    "شاراک": "25449188175934508",
    # Banking
    "وبملت": "10057176175934508",
    "وبصادر": "14066177175934508",
    "وتجارت": "39159057175934508",
    "پاسار": "32347690175934508",
    # Metals
    "فولاد": "54095391175934508",
    "فخوز": "27373759175934508",
    "کگل": "11327634175934508",
    # Automotive
    "خودرو": "34946205175934508",
    "خساپا": "63447043175934508",
    # Food
    "کاله": "27373759175934508",
    "گلپا": "70376991175934508",
    # Technology
    "فناوری": "46474801175934508",
    "مداران": "80405333175934508",
}


async def search_symbol(query: str) -> list[dict]:
    """Search for stocks on TSETMC by symbol or name.

    Args:
        query: Stock symbol or company name (Persian/English)

    Returns:
        List of matching stocks with basic info
    """
    results = []

    # First check our local map
    for symbol, inst_id in SYMBOL_MAP.items():
        if query in symbol or query in str(SYMBOL_MAP.get(symbol, "")):
            results.append({
                "symbol": symbol,
                "instrument_id": inst_id,
                "source": "local_map",
            })

    # Try TSETMC search
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            url = TSETMC_SEARCH_URL + query
            response = await client.get(url, follow_redirects=True)
            soup = BeautifulSoup(response.text, "lxml")

            # Find instrument links
            links = soup.find_all("a", href=re.compile(r"c=\d+"))
            seen = set()
            for link in links[:10]:
                href = link.get("href", "")
                match = re.search(r"c=(\d+)", href)
                if match:
                    inst_id = match.group(1)
                    if inst_id not in seen:
                        seen.add(inst_id)
                        results.append({
                            "symbol": link.get_text(strip=True)[:20],
                            "instrument_id": inst_id,
                            "source": "tsetmc_search",
                        })
    except Exception:
        pass

    return results[:10]


async def get_stock_data(instrument_id: str) -> dict:
    """Fetch real-time stock data from TSETMC for a given instrument ID.

    Args:
        instrument_id: TSETMC instrument ID

    Returns:
        dict with price data, volume, market cap, etc.
    """
    result = {
        "instrument_id": instrument_id,
        "available": False,
        "data": None,
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            # Fetch the instrument page
            url = TSETMC_STOCK_URL + instrument_id
            response = await client.get(url, follow_redirects=True)
            html = response.text
            soup = BeautifulSoup(html, "lxml")

            # Extract data from TSETMC's embedded data
            # TSETMC uses a specific div with IDs
            data = _parse_tsetmc_page(soup, html)
            if data:
                result["available"] = True
                result["data"] = data
    except httpx.TimeoutException:
        result["error"] = "Connection to TSETMC timed out"
    except Exception as e:
        result["error"] = str(e)[:200]

    return result


def _parse_tsetmc_page(soup: BeautifulSoup, html: str) -> Optional[dict]:
    """Parse TSETMC instrument page for stock data."""
    data = {}

    # Try to find price data in script blocks
    scripts = soup.find_all("script")

    # Look for the main data object
    for script in scripts:
        if script.string:
            # Instrument name
            name_match = re.search(r'"Title":"([^"]+)"', script.string)
            if name_match:
                data["name"] = name_match.group(1)

            # Last price
            last_price = re.search(r'"PDrCotVal":([\d.]+)', script.string)
            if last_price:
                data["last_price"] = float(last_price.group(1))

            # Closing price
            close_price = re.search(r'"PDClosing":([\d.]+)', script.string)
            if close_price:
                data["closing_price"] = float(close_price.group(1))

            # Open price
            open_price = re.search(r'"PDOpen":([\d.]+)', script.string)
            if open_price:
                data["open_price"] = float(open_price.group(1))

            # High price
            high_price = re.search(r'"PDHigh":([\d.]+)', script.string)
            if high_price:
                data["high_price"] = float(high_price.group(1))

            # Low price
            low_price = re.search(r'"PDLow":([\d.]+)', script.string)
            if low_price:
                data["low_price"] = float(low_price.group(1))

            # Volume
            volume = re.search(r'"QTotTran5J":([\d.]+)', script.string)
            if volume:
                data["volume"] = int(float(volume.group(1)))

            # Value
            value = re.search(r'"QTotCap":([\d.]+)', script.string)
            if value:
                data["value"] = float(value.group(1))

            # Market cap
            market_cap = re.search(r'"ZTotTran":([\d.]+)', script.string)
            if market_cap:
                data["market_cap"] = float(market_cap.group(1))

            # Yesterday price
            yesterday = re.search(r'"PriceYesterday":([\d.]+)', script.string)
            if yesterday:
                data["yesterday_price"] = float(yesterday.group(1))

            # Number of shares
            shares = re.search(r'"ZNamadVal":([\d.]+)', script.string)
            if shares:
                data["shares_outstanding"] = int(float(shares.group(1)))

            # EPS
            eps = re.search(r'"EstimatedEPS":([\d.]+)', script.string)
            if eps:
                data["eps"] = float(eps.group(1))

            # P/E Ratio
            pe = re.search(r'"PE":([\d.]+)', script.string)
            if pe:
                data["pe_ratio"] = float(pe.group(1))

            # Group/sector info
            sector = re.search(r'"CS":"([^"]+)"', script.string)
            if sector:
                data["sector"] = sector.group(1)

    if not data:
        return None

    # Calculate derived metrics
    if "last_price" in data and "yesterday_price" in data:
        yp = data["yesterday_price"]
        lp = data["last_price"]
        if yp > 0:
            data["change_pct"] = round((lp - yp) / yp * 100, 2)
            data["change_value"] = round(lp - yp, 2)

    if "eps" in data and data["eps"] > 0 and "last_price" in data:
        data["forward_pe"] = round(data["last_price"] / data["eps"], 2)

    # Status
    if "change_pct" in data:
        data["status"] = "positive" if data["change_pct"] > 0 else ("negative" if data["change_pct"] < 0 else "unchanged")
    else:
        data["status"] = "unknown"

    return data


def get_popular_symbols() -> list[dict]:
    """Return list of popular Iranian stock symbols for quick access."""
    return [
        {"symbol": "خپارس", "name_en": "Pars Petrochemical", "sector": "Petrochemical"},
        {"symbol": "فولاد", "name_en": "Mobarakeh Steel", "sector": "Metals"},
        {"symbol": "خودرو", "name_en": "Iran Khodro", "sector": "Automotive"},
        {"symbol": "وبملت", "name_en": "Bank Melli", "sector": "Banking"},
        {"symbol": "فخوز", "name_en": "Khuzestan Steel", "sector": "Metals"},
        {"symbol": "خساپا", "name_en": "Saipa", "sector": "Automotive"},
        {"symbol": "وبصادر", "name_en": "Bank Saderat", "sector": "Banking"},
        {"symbol": "وتجارت", "name_en": "Bank Tejarat", "sector": "Banking"},
        {"symbol": "کاله", "name_en": "Kalleh Dairy", "sector": "Food"},
        {"symbol": "فناوری", "name_en": "Fanaavari", "sector": "Technology"},
        {"symbol": "گلپا", "name_en": "Golpayegan", "sector": "Food"},
        {"symbol": "فپارسا", "name_en": "Parsian Oil", "sector": "Oil & Gas"},
    ]


async def get_market_overview() -> dict:
    """Get a quick overview of the Tehran Stock Exchange market."""
    overview = {
        "indices": [],
        "top_gainers": [],
        "top_losers": [],
        "most_traded": [],
        "status": "available",
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            # Fetch TSETMC main page for market indices
            response = await client.get(TSETMC_BASE, follow_redirects=True)
            soup = BeautifulSoup(response.text, "lxml")
            scripts = soup.find_all("script")

            for script in scripts:
                if script.string and "indexData" in str(script.string):
                    # Parse index data
                    idx_matches = re.findall(
                        r'"LVal18AFC":"([^"]+)".*?"Last":([\d.]+).*?"PChange":(-?[\d.]+)',
                        script.string,
                    )
                    for match in idx_matches[:5]:
                        overview["indices"].append({
                            "name": match[0],
                            "value": float(match[1]),
                            "change": float(match[2]),
                        })
    except Exception as e:
        overview["status"] = "unavailable"
        overview["error"] = str(e)[:200]

    # Add popular stocks as default data
    overview["popular_stocks"] = get_popular_symbols()

    return overview
