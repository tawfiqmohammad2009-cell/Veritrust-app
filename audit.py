import os

def audit_project():
    current_dir = os.getcwd()
    print(f"[*] Scanning project directory: {current_dir}\n")
    
    target_extensions = ['.java', '.kt', '.xml', '.py', '.html', '.js', '.apk']
    found_assets = {ext: [] for ext in target_extensions}
    all_files = []

    for root, dirs, files in os.walk(current_dir):
        if 'veritrust-env' in root or '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, current_dir)
            all_files.append(relpath)
            
            _, ext = os.path.splitext(file)
            if ext in found_assets:
                found_assets[ext].append(relpath)

    print(f"Total files found: {len(all_files)}\n")
    print("--- Asset Breakdown ---")
    for ext, files in found_assets.items():
        if files:
            print(f"\n[{ext.upper()} Files - {len(files)} found]:")
            for f in files[:10]:
                print(f"  - {f}")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more.")

    print("\n--- Key Requirement Check ---")
    has_manifest = any('AndroidManifest.xml' in f for f in all_files)
    has_native = any(f.endswith('.java') or f.endswith('.kt') for f in all_files)
    
    print(f"Android Manifest Present: {'YES' if has_manifest else 'NO'}")
    print(f"Native Android Code (Java/Kotlin): {'YES' if has_native else 'NO'}")

if __name__ == '__main__':
    audit_project()
