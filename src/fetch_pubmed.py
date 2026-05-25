from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from typing import Any

import requests


EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TIMEOUT = 25


PUBLICATION_TYPE_TERMS = [
    "Randomized Controlled Trial",
    "Clinical Trial, Phase III",
    "Clinical Trial, Phase II",
    "Clinical Trial",
    "Multicenter Study",
    "Guideline",
    "Meta-Analysis",
    "Review",
]


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _journal_query(journals: dict[str, list[str]]) -> str:
    names = []
    for key in ("tier_a", "tier_b", "tier_c"):
        names.extend(journals.get(key, []))
    return " OR ".join(f'"{name}"[Journal]' for name in names)


def _topic_query(topics: dict[str, Any]) -> str:
    terms: list[str] = []
    for topic in topics.values():
        for keyword in topic.get("keywords", []):
            terms.append(f'"{keyword}"[Title/Abstract]')
    terms.extend([
        '"randomized"[Title/Abstract]',
        '"phase 3"[Title/Abstract]',
        '"phase III"[Title/Abstract]',
        '"guideline"[Title/Abstract]',
        '"clinical trial"[Title/Abstract]',
        '"translational"[Title/Abstract]',
    ])
    return " OR ".join(sorted(set(terms)))


def _ptype_query() -> str:
    return " OR ".join(f'"{term}"[Publication Type]' for term in PUBLICATION_TYPE_TERMS)


def _get_text(parent: ET.Element, path: str) -> str:
    found = parent.find(path)
    return _clean("".join(found.itertext())) if found is not None else ""


def _extract_article(article: ET.Element, fallback_topic: str = "") -> dict[str, Any]:
    medline = article.find("MedlineCitation")
    pubmed_data = article.find("PubmedData")
    citation = medline.find("Article") if medline is not None else None
    journal = citation.find("Journal") if citation is not None else None
    pmid = _get_text(medline, "PMID") if medline is not None else ""
    title = _get_text(citation, "ArticleTitle") if citation is not None else ""
    journal_title = _get_text(journal, "Title") if journal is not None else ""

    abstract_parts = []
    if citation is not None:
        for node in citation.findall("./Abstract/AbstractText"):
            label = node.attrib.get("Label")
            text = _clean("".join(node.itertext()))
            if label and text:
                abstract_parts.append(f"{label}: {text}")
            elif text:
                abstract_parts.append(text)
    abstract = "\n".join(abstract_parts)

    authors = []
    if citation is not None:
        for author in citation.findall("./AuthorList/Author")[:8]:
            last = _get_text(author, "LastName")
            fore = _get_text(author, "ForeName")
            collective = _get_text(author, "CollectiveName")
            name = collective or " ".join(x for x in [fore, last] if x)
            if name:
                authors.append(name)

    doi = ""
    if pubmed_data is not None:
        for aid in pubmed_data.findall("./ArticleIdList/ArticleId"):
            if aid.attrib.get("IdType") == "doi":
                doi = _clean(aid.text)
                break

    published = ""
    if journal is not None:
        date_node = journal.find("./JournalIssue/PubDate")
        if date_node is not None:
            year = _get_text(date_node, "Year")
            month = _get_text(date_node, "Month")
            day = _get_text(date_node, "Day")
            published = "-".join(x for x in [year, month, day] if x)

    pub_types = []
    if citation is not None:
        for ptype in citation.findall("./PublicationTypeList/PublicationType"):
            text = _clean(ptype.text)
            if text:
                pub_types.append(text)

    return {
        "source": "PubMed",
        "source_region": "intl",
        "source_language": "en",
        "news_origin": "PubMed paper",
        "content_bucket": "intl_news",
        "topic": fallback_topic,
        "topic_cn": "",
        "id": pmid or doi or title,
        "pmid": pmid,
        "doi": doi,
        "title": title,
        "journal": journal_title,
        "published": published,
        "authors": authors,
        "abstract": abstract,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else (f"https://doi.org/{doi}" if doi else ""),
        "publication_types": pub_types,
    }


def _esearch(session: requests.Session, query: str, retmax: int = 80) -> list[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": retmax,
        "sort": "pub date",
        "datetype": "pdat",
        "reldate": 7,
    }
    # PubMed queries that combine many top journals and topics can exceed URL limits.
    # E-utilities accepts POST form data, which keeps the query stable in Actions.
    resp = session.post(f"{EUTILS}/esearch.fcgi", data=params, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data.get("esearchresult", {}).get("idlist", [])


def _efetch(session: requests.Session, ids: list[str]) -> list[dict[str, Any]]:
    if not ids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml",
    }
    resp = session.get(f"{EUTILS}/efetch.fcgi", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    return [_extract_article(article) for article in root.findall("./PubmedArticle")]


def fetch_pubmed(journals: dict[str, Any], topics: dict[str, Any], errors: list[str] | None = None) -> list[dict[str, Any]]:
    errors = errors if errors is not None else []
    session = requests.Session()
    query = f"({_journal_query(journals)}) AND (({_topic_query(topics)}) OR ({_ptype_query()}))"
    try:
        ids = _esearch(session, query, retmax=120)
        time.sleep(0.34)
        items = _efetch(session, ids)
        return [item for item in items if item.get("title")]
    except Exception as exc:
        errors.append(f"PubMed: {exc!r}")
        return []
