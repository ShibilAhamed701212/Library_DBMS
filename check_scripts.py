import re

def check_scripts(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    scripts = re.findall(r'<script', content, re.IGNORECASE)
    end_scripts = re.findall(r'</script>', content, re.IGNORECASE)
    
    print(f"Opening tags: {len(scripts)}")
    print(f"Closing tags: {len(end_scripts)}")
    
    # Check if any opening tag is not followed by a closing tag before another opening tag
    # or if the last one is not closed.
    
    pos = 0
    while True:
        start = content.find('<script', pos)
        if start == -1: break
        
        end = content.find('</script>', start)
        next_start = content.find('<script', start + 1)
        
        if end == -1 or (next_start != -1 and end > next_start):
            print(f"Potential unclosed script starting at position {start}")
            snippet = content[start:start+100]
            print(f"Snippet: {snippet}...")
            # If it's a script with src, it might be fine on one line but usually it needs </script>
        
        pos = start + 1

if __name__ == "__main__":
    check_scripts(r"d:\var-codes\LDBMS\pythonProject\templates\member\community.html")
