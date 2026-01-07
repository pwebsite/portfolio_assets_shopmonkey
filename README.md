# portfolio_assets_shopmonkey

```markdown
# Image Migration Script Cheat Sheet

## Quick Start (3 Steps)

```bash
# Step 1: Find all images in your .md/.html files
python3 migrate.py --scan

# Step 2: Download images locally (auto-names them)
python3 migrate.py --download

# Step 3: Replace old links with CDN links
python3 migrate.py --replace
```

## Before You Run

**Download Notion exported .md**

**Edit the configuration at the top of the script:**

```python
GITHUB_USER = "pwebsite"           # Your GitHub username
REPO_NAME = "portfolio_assets_shopmonkey"     # Your GitHub repo name
BRANCH = "main"                    # Branch name (usually "main")
REPO_SUBFOLDER = "auto"            # Uses current folder name, or set manually
```

## What Each Step Does

### `--scan`

- Scans all `.md` and `.html` files in the current directory
- Finds image URLs (Markdown `![](url)` and HTML `<img src="">`)
- Creates `mapping.csv` with all found images
- Creates `preview.html` so you can see which image is which

### `--download`

- Reads `mapping.csv`
- Downloads each image to the current folder
- Auto-names them like `foldername_01.png`, `foldername_02.jpg`, etc.
- You can manually edit `mapping.csv` before downloading to choose custom names

### `--replace`

- Updates all `.md` and `.html` files
- Replaces old image URLs with new CDN links
- Creates `.backup` files before modifying anything
- CDN format: `https://cdn.jsdelivr.net/gh/USER/REPO@BRANCH/subfolder/image.png`

## Workflow Tips

- **After `--scan`:** Open `preview.html` in a browser to see all images, then optionally edit `mapping.csv` to give them better names
- **After `--download`:** Upload the downloaded images to your GitHub repo in the appropriate folder before running `--replace`
- **Safety:** Backups are created automatically (files with `.backup` extension)

## Example

If you're in a folder called `shopmonkey`:

- Downloaded images: `shopmonkey_01.png`, `shopmonkey_02.jpg`

- CDN links: `https://cdn.jsdelivr.net/gh/pwebsite/portfolio_images@main/shopmonkey/shopmonkey_01.png`
  
  ```
  
  ```
