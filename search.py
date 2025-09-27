# search.py

from typing import Dict
from cat.mad_hatter.decorators import hook
from cat.mad_hatter.decorators import tool

from cat.looking_glass.stray_cat import StrayCat
from cat.log import log
import json

from .helpers import (
    crwl_markdown,
    crawl_markdown_api,
    ddg_search_structured,
)

@tool (return_direct=False)
def duck_duck_go_search(tool_input: str, cat):
    """
    Use this tool when you need to search informations Online.
    tool_input: the query (plain or markdown)
    return: a JSON array of results: [{"title","url","description"}, ...]
    """
    query = (tool_input or "").strip()
    if not query:
        return (
            "Errore: query vuota.\n"
            "Usa questo tool passando una query, ad es.: "
            "duck_duck_go_search('**cheshire cat** hooks reference before_cat_reads_message')"
        )

    ok, results, err = ddg_search_structured(query, limit=8, kl="it-it", kp="-1")
    if ok:
        return json.dumps(results, ensure_ascii=False, indent=2)
    else:
        log.error(f"DDG structured search failed: {err}")
        return f"Ricerca DDG non riuscita. Dettagli: {err}"

@tool(return_direct=False)
def crawl_site_content(tool_input: str, cat):
    """
    Use this tool when you need to read a web page.
    Input: tool_input = URL (with or without scheme)
    Output: Web page content.
    """
    url = (tool_input or "").strip()
    if not url:
        return (
            "Errore: URL mancante.\n"
            "Esempio: crawl_site_content('https://example.com/page')"
        )

    # Aggiunge lo schema se assente (supporta anche raw://)
    if not url.lower().startswith(("http://", "https://", "raw://")):
        url = "https://" + url

    # 1) API Crawl4AI → preferisci fit_markdown
    ok, md, err = crawl_markdown_api(
        url,
        prefer="fit",
        excluded_tags=("form", "header", "footer", "nav", "aside"),
        css_selector="main, article, #main, .main, .content, .post-content, [role='main']",
        table_score_threshold=7,
        citations=False,
    )

    # 2) Fallback CLI (markdown-fit) se API fallisce
    if not ok or not md:
        ok2, out, err2, code = crwl_markdown(url, fit=True)
        if ok2 and out:
            md = out
        else:
            log.error(f"crawl_site_content failed. API: {err} | CLI: code {code}, err: {err2}")
            return f"Estrazione non riuscita.\nAPI: {err}\nCLI: {err2 or f'exit code {code}'}"

    # 3) Troncamento prudente per evitare risposte eccessive
    MAX_CHARS = 30000
    if len(md) > MAX_CHARS:
        md = md[:MAX_CHARS].rsplit("\n", 1)[0] + "\n\n…[troncato]"

    return md


