from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


def normalize_url(url: str) -> str:
    '''Normalizes URLs.'''
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def fetch_page(url: str) -> str:
    '''Gets HTML pages by URL.'''
    response = requests.get(url)
    response.raise_for_status()
    return response.text, response.status_code


def parse_page(html: str) -> dict:
    '''Parses HTML pages and extracts the desired data.'''
    soup = BeautifulSoup(html, 'html.parser')

    return {
        'h1': soup.h1.get_text(strip=True) if soup.h1 else '',
        'title': soup.title.get_text(strip=True) if soup.title else '',
        'description': (soup.find(
            'meta',
            attrs={'name': 'description'}) or {}).get('content', '')
    }


def fetch_page_data(url: str) -> dict:
    '''Combines fetching and parsing of page data.'''
    html, status_code = fetch_page(url)
    parsed_data = parse_page(html)
    parsed_data['status_code'] = status_code
    return parsed_data
