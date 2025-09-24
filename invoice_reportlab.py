"""
ReportLab-based Invoice PDF Generator
Ensures proper color preservation and layout control
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile


class InvoiceReportLab:
    """ReportLab-based invoice generator with guaranteed color support"""
    
    def __init__(self, invoice_dir="invoices"):
        self.invoice_dir = invoice_dir
        os.makedirs(self.invoice_dir, exist_ok=True)
        
        # Define colors
        self.pink_color = HexColor('#e91e63')
        self.light_pink_color = HexColor('#fce4ec')
        self.gray_color = HexColor('#666666')
        
        # Try to register Gujarati font if available
        try:
            # You might need to download and add a Gujarati font file
            # For now, we'll use default fonts
            pass
        except:
            pass
    
    def generate_invoice_pdf(self, invoice, pdf_path=None):
        """Generate PDF using ReportLab with proper colors"""
        try:
            if not pdf_path:
                pdf_path = os.path.join(self.invoice_dir, f"{invoice.number}_reportlab.pdf")
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=10*mm,
                leftMargin=10*mm,
                topMargin=10*mm,
                bottomMargin=10*mm
            )
            
            # Build content
            story = []
            
            # Header section
            story.append(self._create_header())
            story.append(Spacer(1, 10*mm))
            
            # Services and invoice details section
            story.append(self._create_services_section(invoice))
            story.append(Spacer(1, 5*mm))
            
            # Customer info section
            story.append(self._create_customer_section(invoice))
            story.append(Spacer(1, 5*mm))
            
            # Items table
            story.append(self._create_items_table(invoice))
            story.append(Spacer(1, 10*mm))
            
            # Total section
            story.append(self._create_total_section(invoice))
            story.append(Spacer(1, 10*mm))
            
            # Footer
            story.append(self._create_footer())
            
            # Build PDF
            doc.build(story)
            
            print(f"ReportLab PDF generated successfully: {pdf_path}")
            return True, pdf_path
            
        except Exception as e:
            print(f"Error generating ReportLab PDF: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    def _create_header(self):
        """Create header with pink background"""
        # Header table with pink background
        header_data = [
            ['ઝંકાર વિઝન', 'બસ સ્ટેશનની સામે-વધઈ,\nતા.વધઈ, જી.ડાંગ, પીન.નં.:394 730\nફોન. +91 98792 89565']
        ]
        
        header_table = Table(header_data, colWidths=[100*mm, 80*mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.pink_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), white),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 24),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, 0), 10),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        return header_table
    
    def _create_services_section(self, invoice):
        """Create services and invoice details section"""
        services_text = ("D.T.H. ડીશ, એન્ડ્રોઇડ ટી.વી., મિક્સર મશીન,\n"
                        "વોશિંગ મશીન, પંખા વગેરે ઇલેક્ટ્રીક અને\n"
                        "ઇલેક્ટ્રોનીક્સનું સામાન ટૂટેક તથા હોલસેલમાં મળશે.")
        
        invoice_details = f"બિલ નં.: {invoice.number or ''}\nતારીખ: {invoice.invoice_date or ''}"
        
        services_data = [
            [services_text, invoice_details]
        ]
        
        services_table = Table(services_data, colWidths=[120*mm, 60*mm])
        services_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 12),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, 0), 10),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (1, 0), (1, 0), 1, self.pink_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return services_table
    
    def _create_customer_section(self, invoice):
        """Create customer information section"""
        customer = invoice.customer
        customer_name = customer.name if customer else ''
        customer_mobile = customer.phone if customer else ''
        customer_village = customer.address if customer else ''
        
        customer_data = [
            [f'નામ : {customer_name}', f'મો.નં. {customer_mobile}'],
            [f'ગામ : {customer_village}', '']
        ]
        
        customer_table = Table(customer_data, colWidths=[120*mm, 60*mm])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, -1), 1, self.gray_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return customer_table
    
    def _create_items_table(self, invoice):
        """Create items table with pink headers"""
        # Headers
        headers = ['ક્રમ', 'વિગત', 'નંગ', 'ભાવ', 'રૂ. રકમ પૈ.']
        
        # Build table data
        table_data = [headers]
        
        # Add invoice items
        for i, item in enumerate(invoice.invoice_items, 1):
            product_name = item.product.name if item.product else 'N/A'
            qty = str(item.qty or 0)
            rate = f"{item.price or 0:.2f}"
            amount = f"{item.line_total or 0:.2f}"
            
            table_data.append([str(i), product_name, qty, rate, amount])
        
        # Add empty rows to fill space
        while len(table_data) < 13:  # 12 empty rows + 1 header
            table_data.append(['', '', '', '', ''])
        
        # Create table
        items_table = Table(table_data, colWidths=[15*mm, 85*mm, 20*mm, 30*mm, 30*mm])
        
        # Style the table
        style = [
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), self.pink_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Serial number center
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Description left
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Quantity center
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # Rate right
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),   # Amount right
            
            # All borders
            ('GRID', (0, 0), (-1, -1), 1, self.pink_color),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]
        
        items_table.setStyle(TableStyle(style))
        
        return items_table
    
    def _create_total_section(self, invoice):
        """Create total section with pink border"""
        total_amount = f"{invoice.total or 0:.2f}"
        
        total_data = [
            ['કુલ'],
            [total_amount]
        ]
        
        total_table = Table(total_data, colWidths=[40*mm])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.light_pink_color),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
            ('FONTSIZE', (0, 1), (0, 1), 18),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 2, self.pink_color),
            ('LINEBELOW', (0, 0), (0, 0), 2, self.pink_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        # Create a flowable to position the total on the right
        class RightAlignedTable(Flowable):
            def __init__(self, table):
                self.table = table
                self.width = 40*mm
                self.height = 50*mm
                
            def draw(self):
                # Position table on the right side
                self.table.wrapOn(self.canv, self.width, self.height)
                self.table.drawOn(self.canv, A4[0] - 60*mm, 0)
        
        return RightAlignedTable(total_table)
    
    def _create_footer(self):
        """Create footer section"""
        footer_data = [
            ['GSTIN : 24AIRPB9566H1ZV', 'ઝંકાર વિઝન વતી,']
        ]
        
        footer_table = Table(footer_data, colWidths=[90*mm, 90*mm])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEABOVE', (0, 0), (-1, -1), 2, self.pink_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        return footer_table


# Global ReportLab instance
reportlab_generator = InvoiceReportLab()

def generate_invoice_pdf_reportlab(invoice, pdf_path=None):
    """Generate PDF using ReportLab with guaranteed colors"""
    success, result = reportlab_generator.generate_invoice_pdf(invoice, pdf_path)
    return success, result