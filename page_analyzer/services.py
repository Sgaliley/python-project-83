from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


def normalize_url(url: str) -> str:
    '''Нормализует URL.'''
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def fetch_page_data(url: str) -> dict:
    '''Получает данные страницы.'''
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    return {
        'status_code': response.status_code,
        'h1': soup.h1.get_text(strip=True) if soup.h1 else '',
        'title': soup.title.get_text(strip=True) if soup.title else '',
        'description': soup.find(
            'meta',
            attrs={'name': 'description'})['content'] if soup.find(
                'meta',
                attrs={'name': 'description'}) else ''
    }
