import requests
from bs4 import BeautifulSoup
import json
from collections import OrderedDict


class WebsiteParser:
    def __init__(self, url, sections):
        self.url = url
        self.sections = sections

    def get_section_content(self, section, soup):
        elements = soup.find_all(class_=section)
        content = []
        for element in elements:
            title = element.find(['h1', 'h2'])
            title_text = title.get_text(strip=True) if title else ""

            if title:
                title.extract()

            text_parts = []
            raw_text = element.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
            for line in lines:
                if line.startswith(('—', '-', '•')):
                    text_parts.append([line])
                else:
                    text_parts.append(line)

            links = OrderedDict()
            for a in element.find_all('a', href=True):
                link = a.get('href')
                links[link] = None

            section_data = {
                "title": title_text,
                "text": text_parts,
                "links": list(links.keys())
            }
            content.append(section_data)

        return content

    def parse_website(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        data = {}
        for section in self.sections:
            data[section] = self.get_section_content(section, soup)

        with open('parsed_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print("Данные успешно сохранены в parsed_data.json")


if __name__ == "__main__":
    try:
        sections = [
            "container-content",
            # "persons",
            # "home__partners-block"
        ]
        parser = WebsiteParser("https://pish.etu.ru/ru/home/dopolnitelnoe-obrazovanie/metody-rentgenovskogo-kontrolya-promyshlennoj-elektroniki", sections)
        parser.parse_website()
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")