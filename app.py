import os
import argparse
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, Preformatted
)
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import warnings
from PIL import Image

# Disable PIL decompression bomb warning
warnings.simplefilter('ignore', Image.DecompressionBombWarning)
Image.MAX_IMAGE_PIXELS = None  # Remove size limitation

# Configuration
VALID_EXTENSIONS = ['.js', '.ts', '.json', '.html', '.css', '.jsx', '.vue', '.scss', '.md', '.geojson']
EXCLUDE_DIRS = ['node_modules', '.git', 'dist', 'build', 'coverage']
PAGE_SIZE = letter
FONT_NAME = 'Courier'  # Will use ReportLab's built-in Courier
FONT_SIZE = 8
LINE_HEIGHT = 1.0

# Get default stylesheet
styles = getSampleStyleSheet()

# Create custom styles only if they don't already exist
custom_styles = [
    ParagraphStyle(
        name='CodeHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.darkblue,
        spaceAfter=4
    ),
    ParagraphStyle(
        name='StructureHeader',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.darkblue,
        spaceBefore=20,
        spaceAfter=10,
        alignment=1
    ),
    ParagraphStyle(
        name='DirItem',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.darkblue,
        leftIndent=10,
        spaceAfter=2
    ),
    ParagraphStyle(
        name='FileItem',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.darkgreen,
        leftIndent=20,
        spaceAfter=2
    ),
    ParagraphStyle(
        name='SummaryItem',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.purple,
        spaceAfter=5
    ),
    ParagraphStyle(
        name='Code',
        fontName='Courier',
        fontSize=FONT_SIZE,
        leading=FONT_SIZE * LINE_HEIGHT,
        spaceBefore=6,
        spaceAfter=6
    )
]

# Add styles only if they don't exist
for style in custom_styles:
    if style.name not in styles:
        styles.add(style)

def should_include(path):
    """Check if path should be included in documentation"""
    # Get the normalized path parts
    path_parts = os.path.normpath(path).split(os.sep)
    
    # Check if any excluded directory is a direct component of the path
    for part in path_parts:
        if part in EXCLUDE_DIRS:
            return False
    
    if os.path.isfile(path):
        return os.path.splitext(path)[1].lower() in VALID_EXTENSIONS
    return True

def format_code(content, filename):
    """Format code with line numbers"""
    formatted_lines = []
    # Add line numbers
    for i, line in enumerate(content.splitlines()):
        formatted_lines.append(f"{i+1:4d} | {line}")
    return "\n".join(formatted_lines)

def generate_directory_structure(startpath):
    """Generate hierarchical directory structure as flowables"""
    structure = []
    
    # Header
    structure.append(Paragraph("Project Directory Structure", styles['StructureHeader']))
    
    # Recursive directory listing
    for root, dirs, files in os.walk(startpath):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if should_include(os.path.join(root, d))]
        # Filter out excluded files
        files[:] = [f for f in files if should_include(os.path.join(root, f))]
        
        # Calculate indentation level based on directory depth
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        
        # Get relative path and format display
        rel_path = os.path.relpath(root, startpath)
        if rel_path == '.':
            display_path = os.path.basename(os.path.abspath(startpath)) + '/'
        else:
            display_path = os.path.basename(root) + '/'
        
        # Add directory to structure
        structure.append(Paragraph(f"{indent}{display_path}", styles['DirItem']))
        
        # Add files in directory with extra indentation
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            structure.append(Paragraph(f"{subindent}{f}", styles['FileItem']))
    
    return structure

def generate_file_contents(root_dir):
    """Generate file contents with basic formatting"""
    contents = []
    file_count = 0
    
    for root, dirs, files in os.walk(root_dir):
        # Prune excluded directories and files
        dirs[:] = [d for d in dirs if should_include(os.path.join(root, d))]
        files[:] = [f for f in files if should_include(os.path.join(root, f))]
        
        for filename in sorted(files):
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, root_dir)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                content = f"Error reading file: {str(e)}"
            
            file_count += 1
            
            contents.append(PageBreak())
            contents.append(Paragraph(f"File: {rel_path}", styles['CodeHeader']))
            
            # Create preformatted text with basic formatting
            code = format_code(content, filename)
            contents.append(Preformatted(code, styles['Code']))
    
    return contents, file_count

def generate_project_summary(root_dir, file_count):
    """Generate project summary page"""
    summary = []
    
    # Header
    summary.append(Paragraph("Project Documentation Summary", styles['StructureHeader']))
    summary.append(Spacer(1, 0.3 * inch))
    
    # Project details
    summary.append(Paragraph(f"Project Root: {os.path.abspath(root_dir)}", styles['SummaryItem']))
    summary.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['SummaryItem']))
    
    # Count directories
    dir_count = 0
    for root, dirs, _ in os.walk(root_dir):
        dirs[:] = [d for d in dirs if should_include(os.path.join(root, d))]
        dir_count += 1
    
    summary.append(Paragraph(f"Total Directories: {dir_count}", styles['SummaryItem']))
    summary.append(Paragraph(f"Total Files Documented: {file_count}", styles['SummaryItem']))
    summary.append(Spacer(1, 0.2 * inch))
    
    # File type distribution
    ext_counts = {}
    for root, _, files in os.walk(root_dir):
        for filename in files:
            if should_include(os.path.join(root, filename)):
                ext = os.path.splitext(filename)[1].lower()
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
    
    file_type_data = [['File Type', 'Count']]
    for ext, count in sorted(ext_counts.items()):
        file_type_data.append([ext if ext else 'No Extension', str(count)])
    
    file_type_table = Table(file_type_data)
    file_type_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    summary.append(file_type_table)
    
    return summary

def generate_pdf(root_dir, output_file):
    """Generate PDF documentation for the project"""
    doc = SimpleDocTemplate(
        output_file,
        pagesize=PAGE_SIZE,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    story = []
    
    # Cover page
    story.append(Paragraph("Project Documentation", styles['Title']))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"Project: {os.path.basename(os.path.abspath(root_dir))}", styles['Heading2']))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d')}", styles['Heading3']))
    story.append(PageBreak())
    
    # Generate and add directory structure
    story.extend(generate_directory_structure(root_dir))
    story.append(PageBreak())
    
    # Generate and add file contents
    file_contents, file_count = generate_file_contents(root_dir)
    story.extend(file_contents)
    
    # Generate and add project summary
    story.append(PageBreak())
    story.extend(generate_project_summary(root_dir, file_count))
    
    doc.build(story)

if __name__ == "__main__":
    # Register the font
    try:
        pdfmetrics.registerFont(TTFont('Courier', 'cour.ttf'))
    except:
        print("Note: Using built-in font instead of Courier New")
    
    parser = argparse.ArgumentParser(description='Generate PDF documentation for a project')
    parser.add_argument('root_dir', help='Root directory of the project')
    parser.add_argument('output_pdf', help='Output PDF file path')
    args = parser.parse_args()
    
    # Convert to absolute paths
    root_dir = os.path.abspath(args.root_dir)
    output_pdf = os.path.abspath(args.output_pdf)
    
    if not os.path.isdir(root_dir):
        print(f"Error: Directory not found - {root_dir}")
        print("Please make sure you're pointing to the project directory")
        exit(1)
        
    print(f"Generating documentation for: {root_dir}")
    print("This may take several minutes for large projects...")
    
    try:
        generate_pdf(root_dir, output_pdf)
        print(f"Documentation generated successfully: {output_pdf}")
        print(f"File size: {os.path.getsize(output_pdf) // 1024} KB")
    except Exception as e:
        print(f"Error generating documentation: {str(e)}")
        exit(1)