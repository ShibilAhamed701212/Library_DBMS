
import sys
import os

print("="*40)
print("PYTHON DEBUGGER")
print("="*40)
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print("-" * 20)

try:
    import mysql.connector
    print("✅ mysql-connector-python is INSTALLED!")
    print(f"Version: {mysql.connector.__version__}")
except ImportError as e:
    print("❌ mysql-connector-python is NOT FOUND.")
    print("Error:", e)

print("-" * 20)
print("Environment Paths:")
for path in sys.path:
    print(f" - {path}")

print("="*40)
input("Press Enter to exit...")
