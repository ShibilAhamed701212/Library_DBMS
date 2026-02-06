import os

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "LDBMS_codebase_context.txt")

# Directories to ignore
IGNORE_DIRS = {
    ".git", "__pycache__", "venv", ".venv", "env", "node_modules", 
    "migrations", "static", ".idea", ".vscode", "tests", "tmp"
}

# File extensions to include (add more if needed)
INCLUDE_EXTENSIONS = {
    ".py", ".html", ".css", ".js", ".md", ".txt", ".json", ".sql", ".yaml", ".yml"
}

# Specific files to exclude
IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "LDBMS_codebase_context.txt", ".DS_Store"
}

def get_file_tree(root_dir):
    tree_str = "Project Structure:\n"
    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        level = root.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree_str += f"{indent}{os.path.basename(root)}/\n"
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if f not in IGNORE_FILES and os.path.splitext(f)[1] in INCLUDE_EXTENSIONS:
                 tree_str += f"{subindent}{f}\n"
    return tree_str

def export_codebase():
    print(f"Exporting codebase from: {PROJECT_ROOT}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        # 1. Write the directory tree
        tree = get_file_tree(PROJECT_ROOT)
        outfile.write(tree)
        outfile.write("\n" + "="*50 + "\n\n")

        # 2. Write file contents
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if file in IGNORE_FILES:
                    continue
                    
                ext = os.path.splitext(file)[1]
                if ext not in INCLUDE_EXTENSIONS:
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as infile:
                        content = infile.read()
                        
                    # Write in XML-style format
                    outfile.write(f'<file path="{rel_path}">\n')
                    outfile.write(content)
                    outfile.write(f'\n</file>\n\n')
                    
                except Exception as e:
                    print(f"Skipping file {rel_path} due to error: {e}")

    print(f"Export complete! File saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    export_codebase()
