import os
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, ListFlowable, ListItem, Preformatted
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

# Configuration
VALID_EXTENSIONS = ['.js', '.ts', '.json', '.html', '.css', '.jsx', '.vue', '.scss', '.md']
EXCLUDE_DIRS = ['node_modules', '.git', 'dist', 'build', 'coverage']
SYNTAX_STYLE = 'monokai'

FONT_NAME = 'Courier'  # Will use ReportLab's built-in Courier
FONT_SIZE = 8
LINE_HEIGHT = 1.0

# Custom styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='CodeHeader',
    fontName='Helvetica-Bold',
    fontSize=10,
    textColor=colors.darkblue,
    spaceAfter=4
))
styles.add(ParagraphStyle(
    name='StructureHeader',
    fontName='Helvetica-Bold',
    fontSize=14,
    textColor=colors.darkblue,
    spaceBefore=20,
    spaceAfter=10,
    alignment=1
))
styles.add(ParagraphStyle(
    name='DirItem',
    fontName='Helvetica',
    fontSize=10,
    textColor=colors.darkblue,
    leftIndent=10,
    spaceAfter=2
))
styles.add(ParagraphStyle(
    name='FileItem',
    fontName='Helvetica',
    fontSize=10,
    textColor=colors.darkgreen,
    leftIndent=20,
    spaceAfter=2
))
styles.add(ParagraphStyle(
    name='SummaryItem',
    fontName='Helvetica-Bold',
    fontSize=10,
    textColor=colors.purple,
    spaceAfter=5
))
def should_include(path):
    """Check if path should be included in documentation"""
    path_parts = path.split(os.sep)
    if any(excl in path_parts for excl in EXCLUDE_DIRS):
        return False
    if os.path.isfile(path):
        return os.path.splitext(path)[1].lower() in VALID_EXTENSIONS
    return True
def generate_directory_structure(startpath):
    """Generate hierarchical directory structure as flowables"""
    structure = []
    
    # Header
    structure.append(Paragraph("Project Directory Structure", styles['StructureHeader']))
    
    # Recursive directory listing
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if should_include(os.path.join(root, d))]
        files[:] = [f for f in files if should_include(os.path.join(root, f))]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        
        # Add directory item
        rel_path = os.path.relpath(root, startpath)
        if rel_path == '.':
            display_path = os.path.basename(os.path.abspath(startpath)) + '/'
        else:
            display_path = os.path.basename(root) + '/'
        
        structure.append(Paragraph(f"{indent}{display_path}", styles['DirItem']))
        
        # Add files in directory
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            structure.append(Paragraph(f"{subindent}{f}", styles['FileItem']))
    
    return structure

if __name__ == "__main__":
    # Test directory structure visualization
    root_dir = os.path.abspath("./application")  # Point to your application directory
    structure = generate_directory_structure(root_dir)
    
    # Print to console
    print("Directory Structure:")
    for item in structure:
        if hasattr(item, 'text'):
            print(item.text)
    
    # Or save to text file
    with open("directory_structure.txt", "w") as f:
        for item in structure:
            if hasattr(item, 'text'):
                f.write(item.text + "\n")
    print("Saved to directory_structure.txt")