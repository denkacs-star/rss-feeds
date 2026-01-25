#!/usr/bin/env python3
"""
RSS Feed Generator für Carnegie Россия-Евразия
"""

from playwright.sync_api import sync_playwright
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
import sys
import os

def scrape_carnegie():
    """Scrape Carnegie Russia-Eurasia Artikel"""
    print("🔍 Starte Scraping von Carnegie...")
    
    articles = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            url = 'https://carnegieendowment.org/ru/russia-eurasia'
            print(f"📄 Lade {url}")
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Warte auf die Artikel-Titel
            page.wait_for_selector('span.font-sans.text-headlineH5', timeout=10000)
            
            # Finde alle Artikel-Container (vermutlich Links oder Cards)
            # Wir gehen vom Titel aus nach oben zum Container
            article_links = page.query_selector_all('a:has(span.font-sans.text-headlineH5)')
            
            print(f"✅ {len(article_links)} Artikel gefunden")
            
            for idx, link_elem in enumerate(article_links[:15]):  # Max 15 Artikel
                try:
                    # Link extrahieren
                    link = link_elem.get_attribute('href')
                    if link and not link.startswith('http'):
                        link = f"https://carnegieendowment.org{link}"
                    
                    # Titel extrahieren
                    title_elem = link_elem.query_selector('span.font-sans.text-headlineH5')
                    title = title_elem.inner_text().strip() if title_elem else f"Artikel {idx+1}"
                    
                    # Beschreibung versuchen zu finden (meist unter dem Titel)
                    # Typische Klassen: text-body, excerpt, description
                    desc_elem = link_elem.query_selector('span.text-body, p, div.excerpt')
                    description = desc_elem.inner_text().strip() if desc_elem else title
                    
                    # Datum falls vorhanden
                    date_elem = link_elem.query_selector('time, span.date, div.date')
                    if date_elem:
                        date_str = date_elem.get_attribute('datetime') or date_elem.inner_text()
                        try:
                            pub_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        except:
                            pub_date = datetime.now(pytz.UTC)
                    else:
                        pub_date = datetime.now(pytz.UTC)
                    
                    article = {
                        'title': title,
                        'link': link,
                        'description': description[:500],
                        'pubDate': pub_date
                    }
                    
                    articles.append(article)
                    print(f"  ✓ {title[:60]}...")
                    
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
        fg.id('https://carnegieendowment.org/ru/russia-eurasia')
        fg.title('Carnegie Россия-Евразия')
        fg.link(href='https://carnegieendowment.org/ru/russia-eurasia', rel='alternate')
        fg.description('Аналитика Carnegie Россия-Евразия')
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
    print("Carnegie RSS Feed Generator")
    print("=" * 60)
    
    articles = scrape_carnegie()
    
    if not articles:
        print("⚠️ Keine Artikel gefunden!")
        sys.exit(1)
    
    print(f"\n📊 {len(articles)} Artikel erfolgreich gescraped")
    
    output_file = 'carnegie_feed.xml'  # Statt 'rss-feeds/carnegie_feed.xml'
    generate_rss_feed(articles, output_file)
    
    print("\n✨ Fertig!")


if __name__ == '__main__':
    main()
