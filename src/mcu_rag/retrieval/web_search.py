"""
Simple web search helper using DuckDuckGo.
"""
from __future__ import annotations

from typing import List, Dict

import requests
from bs4 import BeautifulSoup


def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Perform a basic web search and return a list of results.

    This helper first tries the DuckDuckGo HTML interface and
    falls back to the DuckDuckGo instant-answer API if parsing fails.

    Each result dict contains ``title``, ``url`` and ``snippet``.
    """
    results: List[Dict[str, str]] = []

    # try HTML scraping of the lightweight DDG endpoint
    try:
        resp = requests.post("https://duckduckgo.com/html", data={"q": query}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for div in soup.find_all("div", class_="result")[:max_results]:
            link = div.find("a", class_="result__a")
            if not link or not link.get("href"):
                continue
            title = link.get_text(strip=True)
            href = link["href"]
            snippet_tag = div.find("a", class_="result__snippet")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            results.append({"title": title, "url": href, "snippet": snippet})
        if results:
            return results
    except Exception:  # pragma: no cover - network variability
        pass

    # fallback: instant-answer API (not true search but may yield something)
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            },
            timeout=10,
        )
        data = resp.json()
        abstract = data.get("AbstractText") or data.get("Definition") or data.get("Answer")
        if abstract:
            results.append({
                "title": "DuckDuckGo Abstract",
                "url": data.get("AbstractURL", ""),
                "snippet": abstract,
            })
        for item in data.get("RelatedTopics", [])[: max_results - len(results)]:
            if isinstance(item, dict):
                results.append({
                    "title": item.get("Text", ""),
                    "url": item.get("FirstURL", ""),
                    "snippet": "",
                })
        return results
    except Exception:  # pragma: no cover
        return []
