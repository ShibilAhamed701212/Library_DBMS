import requests
from backend.repository.db_access import execute, fetch_one, fetch_all
from backend.config.config import get_config

def enrich_book_metadata(book_id):
    """
    Intelligently enriches book data using AI.
    - Creates Author profile if missing.
    - Fetches Bio/Nationality.
    - Identifies and Links Series.
    - Sets Series Order.
    - NEW: Fetches Book Cover & Description.
    """
    book = fetch_one("SELECT * FROM books WHERE book_id = %s", (book_id,))
    if not book: return "Book not found."
    
    title = book['title']
    author_name = book['author']
    
    try:
        # 1. FETCH AUTHOR BIO (OpenLibrary)
        # We need to search for the author first to get their OLID
        print(f"🌍 Searching OpenLibrary for author: {author_name}")
        search_url = f"https://openlibrary.org/search/authors.json?q={author_name}"
        search_resp = requests.get(search_url, timeout=5).json()
        
        bio = None
        
        if search_resp.get('numFound', 0) > 0:
            author_key = search_resp['docs'][0]['key'] # e.g. "OL23919A"
            
            # Fetch Author Details
            details_url = f"https://openlibrary.org/authors/{author_key}.json"
            details_resp = requests.get(details_url, timeout=5).json()
            
            bio_raw = details_resp.get('bio', '')
            if isinstance(bio_raw, dict):
                bio = bio_raw.get('value', '')
            else:
                bio = str(bio_raw)
                
            # Limit bio length
            if bio:
                # CLEANUP: Strip HTML tags (like <q>, <i>, <br>)
                import re
                bio = re.sub(r'<[^>]+>', '', bio)
                bio = bio[:4000] + "..." if len(bio) > 4000 else bio
                
        # 1.5. FALLBACK OR UPGRADE: WIKIPEDIA
        if not bio or len(bio) < 200:
            print(f"🌍 Upgrading bio via Wikipedia for: {author_name}")
            try:
                # 1. SEARCH Wikipedia first to get the correct Page Title
                search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={author_name}&limit=1&namespace=0&format=json"
                search_res = requests.get(search_url, timeout=5).json()
                
                wiki_title = None
                if search_res and len(search_res) > 1 and search_res[1]:
                    wiki_title = search_res[1][0] 
                    print(f"🔍 Wikipedia found matching page: {wiki_title}")
                
                if wiki_title:
                     # 2. Fetch Extract using Action API
                    query_url = "https://en.wikipedia.org/w/api.php"
                    params = {
                        "action": "query",
                        "format": "json",
                        "prop": "extracts",
                        "titles": wiki_title,
                        "exintro": 1,
                        "explaintext": 1,
                        "redirects": 1
                    }
                    wiki_resp = requests.get(query_url, params=params, timeout=5)
                    wiki_data = wiki_resp.json()
                    
                    # Extract the page content (page ID is dynamic)
                    pages = wiki_data.get("query", {}).get("pages", {})
                    for page_id, page_val in pages.items():
                        if page_id != "-1" and 'extract' in page_val:
                            wiki_bio = page_val['extract']
                            if wiki_bio and len(wiki_bio) > len(str(bio or "")):
                                bio = wiki_bio
                                print("✅ Upgraded to Wikipedia Bio via Action API!")
                            break
            except Exception as w_e:
                print(f"⚠️ Wikipedia lookup failed: {w_e}")
        
        # 2. SAVE AUTHOR
        author = fetch_one("SELECT author_id, bio FROM authors WHERE name = %s", (author_name,))
        if not author:
            execute("INSERT INTO authors (name, bio) VALUES (%s, %s)", (author_name, bio))
            author = fetch_one("SELECT author_id, bio FROM authors WHERE name = %s", (author_name,))
        else:
            current_bio = author.get('bio', '') or ''
            should_update = False
            if bio and len(bio) > len(current_bio):
                should_update = True
            elif bio and '<' in current_bio:
                should_update = True
                
            if should_update:
                print(f"🔄 Updating bio for {author_name}")
                execute("UPDATE authors SET bio = %s WHERE author_id = %s", (bio, author['author_id']))
                
        author_id = author['author_id']
        
        # 3. IDENTIFY SERIES & FETCH METADATA (Google Books)
        series_id = None
        s_name = None
        s_order = None
        cover_url = None
        description = None
        
        print(f"🌍 Searching Google Books for series info: {title}")
        gb_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}+inauthor:{author_name}&maxResults=1"
        gb_resp = requests.get(gb_url, timeout=5).json()
        
        if gb_resp.get('totalItems', 0) > 0:
            info = gb_resp['items'][0]['volumeInfo']
            
            # --- 3.1 Fetch Description ---
            description = info.get('description')
            if description:
                description = description[:2000] + "..." if len(description) > 2000 else description
            
            # --- 3.2 Fetch Cover URL ---
            image_links = info.get('imageLinks', {})
            cover_url = image_links.get('extraLarge') or \
                        image_links.get('large') or \
                        image_links.get('medium') or \
                        image_links.get('thumbnail')
            
            if cover_url:
                 cover_url = cover_url.replace("http://", "https://")
            
            print(f"🖼️ Found Cover: {cover_url is not None}")
            
            # --- 3.3 Identify Series ---
            subtitle = info.get('subtitle', '')
            import re
            text_to_search = f"{info.get('title')} {info.get('subtitle', '')} {info.get('description', '')[:200]}"
            
            patterns = [
                r'\(([^)]+),?\s+[#]?(\d+)\)',         
                r'Book (\d+) of (?:the )?([A-Z][a-zA-Z0-9\s\']+)',   
                r'Vol\.? (\d+) of (?:the )?([A-Z][a-zA-Z0-9\s\']+)', 
                r'([A-Z][a-zA-Z0-9\s\']+) Series,? Book (\d+)', 
            ]
            
            found = False
            for pat in patterns:
                match = re.search(pat, text_to_search) 
                if match:
                    g1, g2 = match.groups()
                    if g1.isdigit(): 
                        s_order = int(g1)
                        s_name = g2.strip()
                    else:
                        s_name = g1.strip()
                        if g2.isdigit():
                            s_order = int(g2)
                        
                    if len(s_name) < 50 and s_name and s_name[0].isupper() and " " in s_name:
                        if "history of" in s_name.lower() or "struggle for" in s_name.lower():
                             continue
                        found = True
                        print(f"✅ Found Series via Regex: {s_name} (#{s_order})")
                        break
            
            if not found:
                s_name = None 
                
        # 3.5. FALLBACK: OpenLibrary Work Search
        if not s_name:
            print(f"🌍 Google Books failed, trying OpenLibrary Series for: {title}")
            try:
                ol_s_url = f"https://openlibrary.org/search.json?title={title}&author={author_name}&limit=1"
                ol_s_data = requests.get(ol_s_url, timeout=5).json()
                
                if ol_s_data.get('numFound', 0) > 0:
                     doc = ol_s_data['docs'][0]
                     
                     # 3.5.1 Try to get Cover from OL if Google failed
                     if not cover_url and 'cover_i' in doc:
                         cover_id = doc['cover_i']
                         cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                         print("🖼️ Found Cover via OpenLibrary")
                         
                     work_key = doc.get('key')
                     if work_key:
                         work_url = f"https://openlibrary.org{work_key}.json"
                         work_res = requests.get(work_url, timeout=5).json()
                         
                         if 'series' in work_res and isinstance(work_res['series'], list) and len(work_res['series']) > 0:
                             raw_series = work_res['series'][0]
                             if isinstance(raw_series, str):
                                 s_name = raw_series
                                 s_order = 1
                                 print(f"✅ Found OpenLibrary Series: {s_name}")
            except Exception as e:
                print(f"⚠️ OpenLibrary Series lookup failed: {e}")

        # 4. SAVE SERIES
        if s_name:
            s_name = s_name.replace("Series", "").strip()
            series = fetch_one("SELECT series_id FROM series WHERE name = %s", (s_name,))
            if not series:
                execute("INSERT INTO series (name) VALUES (%s)", (s_name,))
                series = fetch_one("SELECT series_id FROM series WHERE name = %s", (s_name,))
            series_id = series['series_id']
            
        # 5. UPDATE BOOK
        print(f"📝 Saving Metadata for {title}: Cover={bool(cover_url)}, Desc={bool(description)}")
        execute("""
            UPDATE books 
            SET author_id = %s, series_id = %s, series_order = %s, cover_url = %s, description = %s
            WHERE book_id = %s
        """, (author_id, series_id, s_order, cover_url, description, book_id))
        
        return "Success (Open Source)"
        
    except Exception as e:
        print(f"❌ Open Source Enrichment Error: {e}")
        return f"Error: {str(e)}"

def get_author_books(author_id):
    """Returns all books by a specific author."""
    return fetch_all("SELECT * FROM books WHERE author_id = %s ORDER BY series_id, series_order", (author_id,))

def get_series_books(series_id):
    """Returns all books in a series in order."""
    return fetch_all("SELECT * FROM books WHERE series_id = %s ORDER BY series_order", (series_id,))
