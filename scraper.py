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
            
            for idx, article_elem in enumerate(article_elements[:20]):
                try:
                    # Finde alle Links im Artikel
                    all_links = article_elem.query_selector_all('a')
                    
                    # Der zweite Link (Index 1) ist normalerweise der Artikel-Link
                    # Der erste ist der "CARNEGIE POLITIKA" Badge
                    article_link = None
                    for link in all_links:
                        href = link.get_attribute('href')
                        if href and '/politika/202' in href and 'carnegieendowment.org' not in link.inner_text():
                            article_link = link
                            break
                    
                    if not article_link:
                        continue
                    
                    # Link extrahieren
                    link = article_link.get_attribute('href')
                    if link and not link.startswith('http'):
                        link = f"https://carnegieendowment.org{link}"
                    
                    # Titel ist der Text des Artikel-Links
                    title = article_link.inner_text().strip()
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # Gesamten Artikel-Text holen und parsen
                    full_text = article_elem.inner_text()
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    
                    # Beschreibung ist normalerweise die Zeile nach dem Titel
                    description = title  # Fallback
                    for i, line in enumerate(lines):
                        if title in line and i + 1 < len(lines):
                            next_line = lines[i + 1]
                            if len(next_line) > 30 and 'CARNEGIE' not in next_line and 'КОММЕНТАРИЙ' not in next_line:
                                description = next_line
                                break
                    
                    # Datum suchen (Format: "23 января 2026 г.")
                    pub_date = datetime.now(pytz.UTC)
                    for line in lines:
                        if 'января' in line or 'февраля' in line or 'марта' in line or 'апреля' in line or \
                           'мая' in line or 'июня' in line or 'июля' in line or 'августа' in line or \
                           'сентября' in line or 'октября' in line or 'ноября' in line or 'декабря' in line:
                            pub_date = parse_russian_date(line)
                            break
                    
                    article = {
                        'title': title,
                        'link': link,
                        'description': description[:500],
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
