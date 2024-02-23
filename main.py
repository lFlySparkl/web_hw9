import requests
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_quotes_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        return None

def scrape_author_info(author_url):
    response = requests.get(author_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        author_info = {
            'fullname': soup.find('h3', class_='author-title').text.strip(),
            'born_date': soup.find('span', class_='author-born-date').text.strip(),
            'born_location': soup.find('span', class_='author-born-location').text.strip(),
            'description': soup.find('div', class_='author-description').text.strip()
        }
        return author_info
    else:
        return None

def scrape_all_quotes(base_url, max_quotes=150):
    all_quotes = []
    authors_info = {}

    current_page = 1
    quotes_count = 0

    while quotes_count < max_quotes:
        current_url = f"{base_url}/page/{current_page}/"
        print(f"Processing page: {current_url}")

        page_content = get_quotes_page(current_url)

        if not page_content:
            print(f"Failed to retrieve page: {current_url}")
            break

        quotes = page_content.find_all('div', class_='quote')

        # Проверяем наличие цитат на странице
        if not quotes:
            print(f"No quotes found on page: {current_url}")
            break

        for quote in quotes:
            text = quote.find('span', class_='text').text.strip()
            author_url = urljoin(base_url, quote.find('a')['href'])
            tags = [tag.text.strip() for tag in quote.find_all('a', class_='tag')]

            if author_url not in authors_info:
                authors_info[author_url] = scrape_author_info(author_url)

            author_info = authors_info.get(author_url, {})

            # Перевірка на дублікат цитати за текстом та автором
            if any(q['quote'] == text and q['author']['fullname'] == author_info.get('fullname', '') for q in all_quotes):
                print(f"Skipped duplicate quote: {text} by {author_info.get('fullname', '')}")
                continue  # Пропускаємо дублікат

            quote_info = {
                'tags': tags,
                'author': {
                    'fullname': author_info.get('fullname', ''),
                    'born_date': author_info.get('born_date', ''),
                    'born_location': author_info.get('born_location', ''),
                    'description': author_info.get('description', '')
                },
                'quote': text
            }

            all_quotes.append(quote_info)
            quotes_count += 1

            if quotes_count == max_quotes:
                break

        current_page += 1

    return all_quotes, authors_info

def main():
    base_url = 'http://quotes.toscrape.com'
    all_quotes, authors_info = scrape_all_quotes(base_url, max_quotes=150)

    json_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json')

    if not os.path.exists(json_folder_path):
        os.makedirs(json_folder_path)

    quotes_info = [
        {
            'tags': quote['tags'],
            'author': quote['author']['fullname'],
            'quote': quote['quote']
        }
        for quote in all_quotes
    ]

    with open(os.path.join(json_folder_path, 'quotes.json'), 'w', encoding='utf-8') as quotes_file:
        json.dump(quotes_info, quotes_file, ensure_ascii=False, indent=2)

    # Записываем информацию про авторов в файл authors.json
    with open(os.path.join(json_folder_path, 'authors.json'), 'w', encoding='utf-8') as authors_file:
        json.dump(list(authors_info.values()), authors_file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
