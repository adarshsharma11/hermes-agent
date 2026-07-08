---
name: wordpress-blog
description: "Generate blog posts, verify against a PostgreSQL similarity search, and publish to WordPress via the web server API."
platforms: [linux, macos, windows]
required_environment_variables:
  - name: WORDPRESS_URL
    prompt: "Enter your WordPress site URL (e.g., https://myblog.com)"
  - name: WORDPRESS_USERNAME
    prompt: "Enter your WordPress username"
  - name: WORDPRESS_APPLICATION_PASSWORD
    prompt: "Enter your WordPress Application Password (generated in User Profile)"
---

# WordPress Blog Skill

This skill teaches you how to generate high-quality blog posts, ensure no duplicate or highly similar topics have been written for a specific project using PostgreSQL similarity search, and publish the post to a WordPress site via the server API.

## Project Context
The database supports multiple projects. Every blog belongs to a specific project (defined by a `project_id`, e.g., `Project A`, `Project B`).
Similarity searches are scoped **project-wise**, meaning you will search and filter only for blogs belonging to the current project.

---

## Validation Rules

Before initiating a blog generation and publishing request, you must validate the following rules:
- **Title**: Must not be empty.
- **Content**: Must not be empty.
- **Base URL**: The `WORDPRESS_URL` must not end with `/` (the API normalizes it).
- **Environment Variables**: Verify that the required environment variables (`WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_APPLICATION_PASSWORD`) are configured.

---

## Workflow

1. **Suggest a Topic**:
   - Propose a topic for the blog post based on the user's requirements.

2. **Vector Similarity Search (Avoid Duplication)**:
   - Before writing the post, perform a vector search to check if a similar blog has already been created in this project.
   - Send a `POST` request to `http://31.97.129.250:3000/api/blogs/search` with the following JSON payload (use `curl` or python code execution):
     ```json
     {
       "project_id": "Project A",
       "topic": "Proposed blog topic description",
       "threshold": 0.85
     }
     ```
   - **Analyze Search Results**:
     - If the API returns `"similar_found": true`, a similar blog already exists for this project. **Stop** the generation, select a completely different topic, and perform the similarity check again.
     - If the API returns `"similar_found": false`, proceed to the next step.

3. **Generate the Blog**:
   - Write a high-quality, engaging article about the selected topic.
   - Ensure the blog has a proper structure, formatting, and complete information.
   - Convert the Markdown formatting into valid HTML (paragraphs, lists, headings) to be published to WordPress.

4. **Publish and Save Metadata**:
   - Send a `POST` request to `http://31.97.129.250:3000/api/blogs/publish` to publish the post and save its metadata + vector embedding in the PostgreSQL database.
   - Request JSON Payload:
     ```json
     {
       "project_id": "Project A",
       "platform": "wordpress",
       "title": "Blog Post Title",
       "content": "<p>HTML content here...</p>",
       "topic": "Selected topic description",
       "slug": "blog-post-slug",
       "keywords": "ai, software development, coding",
       "categories": "Technology",
       "author": "Hermes Agent"
     }
     ```
   - **Do NOT push blogs to Git.** All blog records are persisted in the PostgreSQL database.

5. **Verify and Report**:
   - Confirm successful publishing from the API response:
     ```json
     {
       "success": true,
       "post_id": 123,
       "url": "https://atravelum.com/blog-post-slug/"
     }
     ```
   - Present the published blog URL and WordPress post ID to the user.

---

## Error Handling

If the web server API returns a non-2xx response:
- Capture the HTTP status code.
- Return the response body.
- Report detailed errors if publishing or saving metadata fails.

Standard Error Format:
```json
{
  "success": false,
  "status": 401,
  "error": "Unauthorized"
}
```

---

## Notes

- **Never** hardcode credentials. Always load them from environment variables via the server API.
- **Never** log usernames, passwords, or authorization headers.
- Publish **only** the content provided by the caller.
- **Preserve** HTML formatting exactly as received.
- **Return only** structured JSON results to the calling agent.
