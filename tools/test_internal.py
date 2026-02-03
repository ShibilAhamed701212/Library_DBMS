from backend.app import create_app
import json

app = create_app()
client = app.test_client()

print("INTERNAL FETCH TEST:")
# We don't need a real session for the 404 check, it should return 401 if it finds the route
response = client.get('/api/book/get/26')

print(f"Status: {response.status_code}")
print(f"Body Preview: {response.get_data(as_text=True)[:200]}")

if response.status_code == 404:
    print("RESULT: Internal 404! The route is NOT registered in the app instance.")
else:
    print("RESULT: Internal success (or 401/500). The route exists in the app instance.")
