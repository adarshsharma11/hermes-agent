#!/usr/bin/env python3
"""
WordPress Publishing Script for Hermes Agent.
Parses a Markdown file, uploads a featured image (if specified),
converts body to HTML, and publishes it via WordPress REST API.
"""

import os
import sys
import re
import argparse
import mimetypes
from pathlib import Path
try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print("Error: The 'requests' package is not installed. Please run '.venv\\Scripts\\pip.exe install requests' or run this script using the virtualenv Python.")
    sys.exit(1)

# Try importing markdown
try:
    import markdown
except ImportError:
    print("Error: The 'markdown' package is not installed. Please run '.venv\\Scripts\\pip.exe install markdown' or run this script using the virtualenv Python.")
    sys.exit(1)

def load_dotenv(dotenv_path=None):
    """Custom pure-Python load_dotenv implementation to avoid external dependency."""
    if dotenv_path is None:
        dotenv_path = Path(".env")
    else:
        dotenv_path = Path(dotenv_path)
        
    if not dotenv_path.exists():
        return
        
    with open(dotenv_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                os.environ[key] = val

def get_hermes_home():
    """Locate the Hermes Home directory to read the global .env file."""
    # Method 1: Check environment variable
    val = os.environ.get("HERMES_HOME", "").strip()
    if val:
        return Path(val)

    # Method 2: Import from hermes_constants if available in python path
    try:
        project_root = Path(__file__).resolve().parents[4]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from hermes_constants import get_hermes_home as get_home
        return get_home()
    except Exception:
        pass

    # Method 3: Platform-native default fallback
    if sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA", "").strip()
        base = Path(local_appdata) if local_appdata else Path.home() / "AppData" / "Local"
        return base / "hermes"
    return Path.home() / ".hermes"

def load_credentials():
    """Load WordPress credentials from .env."""
    hermes_home = get_hermes_home()
    env_path = hermes_home / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Fallback to local .env in the current working directory
        load_dotenv()
        
    wp_url = os.getenv("WORDPRESS_URL")
    wp_user = os.getenv("WORDPRESS_USERNAME")
    wp_pass = os.getenv("WORDPRESS_APPLICATION_PASSWORD")
    
    if not wp_url or not wp_user or not wp_pass:
        print("Error: Missing WordPress credentials in .env file.")
        print(f"Looked in: {env_path.resolve()}")
        print("Make sure WORDPRESS_URL, WORDPRESS_USERNAME, and WORDPRESS_APPLICATION_PASSWORD are set.")
        sys.exit(1)
        
    return wp_url, wp_user, wp_pass

def parse_markdown_file(file_path):
    """Parse Markdown file extracting YAML frontmatter, title, and body."""
    if not os.path.exists(file_path):
        print(f"Error: Markdown file not found at '{file_path}'")
        sys.exit(1)
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter = {}
    body = content

    # Simple frontmatter parsing
    if content.startswith("---"):
        end_idx = content.find("---", 3)
        if end_idx != -1:
            yaml_content = content[3:end_idx].strip()
            body = content[end_idx+3:].strip()
            for line in yaml_content.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip().lower()] = v.strip().strip("'\"")

    # If title not in frontmatter, find the first H1 header in the body
    title = frontmatter.get("title")
    if not title:
        match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            # Remove the H1 title from body to prevent duplication on WordPress
            body = body.replace(match.group(0), "", 1).strip()
        else:
            title = Path(file_path).stem.replace("-", " ").replace("_", " ").title()

    featured_image = frontmatter.get("featured_image")
    status = frontmatter.get("status", "publish")

    return title, body, featured_image, status

def upload_featured_image(wp_url, wp_user, wp_pass, image_path, base_dir):
    """Upload featured image to WordPress media library and return its ID."""
    # Resolve relative image path relative to the Markdown file directory
    resolved_path = Path(image_path)
    if not resolved_path.is_absolute():
        resolved_path = (Path(base_dir) / resolved_path).resolve()
        
    if not resolved_path.exists():
        print(f"Warning: Featured image file not found at '{resolved_path}'")
        return None

    filename = resolved_path.name
    mime_type, _ = mimetypes.guess_type(str(resolved_path))
    if not mime_type:
        mime_type = "image/jpeg"

    base_url = wp_url.rstrip("/")
    if "/wp-json" in base_url:
        base_url = base_url.split("/wp-json")[0]
        
    endpoint = f"{base_url}/wp-json/wp/v2/media"
    
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": mime_type
    }

    print(f"Uploading featured image: {filename} ({mime_type})...")
    try:
        with open(resolved_path, "rb") as img_file:
            response = requests.post(
                endpoint,
                auth=HTTPBasicAuth(wp_user, wp_pass),
                headers=headers,
                data=img_file,
                timeout=30
            )
            
        if response.status_code in (200, 201):
            media_data = response.json()
            media_id = media_data.get("id")
            print(f"Successfully uploaded featured image. Media ID: {media_id}")
            return media_id
        else:
            print(f"Warning: Failed to upload featured image. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Warning: Error uploading image: {e}")
        return None

def create_wordpress_post(wp_url, wp_user, wp_pass, title, html_content, media_id=None, status="publish"):
    """Create a new WordPress post via the REST API."""
    base_url = wp_url.rstrip("/")
    if "/wp-json" in base_url:
        base_url = base_url.split("/wp-json")[0]
        
    endpoint = f"{base_url}/wp-json/wp/v2/posts"
    
    payload = {
        "title": title,
        "content": html_content,
        "status": status
    }
    
    if media_id:
        payload["featured_media"] = media_id

    headers = {
        "Content-Type": "application/json"
    }

    print(f"Creating WordPress post: '{title}' with status '{status}'...")
    try:
        response = requests.post(
            endpoint,
            auth=HTTPBasicAuth(wp_user, wp_pass),
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code in (200, 201):
            post_data = response.json()
            post_id = post_data.get("id")
            post_link = post_data.get("link")
            print("--------------------------------------------------")
            print(f"WordPress Post Created Successfully!")
            print(f"Post ID: {post_id}")
            print(f"Post URL: {post_link}")
            print("--------------------------------------------------")
            return post_id, post_link
        else:
            print(f"Error: Failed to create post. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: Connection failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Publish a Markdown blog post to WordPress.")
    parser.add_argument("--file", required=True, help="Path to the markdown file.")
    parser.add_argument("--image", help="Override path to the featured image.")
    args = parser.parse_args()

    wp_url, wp_user, wp_pass = load_credentials()
    title, body, featured_image, status = parse_markdown_file(args.file)

    # Convert markdown to HTML
    html_content = markdown.markdown(body)

    # Determine image path (CLI override takes precedence)
    image_path = args.image or featured_image
    media_id = None
    if image_path:
        base_dir = os.path.dirname(os.path.abspath(args.file))
        media_id = upload_featured_image(wp_url, wp_user, wp_pass, image_path, base_dir)

    create_wordpress_post(wp_url, wp_user, wp_pass, title, html_content, media_id, status)

if __name__ == "__main__":
    main()
