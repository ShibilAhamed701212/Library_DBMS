from backend.app import create_app

app = create_app()

print("SEARCHING FOR BOOK API ROUTE:")
found = False
for rule in app.url_map.iter_rules():
    if "/admin/api/book/" in rule.rule:
        print(f"FOUND: {rule.rule} | Endpoint: {rule.endpoint}")
        found = True

if not found:
    print("CRITICAL: Book API route NOT found in current code state!")
else:
    print("SUCCESS: Route is present in code. If user gets 404, server RESTART is needed.")
