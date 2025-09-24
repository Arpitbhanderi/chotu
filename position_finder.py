"""
PDF Position Finder Tool
Creates a test overlay with grid lines and text to help find correct positions
"""

import os
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import red, blue, green, black
from reportlab.lib.units import mm
import tempfile

def create_position_finder():
    """Create a position finder overlay to help identify correct coordinates"""
    
    # Create temporary file for overlay
    overlay_fd, overlay_path = tempfile.mkstemp(suffix='.pdf')
    os.close(overlay_fd)
    
    # Create overlay canvas
    c = canvas.Canvas(overlay_path, pagesize=A4)
    
    # Draw grid lines every 50 points
    c.setStrokeColor(blue)
    c.setLineWidth(0.5)
    
    # Vertical lines
    for x in range(0, int(A4[0]), 50):
        c.line(x, 0, x, A4[1])
        c.setFillColor(blue)
        c.setFont("Helvetica", 8)
        c.drawString(x + 2, 10, str(x))
    
    # Horizontal lines
    for y in range(0, int(A4[1]), 50):
        c.line(0, y, A4[0], y)
        c.setFillColor(blue)
        c.setFont("Helvetica", 8)
        c.drawString(10, y + 2, str(y))
    
    # Draw current position markers
    positions = {
        'invoice_number': (480, 665),
        'invoice_date': (480, 640),
        'customer_name': (100, 590),
        'customer_mobile': (400, 590),
        'customer_village': (100, 565),
        'total_amount': (520, 200),
    }
    
    # Mark current positions with red dots and labels
    c.setFillColor(red)
    c.setFont("Helvetica", 10)
    
    for label, (x, y) in positions.items():
        # Draw red circle
        c.circle(x, y, 5, fill=1)
        # Draw label
        c.drawString(x + 10, y, f"{label} ({x}, {y})")
    
    # Draw item table positions
    item_start_y = 480
    item_row_height = 20
    item_positions = {
        'sr_no': 40,
        'description': 90,
        'qty': 250,
        'rate': 320,
        'amount': 400,
    }
    
    c.setFillColor(green)
    for i in range(3):  # Show first 3 rows
        y_pos = item_start_y - (i * item_row_height)
        for col_name, x_pos in item_positions.items():
            c.circle(x_pos, y_pos, 3, fill=1)
            if i == 0:  # Only label first row
                c.drawString(x_pos + 5, y_pos, f"{col_name}")
    
    # Add legend
    c.setFillColor(black)
    c.setFont("Helvetica", 12)
    c.drawString(50, A4[1] - 50, "Position Finder Tool")
    c.setFont("Helvetica", 10)
    c.drawString(50, A4[1] - 70, "Blue: Grid (50pt intervals)")
    c.drawString(50, A4[1] - 85, "Red: Current field positions")
    c.drawString(50, A4[1] - 100, "Green: Item table positions")
    
    c.save()
    return overlay_path

def merge_with_template(template_path, overlay_path, output_path):
    """Merge the position finder with the template"""
    
    # Read template PDF
    template_reader = PdfReader(template_path)
    template_page = template_reader.pages[0]
    
    # Read overlay PDF
    overlay_reader = PdfReader(overlay_path)
    overlay_page = overlay_reader.pages[0]
    
    # Merge overlay onto template
    template_page.merge_page(overlay_page)
    
    # Create output PDF
    writer = PdfWriter()
    writer.add_page(template_page)
    
    # Write to output file
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

def create_template_position_guide():
    """Create a position guide overlaid on your template"""
    
    template_path = os.path.join("templates", "invoice_template.pdf")
    output_path = os.path.join("invoices", "position_finder_guide.pdf")
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return
    
    print("🔍 Creating position finder guide...")
    
    # Create position overlay
    overlay_path = create_position_finder()
    
    # Merge with template
    merge_with_template(template_path, overlay_path, output_path)
    
    # Clean up
    if os.path.exists(overlay_path):
        os.unlink(overlay_path)
    
    print(f"✅ Position guide created: {output_path}")
    print("📋 Instructions:")
    print("1. Open the generated PDF")
    print("2. Note the coordinates where you want text to appear")
    print("3. Use those coordinates to update the positioning")
    
    return output_path

if __name__ == "__main__":
    create_template_position_guide()