# Brita Filter CMS - Documentation

## Overview

The Brita Filter CMS is a multi-stage content processing pipeline for the IngredientIQ blog. It transforms raw markdown drafts into fully optimized, publish-ready content with minimal effort from writers.

### Philosophy

**Writers only need to "pour in" their content.** Everything else—SEO, social media, structure, validation—is auto-generated with the option to override.

---

## Filter Stages

### Filter 0: Raw Input (What Humans Touch)

The only required writing field.

| Field | Description |
|-------|-------------|
| `raw_draft` | Markdown content - the ONLY required writing field |
| `notes_private` | Private notes (never published) |

**Why Markdown?** Deterministic structure extraction (headings, lists, quotes, FAQs) without a heavy block editor.

---

### Filter 1: Structural Normalization (Auto)

Turns raw draft into a clean document skeleton.

**Auto-generated:**
- `body_html` - Sanitized HTML render
- `toc_json` - Table of contents (heading outline)
- `key_sections_json` - Content sections for reuse
- `extracted_faqs_json` - FAQ items detected from content

**Automations:**
- Sanitize + normalize whitespace, punctuation
- Enforce heading hierarchy (single H1, then H2/H3)
- Extract intro, sections, pull quotes, FAQs

---

### Filter 2: Metadata Distillation (Auto with Overrides)

Produces high-signal summaries and entities from any topic.

| Field | Auto-generated From | Lock Toggle |
|-------|---------------------|-------------|
| `title` | First H1 or first sentence | ✅ `title_locked` |
| `slug` | Auto from title, unique | ✅ `slug_locked` |
| `excerpt` | 155-180 char summary | ✅ `excerpt_locked` |
| `key_takeaways` | 3-7 bullet points | ✅ `key_takeaways_locked` |
| `reading_time_minutes` | Word count / 200 wpm | - |
| `word_count` | Body text word count | - |
| `entities_json` | People/orgs/concepts | - |

---

### Filter 3: SEO Pack (Auto)

Always ships the full "publisher metadata suite".

| Field | Target Length | Lock Toggle |
|-------|---------------|-------------|
| `meta_title` | ≤ 60 chars | ✅ `meta_title_locked` |
| `meta_description` | ≤ 160 chars | ✅ `meta_description_locked` |
| `canonical_url` | Auto = current URL | - |
| `robots_indexable` | Default: true | - |
| `robots_followable` | Default: true | - |
| `schema_type` | BlogPosting | - |

**Open Graph:**
- `og_title`, `og_description`, `og_image`

**Twitter/X:**
- `twitter_title`, `twitter_description`

---

### Filter 4: SMO Distribution Pack (Auto)

One-click social with consistent previews.

| Field | Description | Lock Toggle |
|-------|-------------|-------------|
| `social_copy_linkedin` | 1-2 paragraphs | ✅ |
| `social_copy_twitter` | ≤ 280 chars | ✅ |
| `social_hashtags` | 3-8 hashtags | ✅ |

---

### Filter 5: LLM Surface Readiness (Auto)

Makes pages easy for AI to ingest, cite, and trust.

| Field | Description | Lock Toggle |
|-------|-------------|-------------|
| `summary_for_llms` | 80-120 word factual summary | ✅ |
| `key_facts` | Structured claims list | - |
| `sources_json` | URL list with labels | - |

**Site-level Machine Layer:**
- `/llms.txt` - Machine-readable site documentation
- `/blog/feed/rss/` - RSS feed
- `/sitemap.xml` - XML sitemap index

---

### Filter 6: Governance & Workflow

Controls risk and quality without slowing writing.

**Status Options:**
- `draft` → `review` → `scheduled` → `published` → `archived`

**Governance Fields:**
- `requires_compliance_review` - Flag for legal/compliance review
- `reviewer` - Who approved the post
- `reviewed_at` - When approved
- `review_notes` - Feedback

**Validation Tracking:**
- `validation_errors` - Publish-blocking errors
- `validation_warnings` - Non-blocking warnings

**Hard Publish Gates:**
1. ✅ Must have title
2. ✅ Must have slug
3. ✅ Must have excerpt
4. ✅ Must have body_html
5. ✅ Must have author_entity
6. ✅ Must have category_new
7. ✅ Featured image + alt text
8. ✅ SEO pack present
9. ✅ Compliance review (if flagged)

---

## Django Admin Interface

The admin is organized as tabs/fieldsets matching filter stages:

### 🖊️ Pour In (Write)
- `raw_draft` (markdown editor)
- `notes_private`

### 📄 Structured Output (Read-only)
- HTML preview
- TOC preview
- Sections preview
- FAQs preview

