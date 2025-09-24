"""
Invoice Printer Module - Updated to match provided format
Handles all PDF generation and printing functionality
"""

import os
import re
import tempfile
import subprocess
import platform
import pdfkit
from datetime import datetime

# Updated Bill HTML Template to match the provided format
BILL_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="gu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ઝેંકાર વિજન - Invoice</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati:wght@400;700&display=swap');
        
        @font-face {
            font-family: 'Noto Sans Gujarati Fallback';
            src: local('Noto Sans Gujarati'), local('Arial Unicode MS'), local('Arial');
            font-weight: 400;
            font-style: normal;
        }
        
        @font-face {
            font-family: 'Noto Sans Gujarati Fallback';
            src: local('Noto Sans Gujarati'), local('Arial Unicode MS'), local('Arial');
            font-weight: 700;
            font-style: normal;
        }
        
        * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        
        body {
            font-family: 'Noto Sans Gujarati', 'Noto Sans Gujarati Fallback', 'Arial Unicode MS', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: white;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        
        .invoice-container {
            background-color: white;
            border: 2px solid #e91e63;
            width: 210mm;
            min-height: 297mm;
            margin: 0 auto;
            padding: 0;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: #e91e63 !important;
            color: white !important;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #e91e63;
        }
        
        .company-name {
            font-size: 32px !important;
            font-weight: bold !important;
            color: white !important;
        }
        
        .contact-info {
            text-align: right;
            font-size: 12px;
            line-height: 1.4;
            color: white !important;
            margin-top: 5px;
        }
        
        .services-section {
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
        }
        
        .services-text {
            flex: 1;
            font-size: 14px;
            line-height: 1.5;
            color: #333;
        }
        
        .invoice-details {
            border: 1px solid #e91e63;
            padding: 10px;
            min-width: 150px;
        }
        
        .detail-row {
            display: flex;
            margin-bottom: 8px;
            align-items: center;
        }
        
        .detail-label {
            font-weight: bold;
            margin-right: 10px;
            white-space: nowrap;
            min-width: 50px;
        }
        
        .detail-value {
            border-bottom: 1px dotted #666;
            flex: 1;
            min-height: 20px;
            padding: 2px 5px;
        }
        
        .customer-info {
            padding: 15px 20px;
            border-top: 1px solid #e91e63;
        }
        
        .customer-row {
            display: flex;
            margin-bottom: 10px;
            align-items: center;
        }
        
        .customer-label {
            font-weight: bold;
            min-width: 60px;
            margin-right: 10px;
        }
        
        .customer-value {
            flex: 1;
            border-bottom: 1px dotted #666;
            min-height: 25px;
            padding: 2px 5px;
            margin-right: 20px;
        }
        
        .mobile-section {
            display: flex;
            align-items: center;
            min-width: 200px;
        }
        
        .mobile-label {
            font-weight: bold;
            margin-right: 10px;
            white-space: nowrap;
        }
        
        .mobile-value {
            border-bottom: 1px dotted #666;
            flex: 1;
            min-height: 25px;
            padding: 2px 5px;
        }
        
        .table-section {
            flex: 1;
            margin: 0 20px;
            min-height: 400px;
        }
        
        .invoice-table {
            width: 100%;
            border-collapse: collapse;
            border: 2px solid #e91e63;
        }
        
        .invoice-table th {
            background: #e91e63 !important;
            color: white !important;
            padding: 12px 8px;
            text-align: center;
            border: 1px solid #e91e63;
            font-weight: bold;
            font-size: 14px;
        }
        
        .invoice-table td {
            padding: 10px 8px;
            border: 1px solid #e91e63;
            vertical-align: top;
            min-height: 30px;
        }
        
        .sr-col { width: 8%; text-align: center; }
        .description-col { width: 50%; }
        .qty-col { width: 12%; text-align: center; }
        .rate-col { width: 15%; text-align: right; }
        .amount-col { width: 15%; text-align: right; }
        
        .invoice-table tbody tr:nth-child(even) {
            background-color: #fafafa;
        }
        
        .total-section {
            margin: 20px;
            display: flex;
            justify-content: flex-end;
        }
        
        .total-box {
            border: 2px solid #e91e63;
            background: #fce4ec;
            padding: 15px 20px;
            min-width: 200px;
            text-align: center;
        }
        
        .total-label {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .total-amount {
            font-size: 24px;
            font-weight: bold;
            border-bottom: 2px solid #e91e63;
            padding-bottom: 10px;
        }
        
        .payment-info {
            margin-top: 10px;
            font-size: 12px;
            text-align: center;
        }
        
        .payment-status {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .payment-details {
            font-size: 11px;
            color: #666;
        }
        
        .footer {
            padding: 15px 20px;
            border-top: 2px solid #e91e63;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: auto;
        }
        
        .gstin {
            font-weight: bold;
            font-size: 14px;
        }
        
        .signature {
            font-weight: bold;
            font-size: 14px;
        }
        
        @media print {
            * {
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
                -webkit-box-sizing: border-box;
                box-sizing: border-box;
            }
            
            body {
                margin: 0;
                padding: 0;
                background-color: white !important;
                font-family: 'Noto Sans Gujarati', 'Noto Sans Gujarati Fallback', 'Arial Unicode MS', Arial, sans-serif !important;
                font-size: 12px !important;
                line-height: 1.4 !important;
                color: black !important;
            }
            
            @page {
                size: A4 portrait;
                margin: 10mm;
            }
            
            .invoice-container {
                border: 2px solid #e91e63 !important;
                box-shadow: none !important;
                width: 100% !important;
                min-height: auto !important;
                max-width: none !important;
                margin: 0 !important;
                padding: 0 !important;
                background-color: white !important;
                page-break-inside: avoid;
            }
            
            .header {
                background: #e91e63 !important;
                color: white !important;
                border-bottom: 2px solid #e91e63 !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
                break-inside: avoid;
            }
            
            .company-name {
                color: white !important;
                font-weight: bold !important;
                font-size: 32px !important;
            }
            
            .contact-info {
                color: white !important;
            }
            
            .services-section {
                background-color: white !important;
                border-bottom: 1px solid #000 !important;
                break-inside: avoid;
            }
            
            .services-text {
                color: #333 !important;
                font-size: 14px !important;
                line-height: 1.5 !important;
            }
            
            .invoice-details {
                border: 1px solid #e91e63 !important;
                background-color: white !important;
            }
            
            .detail-label {
                font-weight: bold !important;
                color: #000 !important;
            }
            
            .detail-value {
                border-bottom: 1px dotted #666 !important;
                color: #000 !important;
            }
            
            .customer-info {
                border-top: 1px solid #e91e63 !important;
                border-bottom: 1px solid #e91e63 !important;
                break-inside: avoid;
            }
            
            .customer-label {
                font-weight: bold !important;
                color: #000 !important;
            }
            
            .customer-value {
                border-bottom: 1px dotted #666 !important;
                color: #000 !important;
            }
            
            .mobile-value {
                border-bottom: 1px dotted #666 !important;
                color: #000 !important;
            }
            
            .table-section {
                break-inside: avoid;
            }
            
            .invoice-table {
                border-collapse: collapse !important;
                border: 2px solid #e91e63 !important;
                width: 100% !important;
                margin: 0 !important;
                font-size: 12px !important;
            }
            
            .invoice-table th {
                background: #e91e63 !important;
                color: white !important;
                border: 1px solid #e91e63 !important;
                padding: 8px !important;
                font-weight: bold !important;
                font-size: 14px !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            
            .invoice-table td {
                border: 1px solid #e91e63 !important;
                padding: 8px !important;
                color: #000 !important;
                vertical-align: top !important;
            }
            
            .invoice-table tbody tr:nth-child(even) {
                background-color: #f5f5f5 !important;
            }
            
            .total-section {
                break-inside: avoid;
                page-break-inside: avoid;
            }
            
            .total-box {
                border: 2px solid #e91e63 !important;
                background: #fce4ec !important;
                color: #000 !important;
            }
            
            .total-label {
                font-size: 18px !important;
                font-weight: bold !important;
                color: #000 !important;
            }
            
            .total-amount {
                font-size: 24px !important;
                font-weight: bold !important;
                border-bottom: 2px solid #e91e63 !important;
                color: #000 !important;
            }
            
            .payment-info {
                margin-top: 10px !important;
                font-size: 12px !important;
                text-align: center !important;
            }
            
            .payment-status {
                font-weight: bold !important;
                margin-bottom: 5px !important;
                color: #000 !important;
            }
            
            .payment-details {
                font-size: 11px !important;
                color: #666 !important;
            }
            
            .footer {
                border-top: 2px solid #e91e63 !important;
                break-inside: avoid;
                page-break-inside: avoid;
            }
            
            .gstin, .signature {
                font-weight: bold !important;
                color: #000 !important;
                font-size: 14px !important;
            }
            
            /* Ensure all text is visible */
            * {
                text-rendering: optimizeLegibility !important;
                -webkit-font-smoothing: antialiased !important;
            }
            
            /* Hide any screen-only elements */
            .no-print {
                display: none !important;
            }
        }
    </style>
</head>
<body>
    <div class="invoice-container">
        <div class="header">
            <div class="company-name">ઝેંકાર વિજન</div>
            <div class="contact-info">
                બસ સ્ટેશનની સામે-વધઈ,<br>
                તા.વધઈ, જી.ડાંગ, પીન.નં.:394 730<br>
                ફોન. +91 98792 89565
            </div>
        </div>
        
        <div class="services-section">
            <div class="services-text">
                <strong>D.T.H. ડીશ, એન્ડ્રોઇડ ટી.વી., મિક્સર મશીન,<br>
                વોશિંગ મશીન, પંખા વગેરે ઇલેક્ટ્રીક અને<br>
                ઇલેક્ટ્રોનીક્સનું સામાન ટૂટેક તથા હોલસેલમાં મળશે.</strong>
            </div>
            <div class="invoice-details">
                <div class="detail-row">
                    <span class="detail-label">બિલ નં.:</span>
                    <span class="detail-value">{{INVOICE_NUMBER}}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">તારીખ:</span>
                    <span class="detail-value">{{INVOICE_DATE}}</span>
                </div>
            </div>
        </div>
        
        <div class="customer-info">
            <div class="customer-row">
                <span class="customer-label">નામ :</span>
                <span class="customer-value">{{CUSTOMER_NAME}}</span>
                <div class="mobile-section">
                    <span class="mobile-label">મો.નં.</span>
                    <span class="mobile-value">{{CUSTOMER_MOBILE}}</span>
                </div>
            </div>
            <div class="customer-row">
                <span class="customer-label">ગામ :</span>
                <span class="customer-value">{{CUSTOMER_VILLAGE}}</span>
                <div class="mobile-section">
                    <span class="mobile-label"></span>
                    <span class="mobile-value"></span>
                </div>
            </div>
        </div>
        
        <div class="table-section">
            <table class="invoice-table">
                <thead>
                    <tr>
                        <th class="sr-col">ક્રમ</th>
                        <th class="description-col">વિગત</th>
                        <th class="qty-col">નંગ</th>
                        <th class="rate-col">ભાવ</th>
                        <th class="amount-col">રૂ. રકમ પૈ.</th>
                    </tr>
                </thead>
                <tbody>
                    {{TABLE_ROWS}}
                </tbody>
            </table>
        </div>
        
        <div class="total-section">
            <div class="total-box">
                <div class="total-label">કુલ</div>
                <div class="total-amount">{{TOTAL_AMOUNT}}</div>
                {% if PAYMENT_STATUS %}
                <div class="payment-info">
                    <div class="payment-status">{{PAYMENT_STATUS}}</div>
                    {% if TOTAL_PAID %}
                    <div class="payment-details">ચૂકવેલ: ₹{{TOTAL_PAID}} | બાકી: ₹{{REMAINING_BALANCE}}</div>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>
        
        <div class="footer">
            <div class="gstin">GSTIN : 24AIRPB9566H1ZV</div>
            <div class="signature">ઝેંકાર વિજન વતી,</div>
        </div>
    </div>
</body>
</html>"""


class InvoicePrinter:
    """Handles invoice PDF generation and printing"""
    
    def __init__(self, invoice_dir="invoices"):
        self.invoice_dir = invoice_dir
        os.makedirs(self.invoice_dir, exist_ok=True)
    
    def generate_invoice_html(self, invoice):
        """Generate HTML content with invoice data"""
        try:
            # Get invoice data
            customer = invoice.customer
            invoice_number = invoice.number or ''
            invoice_date = invoice.invoice_date or ''
            customer_name = customer.name if customer else ''
            customer_village = customer.address if customer else ''
            customer_mobile = customer.phone if customer else ''
            total_amount = f"{invoice.total or 0:.2f}"
            
            # Payment information
            payment_status = ''
            total_paid = ''
            remaining_balance = ''
            
            if hasattr(invoice, 'payment_status') and invoice.payment_status:
                if invoice.payment_status == 'paid':
                    payment_status = 'પૂરેપૂરું ચૂકવેલ'
                elif invoice.payment_status == 'partial':
                    payment_status = 'આંશિક ચૂકવેલ'
                else:
                    payment_status = 'બાકી'
                
                if hasattr(invoice, 'total_paid') and invoice.total_paid:
                    total_paid = f"{invoice.total_paid:.2f}"
                    remaining_balance = f"{(invoice.total - invoice.total_paid):.2f}"
            
            # Start with template
            html_content = BILL_HTML_TEMPLATE
            
            # Replace placeholders
            html_content = html_content.replace('{{INVOICE_NUMBER}}', invoice_number)
            html_content = html_content.replace('{{INVOICE_DATE}}', invoice_date)
            html_content = html_content.replace('{{CUSTOMER_NAME}}', customer_name)
            html_content = html_content.replace('{{CUSTOMER_VILLAGE}}', customer_village)
            html_content = html_content.replace('{{CUSTOMER_MOBILE}}', customer_mobile)
            html_content = html_content.replace('{{TOTAL_AMOUNT}}', total_amount)
            html_content = html_content.replace('{{PAYMENT_STATUS}}', payment_status)
            html_content = html_content.replace('{{TOTAL_PAID}}', total_paid)
            html_content = html_content.replace('{{REMAINING_BALANCE}}', remaining_balance)
            
            # Build table rows
            table_rows = []
            
            # Add invoice items
            for i, item in enumerate(invoice.invoice_items, 1):
                product_name = item.product.name if item.product else 'N/A'
                qty = item.qty or 0
                rate = f"{item.price or 0:.2f}"
                amount = f"{item.line_total or 0:.2f}"
                
                table_rows.append(
                    f'                    <tr>'
                    f'<td class="sr-col">{i}</td>'
                    f'<td class="description-col">{product_name}</td>'
                    f'<td class="qty-col">{qty}</td>'
                    f'<td class="rate-col">{rate}</td>'
                    f'<td class="amount-col">{amount}</td>'
                    f'</tr>'
                )
            
            # Add empty rows to fill space (minimum 12 rows for better layout)
            while len(table_rows) < 12:
                table_rows.append('                    <tr style="height: 32px;"><td class="sr-col"></td><td class="description-col"></td><td class="qty-col"></td><td class="rate-col"></td><td class="amount-col"></td></tr>')
            
            # Replace table rows placeholder
            html_content = html_content.replace('{{TABLE_ROWS}}', '\n'.join(table_rows))
            
            return html_content
            
        except Exception as e:
            print(f"Error generating HTML: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_pdf(self, invoice, pdf_path=None):
        """Generate PDF from invoice"""
        try:
            if not pdf_path:
                pdf_path = os.path.join(self.invoice_dir, f"{invoice.number}.pdf")
            
            html_content = self.generate_invoice_html(invoice)
            
            if not html_content:
                raise Exception("Failed to generate HTML content")
            
            # PDF options optimized for A4
            options = {
                'page-size': 'A4',
                'orientation': 'Portrait',
                'margin-top': '5mm',
                'margin-right': '5mm',
                'margin-bottom': '5mm',
                'margin-left': '5mm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,
                'print-media-type': None,
                'disable-smart-shrinking': None,
                'zoom': '1.0',
                'dpi': 300,
                'image-quality': 94,
                'javascript-delay': 500,
            }
            
            # Try to find wkhtmltopdf
            config = self._get_wkhtmltopdf_config()
            
            # Generate PDF using temporary file method for better compatibility
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
                temp_html.write(html_content)
                temp_html_path = temp_html.name
            
            try:
                if config:
                    pdfkit.from_file(temp_html_path, pdf_path, options=options, configuration=config)
                else:
                    pdfkit.from_file(temp_html_path, pdf_path, options=options)
            finally:
                # Clean up temp file
                if os.path.exists(temp_html_path):
                    os.unlink(temp_html_path)
            
            print(f"PDF generated successfully: {pdf_path}")
            return True, pdf_path
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    def _get_wkhtmltopdf_config(self):
        """Find wkhtmltopdf executable"""
        possible_paths = [
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\wkhtmltopdf\bin\wkhtmltopdf.exe',
            '/usr/local/bin/wkhtmltopdf',
            '/usr/bin/wkhtmltopdf',
            '/opt/homebrew/bin/wkhtmltopdf'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return pdfkit.configuration(wkhtmltopdf=path)
        
        return None
    
    def print_invoice(self, invoice_number, printer_name=None):
        """Print invoice by number"""
        pdf_path = os.path.join(self.invoice_dir, f"{invoice_number}.pdf")
        
        if not os.path.exists(pdf_path):
            return {"success": False, "message": f"PDF not found for invoice {invoice_number}. Please generate PDF first.", "need_pdf": True}
        
        system = platform.system().lower()
        
        if system == "windows":
            return self._print_windows(pdf_path, printer_name, invoice_number)
        elif system == "linux":
            return self._print_linux(pdf_path, printer_name, invoice_number)
        elif system == "darwin":
            return self._print_macos(pdf_path, printer_name, invoice_number)
        else:
            return {"success": False, "message": f"Unsupported operating system: {system}"}
    
    def _print_windows(self, pdf_path, printer_name, invoice_number):
        """Print on Windows"""
        try:
            if printer_name:
                # Use specific printer
                cmd = f'powershell "Start-Process -FilePath \\"{pdf_path}\\" -Verb Print -ArgumentList \\"{printer_name}\\""'
                subprocess.run(cmd, shell=True, check=True)
            else:
                # Use default printer
                os.startfile(pdf_path, "print")
            
            return {"success": True, "message": f"Invoice {invoice_number} sent to printer"}
        except Exception as e:
            # Fallback: just open the PDF
            try:
                os.startfile(pdf_path)
                return {"success": True, "message": f"Invoice {invoice_number} opened for printing (please print manually)"}
            except Exception:
                return {"success": False, "message": f"Windows print failed: {str(e)}"}
    
    def _print_linux(self, pdf_path, printer_name, invoice_number):
        """Print on Linux using lp command"""
        try:
            if printer_name:
                cmd = ["lp", "-d", printer_name, pdf_path]
            else:
                cmd = ["lp", pdf_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return {"success": True, "message": f"Invoice {invoice_number} sent to printer"}
        except subprocess.CalledProcessError as e:
            # Fallback: open with default viewer
            try:
                subprocess.run(["xdg-open", pdf_path], check=True)
                return {"success": True, "message": f"Invoice {invoice_number} opened for printing"}
            except Exception:
                return {"success": False, "message": f"Linux print failed: {e.stderr if e.stderr else str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Linux print error: {str(e)}"}
    
    def _print_macos(self, pdf_path, printer_name, invoice_number):
        """Print on macOS using lpr command"""
        try:
            if printer_name:
                cmd = ["lpr", "-P", printer_name, pdf_path]
            else:
                cmd = ["lpr", pdf_path]
            
            subprocess.run(cmd, check=True)
            return {"success": True, "message": f"Invoice {invoice_number} sent to printer"}
        except subprocess.CalledProcessError as e:
            # Fallback: open with default viewer
            try:
                subprocess.run(["open", pdf_path], check=True)
                return {"success": True, "message": f"Invoice {invoice_number} opened for printing"}
            except Exception:
                return {"success": False, "message": f"macOS print failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"macOS print error: {str(e)}"}
    
    def get_available_printers(self):
        """Get list of available printers"""
        try:
            system = platform.system().lower()
            
            if system == "windows":
                cmd = 'powershell "Get-Printer | Select-Object Name | Format-Table -HideTableHeaders"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                    printers = [line for line in lines if line and not line.startswith('---')]
                    return {"success": True, "printers": printers}
            elif system in ["linux", "darwin"]:
                result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    printers = []
                    for line in lines:
                        if line.startswith('printer '):
                            printer_name = line.split(' ')[1]
                            printers.append(printer_name)
                    return {"success": True, "printers": printers}
            
            return {"success": False, "message": "Could not retrieve printer list"}
        except Exception as e:
            return {"success": False, "message": f"Error getting printers: {str(e)}"}


# Global printer instance
printer = InvoicePrinter()

# Convenience functions for backward compatibility
def generate_invoice_pdf(invoice, pdf_path):
    """Generate PDF for an invoice using PDF overlay method"""
    try:
        from invoice_overlay import generate_invoice_pdf_overlay
        success, result = generate_invoice_pdf_overlay(invoice, pdf_path)
        return success
    except ImportError as e:
        print(f"Overlay method failed, falling back to ReportLab: {e}")
        try:
            from invoice_reportlab import generate_invoice_pdf_reportlab
            success, result = generate_invoice_pdf_reportlab(invoice, pdf_path)
            return success
        except ImportError:
            # Final fallback to original method
            success, result = printer.generate_pdf(invoice, pdf_path)
            return success

def generate_invoice_pdf_with_colors(invoice, pdf_path=None):
    """Generate PDF using ReportLab with guaranteed color preservation"""
    try:
        from invoice_reportlab import generate_invoice_pdf_reportlab
        return generate_invoice_pdf_reportlab(invoice, pdf_path)
    except ImportError:
        # Fallback to original method
        return printer.generate_pdf(invoice, pdf_path)

def print_invoice_directly(invoice_number, printer_name=None):
    """Print invoice directly"""
    return printer.print_invoice(invoice_number, printer_name)

def get_available_printers():
    """Get available printers"""
    return printer.get_available_printers()