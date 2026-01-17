#!/usr/bin/env python
"""
PDF export functionality for YouTube comments
Generates PDF documents with comments
"""

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_pdf_output(comments, output_path, filtered_user=None, post_metadata=None):
    """
    Generate a PDF file with comments
    
    Args:
        comments: List of comment dictionaries
        output_path: Path to output PDF file
        filtered_user: Username that was filtered (for display in header)
        post_metadata: Optional post metadata dict (for community posts)
    
    Raises:
        ImportError: If reportlab is not installed
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is required for PDF export. Install it with: pip install reportlab")
    
    # Build comment hierarchy
    comment_map = {c['cid']: c for c in comments}
    root_comments = []
    
    # Organize comments into threads
    for comment in comments:
        if comment.get('reply'):
            # This is a reply - find its parent
            parent_cid = comment['cid'].rsplit('.', 1)[0]
            parent = comment_map.get(parent_cid)
            if parent:
                if 'thread_replies' not in parent:
                    parent['thread_replies'] = []
                parent['thread_replies'].append(comment)
        else:
            # This is a root comment
            root_comments.append(comment)
    
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CommentAuthor',
                             parent=styles['Normal'],
                             fontSize=10,
                             textColor='#000000',
                             spaceAfter=2,
                             fontName='Helvetica-Bold'))
    
    styles.add(ParagraphStyle(name='CommentText',
                             parent=styles['Normal'],
                             fontSize=9,
                             textColor='#333333',
                             spaceAfter=6,
                             alignment=TA_LEFT))
    
    styles.add(ParagraphStyle(name='CommentMeta',
                             parent=styles['Normal'],
                             fontSize=8,
                             textColor='#666666',
                             spaceAfter=10))
    
    styles.add(ParagraphStyle(name='ReplyAuthor',
                             parent=styles['Normal'],
                             fontSize=9,
                             textColor='#000000',
                             spaceAfter=2,
                             fontName='Helvetica-Bold',
                             leftIndent=20))
    
    styles.add(ParagraphStyle(name='ReplyText',
                             parent=styles['Normal'],
                             fontSize=8,
                             textColor='#333333',
                             spaceAfter=4,
                             leftIndent=20))
    
    styles.add(ParagraphStyle(name='ReplyMeta',
                             parent=styles['Normal'],
                             fontSize=7,
                             textColor='#666666',
                             spaceAfter=8,
                             leftIndent=20))
    
    # Add title
    title_style = styles['Title']
    title_text = "YouTube Comments"
    if filtered_user:
        title_text += f" - Filtered by {filtered_user}"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    if not root_comments:
        elements.append(Paragraph("No comments available.", styles['Normal']))
    else:
        # Add each comment
        for i, comment in enumerate(root_comments):
            if i > 0:
                elements.append(Spacer(1, 0.15*inch))
            
            _add_comment_to_pdf(elements, comment, styles, comment_map)
    
    # Build PDF
    doc.build(elements)


def _add_comment_to_pdf(elements, comment, styles, comment_map, is_reply=False):
    """
    Add a single comment and its replies to the PDF
    
    Args:
        elements: List of PDF elements
        comment: Comment dictionary
        styles: PDF styles
        comment_map: Map of all comments by ID
        is_reply: Whether this is a reply comment
    """
    # Escape HTML special characters for PDF
    def escape_text(text):
        if not text:
            return ""
        # Replace special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        # Convert line breaks to <br/> tags for reportlab
        text = text.replace('\n', '<br/>')
        return text
    
    author = escape_text(comment.get('author', 'Unknown'))
    text = escape_text(comment.get('text', ''))
    time_str = escape_text(comment.get('time', ''))
    votes = escape_text(str(comment.get('votes', '0')))
    hearted = comment.get('heart', False)
    
    # Choose styles based on whether this is a reply
    author_style = styles['ReplyAuthor'] if is_reply else styles['CommentAuthor']
    text_style = styles['ReplyText'] if is_reply else styles['CommentText']
    meta_style = styles['ReplyMeta'] if is_reply else styles['CommentMeta']
    
    # Add author and time
    author_text = f"{author}"
    if time_str:
        author_text += f" • {time_str}"
    elements.append(Paragraph(author_text, author_style))
    
    # Add hearted indicator
    if hearted:
        elements.append(Paragraph("♥ Hearted by Creator", meta_style))
    
    # Add comment text
    if text:
        elements.append(Paragraph(text, text_style))
    
    # Add vote count
    if votes and votes != '0':
        elements.append(Paragraph(f"👍 {votes}", meta_style))
    
    # Add replies
    replies = comment.get('thread_replies', [])
    if replies:
        elements.append(Spacer(1, 0.05*inch))
        for reply in replies:
            _add_comment_to_pdf(elements, reply, styles, comment_map, is_reply=True)
