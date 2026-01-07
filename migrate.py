import argparse
import csv
import os
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request

# --- CONFIGURATION (EDIT THIS) ---
GITHUB_USER = "pwebsite"
REPO_NAME = "portfolio_assets_shopmonkey"
BRANCH = "main"

# LEAVE THIS EMPTY to force images to be at the root level
# (e.g. .../shopmonkey_01.png instead of .../shopmonkey/shopmonkey_01.png)
REPO_SUBFOLDER = ""
# ---------------------------------

def get_subfolder():
    # MODIFIED: Strictly returns the variable above.
    # Does NOT auto-guess the folder name anymore.
    return REPO_SUBFOLDER

def get_cdn_link(filename):
    sub = get_subfolder()
    # Handle spaces in filename for the URL
    safe_name = urllib.parse.quote(filename)
    path = f"{sub}/{safe_name}" if sub else safe_name
    return f"https://cdn.jsdelivr.net/gh/{GITHUB_USER}/{REPO_NAME}@{BRANCH}/{path}"

def scan_files():
    print("🔍 Scanning for images...")
    found = set()
    md_pattern = r'!\[.*?\]\((.*?)\)'
    html_pattern = r'<img\s+[^>]*src=["\']([^"\']+)'
    
    files = [f for f in os.listdir('.') if f.endswith('.md') or f.endswith('.html')]
    if not files:
        print("❌ No .md or .html files found.")
        return

    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            found.update(re.findall(md_pattern, content))
            found.update(re.findall(html_pattern, content))
    
    # Filter for likely images
    exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')
    images = [url for url in found if url.lower().endswith(exts) or "notion-static" in url or "framerusercontent" in url]
    
    if not images:
        print("No images found.")
        return

    # Write CSV
    if os.path.exists("mapping.csv"):
        print("⚠️  mapping.csv already exists. Skipping overwrite.")
    else:
        with open("mapping.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Original_URL", "New_Filename"])
            for img in sorted(images):
                writer.writerow([img, ""])
        print(f"✅ Created 'mapping.csv' with {len(images)} images.")

    # Generate Preview HTML
    html = "<html><style>body{font-family:sans-serif;padding:20px;} img{max-width:300px;display:block;margin:10px 0;} .card{background:#eee;padding:10px;margin-bottom:20px;}</style><body><h1>Preview</h1>"
    for img in sorted(images):
        html += f"<div class='card'><b>{img}</b><br><img src='{img}'></div>"
    html += "</body></html>"
    
    with open("preview.html", 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ Created 'preview.html'. Open it to see which image is which.")

def download_images():
    if not os.path.exists("mapping.csv"):
        print("❌ mapping.csv not found. Run --scan first.")
        return

    print("⬇️  Downloading images...")
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)

    rows = []
    # If subfolder is empty, just use "image" as prefix, or no prefix if you prefer
    prefix = os.path.basename(os.getcwd()).lower().replace(" ", "-")
    count = 0
    downloaded = 0

    with open("mapping.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        data = list(reader)

    for i, row in enumerate(data):
        original = row[0]
        # Use existing name or generate one
        if len(row) > 1 and row[1].strip():
            new_name = row[1].strip()
        else:
            # Guess extension
            ext = ".png"
            if ".jpg" in original or ".jpeg" in original: ext = ".jpg"
            elif ".gif" in original: ext = ".gif"
            elif ".webp" in original: ext = ".webp"
            new_name = f"{prefix}_{i+1:02d}{ext}"
        
        # Download
        if not os.path.exists(new_name):
            try:
                print(f"   Downloading {new_name}...", end=" ")
                urllib.request.urlretrieve(original, new_name)
                print("✅")
                downloaded += 1
                time.sleep(0.2)
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"   {new_name} exists. Skipping. ✅")
        
        rows.append([original, new_name])

    # Update CSV with generated names
    with open("mapping.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if header: writer.writerow(header)
        writer.writerows(rows)
    
    print(f"🎉 Downloaded {downloaded} images.")

def replace_links():
    if not os.path.exists("mapping.csv"):
        print("❌ mapping.csv not found.")
        return

    print("🔗 Replacing links in text files...")
    
    # Load Map
    url_map = {}
    with open("mapping.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 2 and row[1].strip():
                # We map BOTH the original URL AND the "Bad" URL (if it exists) to the "Good" URL
                # This fixes the issue if you ran the script incorrectly before.
                
                good_link = get_cdn_link(row[1].strip())
                original_url = row[0].strip()
                
                url_map[original_url] = good_link
                
                # Heuristic: If the original URL in the CSV is ALREADY a cdn link but wrong,
                # we still map it to the new "Good" link.
                url_map[original_url] = good_link

    # Process Files
    files = [f for f in os.listdir('.') if f.endswith('.md') or f.endswith('.html')]
    md_pattern = r'(!\[.*?\])\((.*?)\)'
    html_pattern = r'(<img\s+[^>]*src=["\'])([^"\']+)(["\'])'

    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        changes = 0
        
        def replace_md(match):
            nonlocal changes
            current = match.group(2).strip()
            # Check if we have a replacement
            if current in url_map:
                # Avoid replacing if it's already correct
                if url_map[current] == current:
                    return match.group(0)
                changes += 1
                return f"{match.group(1)}({url_map[current]})"
            return match.group(0)

        def replace_html(match):
            nonlocal changes
            current = match.group(2).strip()
            if current in url_map:
                if url_map[current] == current:
                    return match.group(0)
                changes += 1
                return f"{match.group(1)}{url_map[current]}{match.group(3)}"
            return match.group(0)

        new_content = re.sub(md_pattern, replace_md, content)
        new_content = re.sub(html_pattern, replace_html, new_content)

        if changes > 0:
            shutil.copy(filepath, filepath + ".backup")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Updated {filepath} ({changes} links fixed)")
        else:
            print(f"   No changes in {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Notion to GitHub Migration Tool")
    parser.add_argument("--scan", action="store_true", help="1. Scan files and create mapping.csv")
    parser.add_argument("--download", action="store_true", help="2. Download images and auto-name them")
    parser.add_argument("--replace", action="store_true", help="3. Update text files with new links")
    
    args = parser.parse_args()

    if args.scan:
        scan_files()
    elif args.download:
        download_images()
    elif args.replace:
        replace_links()
    else:
        print("⚠️  Please run a command:")
        print("   python3 migrate.py --scan")
        print("   python3 migrate.py --download")
        print("   python3 migrate.py --replace")

if __name__ == "__main__":
    main()