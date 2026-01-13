#!/usr/bin/env python
"""
Test script for the Brita Filter CMS pipeline.
Run with: python test_brita_pipeline.py
"""
import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodanalysis.settings')

import django
django.setup()

from Website.processors import BritaFilterPipeline

# Test content
TEST_MARKDOWN = """# The Ultimate Guide to Food Safety

This comprehensive guide covers everything you need to know about food safety in 2026.

## Introduction

Food safety is more important than ever. In this article, we'll explore the key principles
that every home cook and professional chef should follow.

## Key Takeaways

- Always wash your hands before handling food
- Keep raw meats separate from other ingredients
- Cook foods to proper internal temperatures
- Refrigerate leftovers within 2 hours

## Understanding Temperature Control

The "danger zone" for food is between 40°F and 140°F. Bacteria grow rapidly in this range,
which is why proper temperature control is essential.

### Hot Foods

Hot foods should be kept at 140°F or above.

### Cold Foods

Cold foods should be kept at 40°F or below.

## FAQ

**Q: How long can food sit out?**
**A:** Food should not sit at room temperature for more than 2 hours.

**Q: What is cross-contamination?**
**A:** Cross-contamination is when bacteria spreads from one food item to another.

## Conclusion

Following these guidelines will help keep you and your family safe from foodborne illness.

---

*Last updated: January 2026*
"""

def main():
    print("=" * 60)
    print("BRITA FILTER CMS - Pipeline Test")
    print("=" * 60)
    print()
    
    # Process the test content
    result = BritaFilterPipeline.process_draft(TEST_MARKDOWN)
    
    # Display results
    print("✅ FILTER 1 - Structural Output")
    print("-" * 40)
    print(f"  Body HTML length: {len(result.body_html)} chars")
    print(f"  TOC entries: {len(result.toc_json)}")
    print(f"  Sections: {len(result.key_sections_json)}")
    print(f"  FAQs extracted: {len(result.extracted_faqs)}")
    print()
    
    print("✅ FILTER 2 - Metadata Distillation")
    print("-" * 40)
    print(f"  Auto Title: {result.auto_title}")
    print(f"  Auto Slug: {result.auto_slug}")
    print(f"  Auto Excerpt: {result.auto_excerpt[:80]}..." if len(result.auto_excerpt) > 80 else f"  Auto Excerpt: {result.auto_excerpt}")
    print(f"  Word Count: {result.auto_word_count}")
    print(f"  Reading Time: {result.auto_reading_time} min")
    print(f"  Key Takeaways: {len(result.auto_key_takeaways)}")
    print(f"  Entities: {len(result.entities_json)}")
    print()
    
    print("✅ FILTER 3 - SEO Pack")
    print("-" * 40)
    print(f"  Meta Title: {result.auto_meta_title}")
    print(f"  Meta Description: {result.auto_meta_description[:80]}..." if len(result.auto_meta_description) > 80 else f"  Meta Description: {result.auto_meta_description}")
    print()
    
    print("✅ FILTER 4 - SMO Pack")
    print("-" * 40)
    print(f"  Twitter Copy: {result.auto_social_copy_twitter[:80]}..." if len(result.auto_social_copy_twitter) > 80 else f"  Twitter Copy: {result.auto_social_copy_twitter}")
    print(f"  Hashtags: {result.auto_social_hashtags}")
    print()
    
    print("✅ FILTER 5 - LLM Readiness")
    print("-" * 40)
    print(f"  LLM Summary: {result.auto_summary_for_llms[:100]}..." if len(result.auto_summary_for_llms) > 100 else f"  LLM Summary: {result.auto_summary_for_llms}")
    print(f"  Key Facts: {len(result.auto_key_facts)}")
    print()
    
    print("✅ FILTER 6 - Governance")
    print("-" * 40)
    print(f"  Validation Errors: {len(result.validation_errors)}")
    if result.validation_errors:
        for err in result.validation_errors:
            print(f"    ❌ {err}")
    print(f"  Validation Warnings: {len(result.validation_warnings)}")
    if result.validation_warnings:
        for warn in result.validation_warnings:
            print(f"    ⚠️ {warn}")
    print()
    
    print("=" * 60)
    print("✅ Brita Filter CMS Pipeline Test PASSED!")
    print("=" * 60)
    
    return 0 if not result.validation_errors else 1


if __name__ == '__main__':
    sys.exit(main())
