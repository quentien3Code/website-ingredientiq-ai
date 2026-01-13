/**
 * Brita Filter CMS - Admin JavaScript
 * Provides interactive features for the Brita CMS admin
 * 
 * Features:
 * - Auto-generation of Filter 2 metadata from Filter 0 markdown
 * - Markdown file dropzone
 * - Live markdown preview
 * - Lock toggle visual feedback
 * - Character counters
 * - Auto-save to local storage
 */

(function($) {
    'use strict';
    
    // Global state
    var autoGenTimeout = null;
    var currentPostId = null;
    
    // Wait for DOM ready
    $(document).ready(function() {
        // Extract current post ID from URL
        var match = window.location.pathname.match(/\/(\d+)\//);
        currentPostId = match ? match[1] : null;
        
        initMarkdownDropzone();
        initMarkdownPreview();
        initMetadataAutoGeneration();
        initLockToggles();
        initAutoLockOnEdit();
        initCharacterCounters();
        initSlugValidation();
        initAutoSave();
    });
    
    // ============================================
    // METADATA AUTO-GENERATION FROM MARKDOWN
    // ============================================
    
    /**
     * Initialize auto-generation of Filter 2 metadata from Filter 0 markdown
     */
    function initMetadataAutoGeneration() {
        var $rawDraft = $('textarea[name="raw_draft"]');
        if (!$rawDraft.length) return;
        
        // Add "Generate Metadata" button after the raw_draft field
        var $generateBtn = $('<button type="button" class="generate-metadata-btn" style="margin: 10px 0; padding: 10px 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500;">' +
            '✨ Generate Metadata</button>');
        
        // Find the dropzone upload button and add after it, or after raw_draft
        var $uploadBtn = $('.dropzone-upload-btn');
        if ($uploadBtn.length) {
            $uploadBtn.after($generateBtn);
        } else {
            $rawDraft.after($generateBtn);
        }
        
        // Button click handler
        $generateBtn.on('click', function(e) {
            e.preventDefault();
            var markdown = $rawDraft.val();
            generateMetadataFromMarkdown(markdown, true);
        });
        
        // Auto-generate on markdown changes (debounced)
        $rawDraft.on('input', function() {
            clearTimeout(autoGenTimeout);
            autoGenTimeout = setTimeout(function() {
                var markdown = $rawDraft.val();
                generateMetadataFromMarkdown(markdown, false);
            }, 500); // 500ms debounce
        });
    }
    
    /**
     * Generate all Filter 2 metadata fields from markdown content
     * @param {string} markdown - The raw markdown content
     * @param {boolean} notify - Whether to show success toast
     */
    function generateMetadataFromMarkdown(markdown, notify) {
        if (!markdown || !markdown.trim()) return;
        
        var fieldsUpdated = 0;
        
        // Generate Title
        if (!isFieldLocked('title')) {
            var title = extractTitle(markdown);
            if (title && setFieldValue('title', title)) {
                fieldsUpdated++;
            }
        }
        
        // Generate Slug (from title)
        if (!isFieldLocked('slug')) {
            var currentTitle = $('[name="title"]').val();
            if (currentTitle) {
                var slug = generateSlug(currentTitle);
                if (slug && setFieldValue('slug', slug)) {
                    fieldsUpdated++;
                    // Validate slug uniqueness
                    validateSlugUniqueness(slug);
                }
            }
        }
        
        // Generate Excerpt
        if (!isFieldLocked('excerpt')) {
            var excerpt = extractExcerpt(markdown);
            if (excerpt && setFieldValue('excerpt', excerpt)) {
                fieldsUpdated++;
            }
        }
        
        // Generate Key Takeaways
        if (!isFieldLocked('key_takeaways')) {
            var takeaways = extractKeyTakeaways(markdown);
            if (takeaways && takeaways.length > 0) {
                // Key takeaways is a JSON field
                var $field = $('[name="key_takeaways"]');
                if ($field.length) {
                    $field.val(JSON.stringify(takeaways, null, 2));
                    fieldsUpdated++;
                }
            }
        }
        
        if (notify && fieldsUpdated > 0) {
            showNotification('✅ Metadata updated (' + fieldsUpdated + ' fields)', 'success');
        }
    }
    
    /**
     * Extract title from markdown (first H1)
     */
    function extractTitle(markdown) {
        // Look for first H1
        var h1Match = markdown.match(/^#\s+(.+)$/m);
        if (h1Match) {
            return h1Match[1].trim().substring(0, 255);
        }
        
        // Fallback: first non-empty line
        var lines = markdown.split('\n');
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (line && !line.startsWith('#') && !line.startsWith('-') && !line.startsWith('*')) {
                return line.substring(0, 70);
            }
        }
        
        return 'Untitled';
    }
    
    /**
     * Generate URL-safe slug from title
     */
    function generateSlug(title) {
        return title
            .toLowerCase()
            .trim()
            // Remove punctuation and special chars
            .replace(/[^\w\s-]/g, '')
            // Replace spaces with hyphens
            .replace(/\s+/g, '-')
            // Collapse multiple hyphens
            .replace(/-+/g, '-')
            // Trim hyphens from start/end
            .replace(/^-+|-+$/g, '')
            // Limit length
            .substring(0, 75);
    }
    
    /**
     * Extract excerpt from markdown (155-180 chars, max 500)
     */
    function extractExcerpt(markdown) {
        // Strip markdown formatting
        var text = stripMarkdown(markdown);
        
        // Remove the title (first line if it was H1)
        var lines = text.split('\n').filter(function(l) { return l.trim(); });
        
        // Skip lines that look like headings or list items
        var contentLines = [];
        var skipFirst = markdown.match(/^#\s+/m); // If there was an H1
        var skipped = false;
        
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            
            // Skip first line if it was the title
            if (!skipped && skipFirst && i === 0) {
                skipped = true;
                continue;
            }
            
            // Skip headings and list markers
            if (line.match(/^(#{1,6}\s|[-*+]\s|\d+\.\s)/)) {
                continue;
            }
            
            // Skip very short lines (likely formatting)
            if (line.length < 10) continue;
            
            contentLines.push(line);
        }
        
        // Join and create excerpt
        var content = contentLines.join(' ').replace(/\s+/g, ' ').trim();
        
        if (!content) return '';
        
        // Target 155-180 chars
        var excerpt = '';
        var sentences = content.match(/[^.!?]+[.!?]+/g) || [content];
        
        for (var j = 0; j < sentences.length; j++) {
            var sentence = sentences[j].trim();
            if (excerpt.length + sentence.length <= 180) {
                excerpt += (excerpt ? ' ' : '') + sentence;
            } else if (excerpt.length >= 155) {
                break;
            } else {
                // Need more content but next sentence too long
                // Truncate the sentence
                var remaining = 180 - excerpt.length - 1;
                if (remaining > 20) {
                    var truncated = sentence.substring(0, remaining);
                    // Try to break at word boundary
                    var lastSpace = truncated.lastIndexOf(' ');
                    if (lastSpace > remaining - 30) {
                        truncated = truncated.substring(0, lastSpace);
                    }
                    excerpt += (excerpt ? ' ' : '') + truncated + '...';
                }
                break;
            }
        }
        
        // Ensure we don't exceed 500
        return excerpt.substring(0, 500);
    }
    
    /**
     * Extract key takeaways from markdown
     */
    function extractKeyTakeaways(markdown) {
        var takeaways = [];
        
        // 1. Look for "Key Takeaways", "TL;DR", "Summary" section
        var sectionPatterns = [
            /^##?\s*(key\s*takeaways?|takeaways?|tl;?dr|summary)\s*$/im,
        ];
        
        for (var i = 0; i < sectionPatterns.length; i++) {
            var match = markdown.match(sectionPatterns[i]);
            if (match) {
                // Find the content after this heading
                var startIndex = match.index + match[0].length;
                var afterHeading = markdown.substring(startIndex);
                
                // Extract bullet points until next heading or end
                var bulletMatch;
                var bulletPattern = /^[-*+]\s+(.+)$/gm;
                var count = 0;
                
                while ((bulletMatch = bulletPattern.exec(afterHeading)) !== null && count < 7) {
                    // Stop if we hit another heading
                    var beforeBullet = afterHeading.substring(0, bulletMatch.index);
                    if (beforeBullet.match(/^##?\s+/m)) break;
                    
                    var point = bulletMatch[1].trim();
                    if (point.length > 0 && point.length <= 120) {
                        takeaways.push(point);
                        count++;
                    }
                }
                
                if (takeaways.length >= 3) {
                    return takeaways;
                }
            }
        }
        
        // 2. Fallback: extract from first meaningful bullet list
        if (takeaways.length < 3) {
            var bulletPattern = /^[-*+]\s+(.+)$/gm;
            var bulletMatch;
            var allBullets = [];
            
            while ((bulletMatch = bulletPattern.exec(markdown)) !== null) {
                var point = bulletMatch[1].trim();
                // Filter out very short or very long items
                if (point.length >= 15 && point.length <= 120) {
                    allBullets.push(point);
                }
            }
            
            // Take first 5 meaningful bullets
            takeaways = allBullets.slice(0, 5);
        }
        
        // 3. If still not enough, generate from paragraphs
        if (takeaways.length < 3) {
            var text = stripMarkdown(markdown);
            var sentences = text.match(/[^.!?]+[.!?]+/g) || [];
            
            // Filter for action-oriented sentences
            var actionSentences = sentences.filter(function(s) {
                s = s.trim();
                return s.length >= 30 && s.length <= 120 &&
                       !s.match(/^(the|this|that|it|a|an)\s/i);
            });
            
            for (var j = 0; j < Math.min(5, actionSentences.length); j++) {
                if (takeaways.length < 7) {
                    takeaways.push(actionSentences[j].trim());
                }
            }
        }
        
        return takeaways.slice(0, 7);
    }
    
    /**
     * Strip markdown formatting from text
     */
    function stripMarkdown(md) {
        return md
            // Remove headers
            .replace(/^#{1,6}\s+/gm, '')
            // Remove bold/italic
            .replace(/\*\*(.+?)\*\*/g, '$1')
            .replace(/\*(.+?)\*/g, '$1')
            .replace(/__(.+?)__/g, '$1')
            .replace(/_(.+?)_/g, '$1')
            // Remove links, keep text
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
            // Remove images
            .replace(/!\[([^\]]*)\]\([^)]+\)/g, '')
            // Remove code blocks
            .replace(/```[\s\S]*?```/g, '')
            .replace(/`([^`]+)`/g, '$1')
            // Remove blockquotes
            .replace(/^>\s+/gm, '')
            // Remove horizontal rules
            .replace(/^---+$/gm, '')
            .replace(/^\*\*\*+$/gm, '')
            // Remove list markers
            .replace(/^[-*+]\s+/gm, '')
            .replace(/^\d+\.\s+/gm, '')
            // Clean up whitespace
            .replace(/\n{3,}/g, '\n\n')
            .trim();
    }
    
    /**
     * Check if a field is locked
     */
    function isFieldLocked(fieldName) {
        var $lock = $('[name="' + fieldName + '_locked"]');
        return $lock.length && $lock.is(':checked');
    }
    
    /**
     * Set field value (returns true if changed)
     */
    function setFieldValue(fieldName, value) {
        var $field = $('[name="' + fieldName + '"]');
        if (!$field.length) return false;
        
        var currentValue = $field.val();
        if (currentValue !== value) {
            $field.val(value);
            $field.trigger('input'); // Trigger for counters etc
            return true;
        }
        return false;
    }
    
    // ============================================
    // SLUG VALIDATION
    // ============================================
    
    /**
     * Initialize slug uniqueness validation
     */
    function initSlugValidation() {
        var $slug = $('[name="slug"]');
        if (!$slug.length) return;
        
        // Add warning container
        var $warning = $('<div class="slug-warning" style="color: #dc3545; font-size: 12px; margin-top: 5px; display: none;"></div>');
        $slug.after($warning);
        
        // Validate on change
        var validateTimeout;
        $slug.on('input', function() {
            clearTimeout(validateTimeout);
            validateTimeout = setTimeout(function() {
                validateSlugUniqueness($slug.val());
            }, 300);
        });
    }
    
    /**
     * Validate slug uniqueness via AJAX
     */
    function validateSlugUniqueness(slug) {
        if (!slug) return;
        
        var $warning = $('.slug-warning');
        
        // Call our custom API endpoint
        $.ajax({
            url: '/web/api/validate-slug/',
            method: 'GET',
            data: { 
                slug: slug,
                exclude_id: currentPostId || ''
            },
            dataType: 'json',
            success: function(response) {
                if (response.exists) {
                    $warning.text('⚠️ Blog Post with this Slug already exists.').show();
                } else {
                    $warning.hide();
                }
            },
            error: function() {
                // Silent fail - slug will be validated on save
                $warning.hide();
            }
        });
    }
    
    // ============================================
    // AUTO-LOCK ON MANUAL EDIT
    // ============================================
    
    /**
     * Auto-lock fields when user manually edits them
     */
    function initAutoLockOnEdit() {
        var lockableFields = ['title', 'slug', 'excerpt', 'key_takeaways'];
        
        lockableFields.forEach(function(fieldName) {
            var $field = $('[name="' + fieldName + '"]');
            var $lock = $('[name="' + fieldName + '_locked"]');
            
            if (!$field.length || !$lock.length) return;
            
            // On keydown (actual typing), auto-lock
            $field.on('keydown', function(e) {
                // Ignore modifier keys and navigation
                if (e.ctrlKey || e.metaKey || e.key === 'Tab' || e.key === 'Shift') return;
                
                // If not already locked and user is typing, lock it
                if (!$lock.is(':checked')) {
                    $lock.prop('checked', true).trigger('change');
                    showNotification('🔒 ' + fieldName.replace(/_/g, ' ') + ' locked (manual edit)', 'info');
                }
            });
        });
    }
    
    // ============================================
    // NOTIFICATION HELPER (shared)
    // ============================================
    
    /**
     * Show toast notification
     */
    function showNotification(message, type) {
        var bgColor = {
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8'
        }[type] || '#6c757d';
        
        var textColor = type === 'warning' ? '#000' : '#fff';
        
        var $notification = $('<div class="brita-notification">' + message + '</div>');
        $notification.css({
            'position': 'fixed',
            'top': '20px',
            'right': '20px',
            'padding': '12px 20px',
            'background': bgColor,
            'color': textColor,
            'border-radius': '4px',
            'box-shadow': '0 2px 10px rgba(0,0,0,0.2)',
            'z-index': 10000,
            'font-size': '14px',
            'max-width': '350px'
        });
        
        $('body').append($notification);
        
        setTimeout(function() {
            $notification.fadeOut(300, function() {
                $(this).remove();
            });
        }, 3000);
    }
    
    // ============================================
    // MARKDOWN DROPZONE
    // ============================================
    
    /**
     * Initialize drag-and-drop dropzone for markdown files
     */
    function initMarkdownDropzone() {
        var $rawDraft = $('textarea[name="raw_draft"]');
        
        if (!$rawDraft.length) return;
        
        // Create dropzone overlay
        var $dropzone = $('<div class="markdown-dropzone">' +
            '<div class="dropzone-content">' +
            '<div class="dropzone-icon">📄</div>' +
            '<div class="dropzone-text">Drop Markdown file here</div>' +
            '<div class="dropzone-subtext">.md, .txt, or .markdown files</div>' +
            '</div>' +
            '</div>');
        
        // Create file input for click-to-upload
        var $fileInput = $('<input type="file" accept=".md,.txt,.markdown,text/markdown,text/plain" style="display: none;">');
        
        // Create upload button
        var $uploadBtn = $('<button type="button" class="dropzone-upload-btn" style="margin: 5px 0 10px 0; padding: 8px 15px; background: #17a2b8; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px;">' +
            '📁 Import Markdown File</button>');
        
        // Wrap textarea in a dropzone container
        var $container = $('<div class="dropzone-container" style="position: relative;"></div>');
        $rawDraft.before($uploadBtn).before($fileInput);
        $rawDraft.wrap($container);
        $rawDraft.parent().append($dropzone);
        
        // Style the dropzone overlay
        $dropzone.css({
            'position': 'absolute',
            'top': 0,
            'left': 0,
            'right': 0,
            'bottom': 0,
            'background': 'rgba(76, 175, 80, 0.95)',
            'display': 'none',
            'align-items': 'center',
            'justify-content': 'center',
            'border': '3px dashed #fff',
            'border-radius': '4px',
            'z-index': 100,
            'pointer-events': 'none'
        });
        
        $dropzone.find('.dropzone-content').css({
            'text-align': 'center',
            'color': 'white'
        });
        
        $dropzone.find('.dropzone-icon').css({
            'font-size': '48px',
            'margin-bottom': '10px'
        });
        
        $dropzone.find('.dropzone-text').css({
            'font-size': '18px',
            'font-weight': 'bold'
        });
        
        $dropzone.find('.dropzone-subtext').css({
            'font-size': '12px',
            'opacity': 0.8,
            'margin-top': '5px'
        });
        
        // Click button to trigger file input
        $uploadBtn.on('click', function(e) {
            e.preventDefault();
            $fileInput.click();
        });
        
        // Handle file selection
        $fileInput.on('change', function(e) {
            var file = e.target.files[0];
            if (file) {
                handleFile(file, $rawDraft);
            }
            $(this).val('');
        });
        
        // Drag and drop handlers
        var $dropArea = $rawDraft.parent();
        var dragCounter = 0;
        
        $dropArea.on('dragenter', function(e) {
            e.preventDefault();
            e.stopPropagation();
            dragCounter++;
            $dropzone.css('display', 'flex');
        });
        
        $dropArea.on('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            dragCounter--;
            if (dragCounter === 0) {
                $dropzone.hide();
            }
        });
        
        $dropArea.on('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
        
        $dropArea.on('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            dragCounter = 0;
            $dropzone.hide();
            
            var files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0], $rawDraft);
            }
        });
        
        $rawDraft.on('dragenter dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
        
        $rawDraft.on('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            var files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0], $rawDraft);
            }
        });
        
        function handleFile(file, $textarea) {
            var validTypes = ['text/markdown', 'text/plain', 'text/x-markdown'];
            var validExtensions = ['.md', '.txt', '.markdown'];
            var fileName = file.name.toLowerCase();
            var isValid = validTypes.includes(file.type) || 
                          validExtensions.some(function(ext) { return fileName.endsWith(ext); });
            
            if (!isValid) {
                alert('Please drop a Markdown file (.md, .txt, or .markdown)');
                return;
            }
            
            if (file.size > 1024 * 1024) {
                alert('File is too large. Maximum size is 1MB.');
                return;
            }
            
            var reader = new FileReader();
            reader.onload = function(e) {
                var content = e.target.result;
                var currentContent = $textarea.val().trim();
                
                if (currentContent) {
                    var action = confirm(
                        'Current content exists.\n\n' +
                        'OK = Replace all content\n' +
                        'Cancel = Append to existing content'
                    );
                    
                    if (action) {
                        $textarea.val(content);
                    } else {
                        $textarea.val(currentContent + '\n\n---\n\n' + content);
                    }
                } else {
                    $textarea.val(content);
                }
                
                $textarea.trigger('input');
                showNotification('✅ Imported: ' + file.name, 'success');
            };
            
            reader.onerror = function() {
                alert('Error reading file. Please try again.');
            };
            
            reader.readAsText(file);
        }
    }
    
    // ============================================
    // MARKDOWN PREVIEW
    // ============================================
    
    /**
     * Initialize markdown preview
     */
    function initMarkdownPreview() {
        var $rawDraft = $('textarea[name="raw_draft"]');
        
        if (!$rawDraft.length) return;
        
        var $toggleBtn = $('<button type="button" class="preview-toggle" style="margin: 5px 5px 5px 0; padding: 5px 10px; background: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer;">📄 Toggle Preview</button>');
        var $preview = $('<div class="markdown-preview" style="display: none; padding: 15px; background: #fafafa; border: 1px solid #ddd; border-radius: 4px; max-height: 400px; overflow-y: auto; margin-top: 10px;"></div>');
        
        // Insert after generate button if exists
        var $generateBtn = $('.generate-metadata-btn');
        if ($generateBtn.length) {
            $generateBtn.after($toggleBtn);
        } else {
            $rawDraft.after($toggleBtn);
        }
        $rawDraft.parent().after($preview);
        
        $toggleBtn.on('click', function() {
            $preview.toggle();
            if ($preview.is(':visible')) {
                updatePreview();
                $(this).text('🖊️ Hide Preview');
            } else {
                $(this).text('📄 Toggle Preview');
            }
        });
        
        var previewTimeout;
        $rawDraft.on('input', function() {
            clearTimeout(previewTimeout);
            previewTimeout = setTimeout(function() {
                if ($preview.is(':visible')) {
                    updatePreview();
                }
            }, 500);
        });
        
        function updatePreview() {
            var markdown = $rawDraft.val();
            var html = markdownToHtml(markdown);
            $preview.html(html);
        }
    }
    
    /**
     * Simple markdown to HTML converter
     */
    function markdownToHtml(md) {
        if (!md) return '<em style="color: #999;">Start typing to see preview...</em>';
        
        var html = md
            .replace(/^###### (.+)$/gm, '<h6>$1</h6>')
            .replace(/^##### (.+)$/gm, '<h5>$1</h5>')
            .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/^\* (.+)$/gm, '<li>$1</li>')
            .replace(/^- (.+)$/gm, '<li>$1</li>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
            .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>');
        
        return html;
    }
    
    // ============================================
    // LOCK TOGGLES
    // ============================================
    
    /**
     * Initialize lock toggle behavior
     */
    function initLockToggles() {
        var lockFields = [
            'title', 'slug', 'excerpt', 'meta_title', 'meta_description',
            'key_takeaways', 'social_copy_linkedin', 'social_copy_twitter',
            'social_hashtags', 'summary_for_llms'
        ];
        
        lockFields.forEach(function(field) {
            var $field = $('[name="' + field + '"]');
            var $lock = $('[name="' + field + '_locked"]');
            
            if ($field.length && $lock.length) {
                updateLockState($field, $lock.is(':checked'));
                
                $lock.on('change', function() {
                    updateLockState($field, $(this).is(':checked'));
                    
                    // Show unlock notification
                    if (!$(this).is(':checked')) {
                        showNotification('🔓 ' + field.replace(/_/g, ' ') + ' unlocked - will auto-update', 'info');
                    }
                });
            }
        });
        
        function updateLockState($field, isLocked) {
            if (isLocked) {
                $field.css({
                    'background-color': '#fff8dc',
                    'border-color': '#daa520'
                });
                $field.closest('.field-box, .form-row').find('label').first()
                    .css('color', '#856404');
            } else {
                $field.css({
                    'background-color': '',
                    'border-color': ''
                });
                $field.closest('.field-box, .form-row').find('label').first()
                    .css('color', '');
            }
        }
    }
    
    // ============================================
    // CHARACTER COUNTERS
    // ============================================
    
    /**
     * Initialize character counters for fields with limits
     */
    function initCharacterCounters() {
        var fieldsWithLimits = {
            'meta_title': { max: 60, warn: 55 },
            'meta_description': { max: 160, warn: 150 },
            'excerpt': { max: 500, warn: 180, ideal: { min: 155, max: 180 } },
            'og_title': { max: 95, warn: 90 },
            'og_description': { max: 200, warn: 190 },
            'social_copy_twitter': { max: 280, warn: 250 }
        };
        
        Object.keys(fieldsWithLimits).forEach(function(field) {
            var $field = $('[name="' + field + '"]');
            if (!$field.length) return;
            
            var limits = fieldsWithLimits[field];
            var $counter = $('<span class="char-counter" style="font-size: 11px; margin-left: 10px;"></span>');
            $field.after($counter);
            
            function updateCounter() {
                var len = $field.val().length;
                var remaining = limits.max - len;
                
                var displayText = len + '/' + limits.max;
                
                // For excerpt, show ideal range indicator
                if (limits.ideal) {
                    if (len >= limits.ideal.min && len <= limits.ideal.max) {
                        displayText += ' ✓ ideal';
                    } else if (len > 0 && len < limits.ideal.min) {
                        displayText += ' (aim for ' + limits.ideal.min + '-' + limits.ideal.max + ')';
                    }
                }
                
                $counter.text(displayText);
                
                if (remaining < 0) {
                    $counter.css('color', '#dc3545');
                } else if (limits.ideal && len >= limits.ideal.min && len <= limits.ideal.max) {
                    $counter.css('color', '#28a745');
                } else if (len >= limits.warn) {
                    $counter.css('color', '#ffc107');
                } else {
                    $counter.css('color', '#6c757d');
                }
            }
            
            $field.on('input', updateCounter);
            updateCounter();
        });
    }
    
    // ============================================
    // AUTO-SAVE
    // ============================================
    
    /**
     * Initialize auto-save (local storage backup)
     */
    function initAutoSave() {
        var $rawDraft = $('textarea[name="raw_draft"]');
        if (!$rawDraft.length) return;
        
        var storageKey = 'brita_draft_' + (currentPostId || 'new');
        
        var savedDraft = localStorage.getItem(storageKey);
        var savedTime = localStorage.getItem(storageKey + '_time');
        
        if (savedDraft && savedTime) {
            var savedDate = new Date(parseInt(savedTime));
            var current = $rawDraft.val();
            
            if (savedDraft !== current && savedDraft.length > current.length) {
                if (confirm('Found unsaved draft from ' + savedDate.toLocaleString() + '. Restore it?')) {
                    $rawDraft.val(savedDraft);
                    $rawDraft.trigger('input');
                }
            }
        }
        
        var saveTimeout;
        $rawDraft.on('input', function() {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(function() {
                localStorage.setItem(storageKey, $rawDraft.val());
                localStorage.setItem(storageKey + '_time', Date.now().toString());
            }, 2000);
        });
        
        $('form').on('submit', function() {
            localStorage.removeItem(storageKey);
            localStorage.removeItem(storageKey + '_time');
        });
    }
    
})(django.jQuery || jQuery);
