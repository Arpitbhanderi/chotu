"""
PDF Overlay Invoice Generator
Uses a static PDF template and overlays invoice data directly onto it
"""

import os
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
from reportlab.lib.units import mm
import tempfile


class PDFOverlayInvoiceGenerator:
    """Generate invoices by overlaying data on a PDF template"""
    
    def __init__(self, template_path=None, invoice_dir="invoices"):
        self.template_path = template_path or os.path.join("templates", "invoice_template.pdf")
        self.invoice_dir = invoice_dir
        os.makedirs(self.invoice_dir, exist_ok=True)
        
        # Define text positions (in points from bottom-left corner)
        # Added margins for better spacing from edges
        self.positions = {
            'invoice_number': (362, 500),  # Bill No field (moved 10pt right)
            'invoice_date': (362, 484),    # Date field (moved 10pt right)
            'customer_name': (55, 445),    # Customer name (moved 10pt right)
            'customer_mobile': (340, 433), # Mobile number (moved 10pt right)
            'customer_village': (55, 427), # Village/Address (moved 10pt right)
            'total_amount': (392, 40),     # Total amount (moved 10pt right, 10pt up)
            'paid_amount': (70, 50),      # Paid amount (100pt right of total, 1pt below)
            'remaining_amount': (98, 35),  # Remaining amount (100pt right of total, 39pt below total)
            'next_payment_date': (120, 50), # Next payment date (below customer info)
        }
        
        # Item table positions (starting from first row)
        # Added margins for better column spacing
        self.item_start_y = 368
        self.item_row_height = 22
        self.item_positions = {
            'sr_no': 25,      # Serial number column (moved 10pt right)
            'description': 48, # Description column (moved 10pt right)
            'qty': 290,       # Quantity column (moved 10pt right)
            'rate': 345,      # Rate column (moved 10pt right)
            'amount': 413,    # Amount column (moved 10pt left for right margin)
        }
    
    def generate_invoice_pdf(self, invoice, output_path=None):
        """Generate invoice by overlaying data on template"""
        try:
            if not output_path:
                output_path = os.path.join(self.invoice_dir, f"{invoice.number}_overlay.pdf")
            
            # Always check template exists and is current
            if not os.path.exists(self.template_path):
                raise Exception(f"Template not found: {self.template_path}")
            
            # Log template info for debugging
            template_stat = os.stat(self.template_path)
            print(f"Using template: {self.template_path} (size: {template_stat.st_size} bytes)")
            
            # Create overlay PDF with invoice data
            overlay_path = self._create_data_overlay(invoice)
            
            # Merge overlay with template
            self._merge_pdfs(self.template_path, overlay_path, output_path)
            
            # Clean up temporary file
            if os.path.exists(overlay_path):
                os.unlink(overlay_path)
            
            print(f"PDF overlay invoice generated: {output_path}")
            return True, output_path
            
        except Exception as e:
            print(f"Error generating PDF overlay invoice: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    def _create_data_overlay(self, invoice):
        """Create a transparent PDF with just the invoice data"""
        # Create temporary file for overlay
        overlay_fd, overlay_path = tempfile.mkstemp(suffix='.pdf')
        os.close(overlay_fd)
        
        # Create overlay canvas
        c = canvas.Canvas(overlay_path, pagesize=A4)
        c.setFillColor(black)
        
        # Add invoice number and date
        if invoice.number:
            c.setFont("Helvetica", 8)
            c.drawString(self.positions['invoice_number'][0], 
                        self.positions['invoice_number'][1], 
                        str(invoice.number))
        
        if invoice.invoice_date:
            c.setFont("Helvetica", 8)
            c.drawString(self.positions['invoice_date'][0], 
                        self.positions['invoice_date'][1], 
                        str(invoice.invoice_date))
        
        # Add customer information
        customer = invoice.customer
        if customer:
            c.setFont("Helvetica", 12)
            
            # Customer name
            if customer.name:
                c.drawString(self.positions['customer_name'][0], 
                           self.positions['customer_name'][1], 
                           customer.name)
            
            # Customer mobile
            if customer.phone:
                c.drawString(self.positions['customer_mobile'][0], 
                           self.positions['customer_mobile'][1], 
                           customer.phone)
            
            # Customer village/address
            if customer.address:
                c.drawString(self.positions['customer_village'][0], 
                           self.positions['customer_village'][1], 
                           customer.address)
            
            # Next payment date - only show if payment is not fully paid
            if customer.expected_next_payment_date and invoice.payment_status != 'paid':
                c.setFont("Helvetica", 10)
                c.drawString(self.positions['next_payment_date'][0], 
                           self.positions['next_payment_date'][1], 
                           f"Next Payment: {customer.expected_next_payment_date}")
        
        # Add invoice items
        c.setFont("Helvetica", 10)
        current_row = 0
        
        for i, item in enumerate(invoice.invoice_items[:12]):  # Max 12 items
            base_y_pos = self.item_start_y - (current_row * self.item_row_height)
            
            # Serial number
            c.drawString(self.item_positions['sr_no'], base_y_pos, str(i + 1))
            
            # Product name and description
            if item.product and item.product.name:
                # Product name on first line - increased character limit
                product_name = item.product.name[:40] + "..." if len(item.product.name) > 40 else item.product.name
                c.drawString(self.item_positions['description'], base_y_pos, product_name)
                
                # Product description on second line (if exists) - moved lower
                if item.product.description and item.product.description.strip():
                    desc_y_pos = base_y_pos - 15  # 15 points below the product name (increased from 12)
                    c.setFont("Helvetica", 8)  # Smaller font for description
                    # Increased character limit for description and better text wrapping
                    description = item.product.description[:50] + "..." if len(item.product.description) > 50 else item.product.description
                    c.drawString(self.item_positions['description'], desc_y_pos, description)
                    c.setFont("Helvetica", 10)  # Reset to normal font
                    
                    # If we added description, we need to account for extra space
                    current_row += 1  # Add extra row for description
            
            # Quantity (aligned with product name)
            if item.qty:
                c.drawRightString(self.item_positions['qty'], base_y_pos, str(item.qty))
            
            # Rate (aligned with product name)
            if item.price:
                c.drawRightString(self.item_positions['rate'], base_y_pos, f"{item.price:.2f}")
            
            # Amount (aligned with product name)
            if item.line_total:
                c.drawRightString(self.item_positions['amount'], base_y_pos, f"{item.line_total:.2f}")
            
            current_row += 1  # Move to next row
        
        # Add total amount
        if invoice.total:
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(self.positions['total_amount'][0], 
                              self.positions['total_amount'][1], 
                              f"{invoice.total:.2f}")

        # Add paid and remaining amounts (configurable positions)
        if invoice.total_paid and invoice.total_paid > 0:
            c.setFont("Helvetica", 10)
            c.drawRightString(self.positions['paid_amount'][0], 
                            self.positions['paid_amount'][1], 
                            f"Paid: {invoice.total_paid:.2f}")
            remaining = invoice.total - invoice.total_paid
            c.drawRightString(self.positions['remaining_amount'][0], 
                            self.positions['remaining_amount'][1], 
                            f"Remaining: {remaining:.2f}")
        
        # Save the overlay
        c.save()
        return overlay_path
    
    def _merge_pdfs(self, template_path, overlay_path, output_path):
        """Merge template PDF with overlay PDF"""
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
    
    def update_positions(self, positions_dict):
        """Update text positions for fine-tuning"""
        self.positions.update(positions_dict)
    
    def update_paid_remaining_positions(self, paid_x=None, paid_y=None, remaining_x=None, remaining_y=None):
        """Update paid and remaining amount positions easily"""
        if paid_x is not None or paid_y is not None:
            current_paid = list(self.positions['paid_amount'])
            if paid_x is not None:
                current_paid[0] = paid_x
            if paid_y is not None:
                current_paid[1] = paid_y
            self.positions['paid_amount'] = tuple(current_paid)
            
        if remaining_x is not None or remaining_y is not None:
            current_remaining = list(self.positions['remaining_amount'])
            if remaining_x is not None:
                current_remaining[0] = remaining_x
            if remaining_y is not None:
                current_remaining[1] = remaining_y
            self.positions['remaining_amount'] = tuple(current_remaining)
    
    def update_next_payment_position(self, x=None, y=None):
        """Update next payment date position easily"""
        if x is not None or y is not None:
            current_pos = list(self.positions['next_payment_date'])
            if x is not None:
                current_pos[0] = x
            if y is not None:
                current_pos[1] = y
            self.positions['next_payment_date'] = tuple(current_pos)


# Example usage:
# generator = get_overlay_generator()
# generator.update_paid_remaining_positions(paid_x=400, paid_y=39, remaining_x=400, remaining_y=1)
# generator.generate_invoice_pdf(invoice)

# Global overlay generator instance - recreated each time to avoid caching
def get_overlay_generator():
    """Get a fresh overlay generator instance"""
    return PDFOverlayInvoiceGenerator()


def generate_invoice_pdf_overlay(invoice, pdf_path=None, paid_x=None, paid_y=None, remaining_x=None, remaining_y=None, next_payment_x=None, next_payment_y=None):
    """Generate PDF using overlay method with fresh template loading"""
    generator = get_overlay_generator()  # Always create fresh instance
    
    # Update positions if provided
    if any([paid_x, paid_y, remaining_x, remaining_y]):
        generator.update_paid_remaining_positions(
            paid_x=paid_x, paid_y=paid_y, 
            remaining_x=remaining_x, remaining_y=remaining_y
        )
    
    if next_payment_x is not None or next_payment_y is not None:
        generator.update_next_payment_position(x=next_payment_x, y=next_payment_y)
    
    return generator.generate_invoice_pdf(invoice, pdf_path)