### 📊 Metadata
- Title, slug, excerpt (with locks)
- Author, category, tags
- Reading time, word count
- Entities preview

### 🔍 SEO Pack
- Meta title/description (with locks)
- Canonical URL
- Robots directives
- Schema type

### 📱 Social Pack
- Open Graph settings
- Twitter card settings
- Social copy (with locks)
- Hashtags

### 🤖 LLM Readiness
- LLM summary (with lock)
- Key facts preview
- Sources

### ⚙️ Governance
- Validation status & lint report
- Status, publish date
- Featured/pinned toggles
- Preview link
- Compliance review settings
- Related posts

---

## URL Routes

### Sitemaps
- `/sitemap.xml` - Sitemap index

### RSS/Atom Feeds
- `/blog/feed/rss/` - Latest posts (RSS 2.0)
- `/blog/feed/atom/` - Latest posts (Atom 1.0)
- `/blog/category/<slug>/feed/` - Category feed
- `/blog/tag/<slug>/feed/` - Tag feed

### SEO Files
- `/robots.txt` - Dynamic robots.txt
- `/llms.txt` - LLM documentation
- `/humans.txt` - Team credits
- `/.well-known/security.txt` - Security contact

---

## Models

### Core Content Models
- `Blogs` - Main blog post model with all Brita fields
- `BlogCategory` - Post categories
- `BlogTag` - Post tags  
- `BlogAuthor` - Author profiles

### Historical Tracking
- All Blogs changes tracked via `django-simple-history`
- Access history in admin at bottom of edit page

---

## Celery Tasks (Optional)

Located in `Website/tasks.py`:

- `check_post_links(post_id)` - Validate all links in a post
- `generate_og_image(post_id)` - Generate OG image
- `ping_search_engines()` - Notify search engines of updates
- `process_batch_posts(post_ids)` - Batch reprocess through pipeline

---

## Files Structure

```
Website/
├── models.py          # Blogs model with all Brita fields
├── admin.py           # Re-exports from admin_brita.py
├── admin_brita.py     # Full Brita admin implementation
├── processors.py      # 6-stage filter pipeline
├── validators.py      # SEO, accessibility, content validators
├── signals.py         # Pre/post save hooks
├── feeds.py           # RSS/Atom feeds
├── sitemaps.py        # XML sitemaps
├── seo_views.py       # robots.txt, llms.txt, etc.
├── tasks.py           # Celery async tasks

static/admin/
├── css/brita_admin.css  # Admin styling
└── js/brita_admin.js    # Admin JavaScript
```

---

## Quick Start

### 1. Create a new post
1. Go to Django Admin → Blog Posts → Add
2. Write your content in markdown in the "Pour In" section
3. Save - the pipeline auto-generates everything

### 2. Review generated content
1. Check "Structured Output" for HTML preview
2. Review "Metadata" and adjust if needed
3. Check "Governance" for validation status

### 3. Override auto-generated fields
1. Edit any auto-generated field
2. Check the "locked" checkbox to prevent future auto-updates

### 4. Publish
1. Ensure all validation errors are resolved
2. Set status to "Published"
3. Save

---

## Testing

Run the pipeline test:

```bash
python test_brita_pipeline.py
```

This validates all 6 filters are working correctly.

---

## Dependencies

Required packages:
- `django` >= 4.2
- `django-simple-history` - Revision tracking
- `bleach` - HTML sanitization

Optional:
- `celery` + `redis` - Background tasks
- `pillow` - Image processing for OG images

---

## Configuration

### Settings

```python
# Optional: Configure site URL for canonical links
SITE_URL = 'https://ingredientiq.ai'

# Optional: Celery for async tasks
CELERY_BROKER_URL = 'redis://localhost:6379/0'
```

---

## Verification Gates

### Preview Before Publish
All posts have a shareable preview URL: `/blog/preview/<uuid>/`

### SEO Lint
Automatic checks for:
- Title length (50-60 chars optimal)
- Meta description length (150-160 chars optimal)
- Missing canonical URL
- Heading structure (single H1)

### Accessibility Lint
Automatic checks for:
- Missing alt text on images
- Empty links
- Proper heading hierarchy

### Link Check (Async)
Available via Celery task for checking all links in a post.

### Policy/High-Risk Flag
Posts marked `requires_compliance_review` must be reviewed before publishing.

---

## Changelog

### v1.0 (January 2026)
- Initial Brita Filter CMS implementation
- All 6 filter stages operational
- Admin interface with tab-based organization
- RSS/Atom feeds
- XML sitemaps
- Dynamic robots.txt and llms.txt
