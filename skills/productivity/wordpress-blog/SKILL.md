---
name: wordpress-blog
description: "Generate blog posts, save as Markdown, push to Git, and publish to WordPress."
platforms: [linux, macos, windows]
required_environment_variables:
  - name: WORDPRESS_URL
    prompt: "Enter your WordPress site URL (e.g. https://myblog.com)"
  - name: WORDPRESS_USERNAME
    prompt: "Enter your WordPress username"
  - name: WORDPRESS_APPLICATION_PASSWORD
    prompt: "Enter your WordPress Application Password (generated in User Profile)"
---

# WordPress Blog Skill

This skill teaches you how to write blog posts, manage them locally as Markdown files, push them to the Git repository, and publish them to WordPress (including uploading featured images).

## Prerequisites

Ensure you have set the WordPress credentials in your `.env` file (`${HERMES_HOME}/.env`):
- `WORDPRESS_URL`
- `WORDPRESS_USERNAME`
- `WORDPRESS_APPLICATION_PASSWORD`

## Workflow

### 1. Write the Blog Post
Write a high-quality, engaging article about the specified topic.
- Use standard Markdown formatting.
- Include YAML frontmatter at the top of the file:
  ```yaml
  ---
  title: "Blog Post Title"
  status: "publish"  # Use "publish" to release immediately or "draft" to save as draft
  featured_image: "relative/path/to/image.png"  # Optional: local path to the featured image
  ---
  ```
- Save the post in the `blogs/` directory in your current working directory.
- Name the file with a slugified date prefix (e.g., `blogs/2026-07-06-ai-trends.md`). If the `blogs/` directory does not exist, create it.

### 2. Push to Git Repository
After saving the Markdown file, add it to the Git repository, commit it, and push it:
```bash
git add blogs/<filename>.md
git commit -m "Add blog post: <title>"
git push
```

### 3. Publish to WordPress
Execute the helper Python script using the `terminal` tool to upload the featured image, convert the Markdown body to HTML, and publish it to WordPress:
```bash
python "${HERMES_SKILL_DIR}/scripts/publish_wordpress.py" --file "blogs/<filename>.md"
```
*(If a featured image is specified in the YAML frontmatter, the script will automatically upload it first and attach it to the post).*

### 4. Report
Verify that both the Git push and the WordPress publish succeeded, and present the resulting WordPress post URL and ID to the user.
