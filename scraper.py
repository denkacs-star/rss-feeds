#!/usr/bin/env python3
"""
RSS Feed Generator für Carnegie Россия-Евразия Политика
"""

from playwright.sync_api import sync_playwright
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
import sys
import os
import re

def parse_russian_date(date_text):
    """Parse russische Datumsangaben wie '23 января 2026 г.'"""
    months_ru = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    
    try:
        # Format: "23 января 2026 г."
        match = re.search(r'(\d+)\s+(\w+)\s+(\d{4})', date_text)
        if match:
            day = int(match.group(1))
            month_name = match.group(2)
            year = int(match.group(3))
            month = months_ru.get(month_name, 1)
            return datetime(year, month, day, tzinfo=pytz.UTC)
    except:
        pass
    
    return datetime.now(pytz.UTC)


def scrape_carnegie():
    """Scrape Carnegie Russia-Eurasia Politika Artikel"""
    print("🔍 Starte Scraping von Carnegie...")
    
    articles = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            url = 'https://carnegieendowment.org/ru/russia-eurasia/politika'
            print(f"📄 Lade {url}")
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Warte auf die Artikel
            page.wait_for_selector('article', timeout=10000)
            
            # Finde alle Artikel-Elemente
            article_elements = page.query_selector_all('article')
            
            print(f"✅ {len(article_elements)} Artikel gefunden")
            
            for idx, article_elem in enumerate(article_elements[:20]):  # Max 20 Artikel
                try:
                    # Link extrahieren (das <a> Element innerhalb des <article>)
                    link_elem = article_elem.query_selector('a[href*="/politika/"]')
                    if not link_elem:
                        continue
                    
                    link = link_elem.get_attribute('href')
                    if link and not link.startswith('http'):
                        link = f"https://carnegieendowment.org{link}"
                    
                    # Titel extrahieren (generic Element mit dem Titel-Text)
                    title_elem = article_elem.query_selector('generic, h1, h2, h3, [role="heading"]')
                    if not title_elem:
                        continue
                    title = title_elem.inner_text().strip()
                    
                    # Überspringen wenn der Titel "Комментарий" oder "Подкаст" ist (das sind Labels)
                    if title in ['Комментарий', 'Подкаст', 'Carnegie Politika']:
                        # Versuche den nächsten generic zu finden
                        all_generics = article_elem.query_selector_all('generic')
                        for gen in all_generics:
                            text = gen.inner_text().strip()
                            if len(text) > 20 and text not in ['Комментарий', 'Подкаст', 'Carnegie Politika']:
                                title = text
                                break
                    
                    # Beschreibung extrahieren (das zweite generic Element)
                    desc_elements = article_elem.query_selector_all('generic')
                    description = title  # Fallback
                    for desc_elem in desc_elements:
                        text = desc_elem.inner_text().strip()
                        if len(text) > 50 and text != title:
                            description = text[:500]
                            break
                    
                    # Datum extrahieren (listitem mit Datum)
                    date_elem = article_elem.query_selector('listitem[class*=""], list listitem:last-child')
                    pub_date = datetime.now(pytz.UTC)
                    
                    if date_elem:
                        date_text = date_elem.inner_text().strip()
                        if 'г.' in date_text or '202' in date_text:
                            pub_date = parse_russian_date(date_text)
                    
                    article = {
                        'title': title,
                        'link': link,
                        'description': description,
                        'pubDate': pub_date
                    }
                    
                    articles.append(article)
                    print(f"  ✓ {title[:60]}... ({pub_date.strftime('%d.%m.%Y')})")
                    
                except Exception as e:
                    print(f"  ⚠️ Fehler bei Artikel {idx}: {e}")
                    continue
            
            browser.close()
            
    except Exception as e:
        print(f"❌ Scraping Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    return articles


def generate_rss_feed(articles, output_file='carnegie_feed.xml'):
    """Generiere RSS Feed aus Artikeln"""
    print(f"\n📝 Generiere RSS Feed...")
    
    try:
        fg = FeedGenerator()
        fg.id('https://carnegieendowment.org/ru/russia-eurasia/politika')
        fg.title('Carnegie Россия-Евразия: Политика')
        fg.link(href='https://carnegieendowment.org/ru/russia-eurasia/politika', rel='alternate')
        fg.description('Политические аналитики Carnegie Россия-Евразия')
        fg.language('ru')
        fg.generator('Python Playwright RSS Generator')
        
        for article in articles:
            fe = fg.add_entry()
            fe.id(article['link'])
            fe.title(article['title'])
            fe.link(href=article['link'])
            fe.description(article['description'])
            fe.published(article['pubDate'])
            fe.updated(article['pubDate'])
        
        # Erstelle Verzeichnis
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        fg.rss_file(output_file, pretty=True)
        print(f"✅ RSS Feed gespeichert: {output_file}")
        
    except Exception as e:
        print(f"❌ Feed-Generierung Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    print("=" * 60)
    print("Carnegie RSS Feed Generator - Политика")
    print("=" * 60)
    
    articles = scrape_carnegie()
    
    if not articles:
        print("⚠️ Keine Artikel gefunden!")
        sys.exit(1)
    
    print(f"\n📊 {len(articles)} Artikel erfolgreich gescraped")
    
    # Feed im Root-Verzeichnis speichern
    output_file = 'carnegie_feed.xml'
    generate_rss_feed(articles, output_file)
    
    print("\n✨ Fertig!")


if __name__ == '__main__':
    main()
