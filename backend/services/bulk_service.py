
import csv
import io
from backend.repository.db_access import fetch_all, execute

def export_books_csv():
    """Returns the entire book catalog as a CSV formatted string."""
    books = fetch_all("SELECT title, author, category, copies FROM books")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Title', 'Author', 'Category', 'Total Copies'])
    
    # Data
    for b in books:
        writer.writerow([b['title'], b['author'], b['category'], b['copies']])
        
    return output.getvalue()

def import_books_csv(stream):
    """
    Parses a CSV file stream and imports books into the database.
    Format: Title, Author, Category, Copies
    """
    try:
        data = stream.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(data))
        
        imported_count = 0
        errors = []
        
        for row in reader:
            try:
                title = row.get('Title') or row.get('title')
                author = row.get('Author') or row.get('author')
                category = row.get('Category') or row.get('category')
                copies = int(row.get('Total Copies') or row.get('copies') or 1)
                
                if not title or not author:
                    continue
                
                execute(
                    """
                    INSERT INTO books (title, author, category, copies, available_copies)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (title, author, category, copies, copies)
                )
                imported_count += 1
            except Exception as e:
                errors.append(f"Row {reader.line_num}: {str(e)}")
        
        return {
            "success": True, 
            "message": f"✅ Successfully imported {imported_count} books.",
            "errors": errors
        }
    except Exception as e:
        return {"success": False, "message": f"❌ Import failed: {str(e)}"}
