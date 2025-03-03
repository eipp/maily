"""Invoice document generator."""

import os
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from .pdf_generator import PDFGenerator
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

logger = logging.getLogger(__name__)

class InvoiceGenerator(PDFGenerator):
    """Generator for invoice documents."""

    def __init__(self, document_base_path: str, document_base_url: str):
        """Initialize the invoice generator.

        Args:
            document_base_path: Base path for document storage
            document_base_url: Base URL for document access
        """
        super().__init__(document_base_path, document_base_url)
        
        # Add invoice-specific styles
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=20,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceSubheading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=6,
            spaceAfter=3
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=3
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceTotal',
            parent=self.styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            spaceAfter=3
        ))

    async def generate(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate an invoice document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Define file paths
        file_name = f"{document_id}.pdf"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"
        
        # Generate invoice PDF
        self._generate_invoice_pdf(document_id, document_data, template, file_path)
        
        # Create preview
        self.create_preview(file_path, document_id)
        
        # Track metrics
        self.track_metrics(file_path, "invoice", template)
        
        return file_path, file_url, preview_url

    def _generate_invoice_pdf(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]],
        output_path: str
    ) -> None:
        """Generate an invoice PDF.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data
            output_path: Output file path
        """
        # Ensure directory exists
        self.ensure_directories(os.path.dirname(output_path))
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Get invoice data
        invoice_number = document_data.get("invoice_number", f"INV-{document_id[:8]}")
        invoice_date = document_data.get("invoice_date", datetime.now().strftime("%Y-%m-%d"))
        due_date = document_data.get("due_date", "")
        company_name = document_data.get("company_name", "")
        company_address = document_data.get("company_address", "")
        company_logo = document_data.get("company_logo", "")
        client_name = document_data.get("client_name", "")
        client_address = document_data.get("client_address", "")
        items = document_data.get("items", [])
        subtotal = document_data.get("subtotal", 0.0)
        tax_rate = document_data.get("tax_rate", 0.0)
        tax_amount = document_data.get("tax_amount", 0.0)
        total = document_data.get("total", 0.0)
        currency = document_data.get("currency", "$")
        notes = document_data.get("notes", "")
        payment_terms = document_data.get("payment_terms", "")
        payment_instructions = document_data.get("payment_instructions", "")
        
        # Apply template if provided
        if template:
            if not company_name and "company_name" in template:
                company_name = template["company_name"]
                
            if not company_address and "company_address" in template:
                company_address = template["company_address"]
                
            if not company_logo and "company_logo" in template:
                company_logo = template["company_logo"]
                
            if not payment_terms and "payment_terms" in template:
                payment_terms = template["payment_terms"]
                
            if not payment_instructions and "payment_instructions" in template:
                payment_instructions = template["payment_instructions"]
                
            if not currency and "currency" in template:
                currency = template["currency"]
        
        # Calculate totals if not provided
        if items and not subtotal:
            subtotal = sum(item.get("quantity", 1) * item.get("price", 0) for item in items)
            
        if subtotal and tax_rate and not tax_amount:
            tax_amount = subtotal * (tax_rate / 100)
            
        if subtotal and tax_amount and not total:
            total = subtotal + tax_amount
        
        # Build document elements
        elements = []
        
        # Add header with logo and company info
        header_data = [["", ""]]
        
        # Company logo
        if company_logo and os.path.exists(company_logo):
            img = Image(company_logo, width=1.5*inch, height=0.75*inch)
            header_data[0][0] = img
        else:
            header_data[0][0] = Paragraph(company_name, self.styles["InvoiceTitle"])
        
        # Company info
        company_info = []
        if company_name:
            company_info.append(company_name)
        if company_address:
            company_info.append(company_address)
            
        header_data[0][1] = Paragraph("<br/>".join(company_info), self.styles["InvoiceText"])
        
        header_table = Table(header_data, colWidths=[3*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add invoice title and details
        elements.append(Paragraph("INVOICE", self.styles["InvoiceTitle"]))
        elements.append(Spacer(1, 0.1*inch))
        
        # Invoice details and client info
        invoice_details = [
            ["Invoice Number:", invoice_number, "Client:", client_name],
            ["Invoice Date:", invoice_date, "Client Address:", client_address],
            ["Due Date:", due_date, "", ""]
        ]
        
        details_table = Table(invoice_details, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 2.5*inch])
        details_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(details_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add items table
        if items:
            # Table header
            items_data = [["Item", "Description", "Quantity", "Unit Price", "Amount"]]
            
            # Table rows
            for item in items:
                item_name = item.get("name", "")
                item_description = item.get("description", "")
                item_quantity = item.get("quantity", 1)
                item_price = item.get("price", 0)
                item_amount = item_quantity * item_price
                
                items_data.append([
                    item_name,
                    item_description,
                    str(item_quantity),
                    f"{currency}{item_price:.2f}",
                    f"{currency}{item_amount:.2f}"
                ])
            
            # Table style
            items_table = Table(items_data, colWidths=[1.5*inch, 3*inch, 1*inch, 1*inch, 1*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(items_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Add totals
        totals_data = []
        
        if subtotal:
            totals_data.append(["", "", "", "Subtotal:", f"{currency}{subtotal:.2f}"])
            
        if tax_rate and tax_amount:
            totals_data.append(["", "", "", f"Tax ({tax_rate}%):", f"{currency}{tax_amount:.2f}"])
            
        if total:
            totals_data.append(["", "", "", "Total:", f"{currency}{total:.2f}"])
        
        if totals_data:
            totals_table = Table(totals_data, colWidths=[1.5*inch, 3*inch, 1*inch, 1*inch, 1*inch])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
                ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
                ('FONTNAME', (4, -1), (4, -1), 'Helvetica-Bold'),
                ('LINEABOVE', (3, -1), (4, -1), 1, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(totals_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Add notes and payment terms
        if notes or payment_terms or payment_instructions:
            elements.append(Paragraph("Notes & Payment Terms", self.styles["InvoiceHeading"]))
            
            if notes:
                elements.append(Paragraph(notes, self.styles["InvoiceText"]))
                elements.append(Spacer(1, 0.1*inch))
                
            if payment_terms:
                elements.append(Paragraph(f"Payment Terms: {payment_terms}", self.styles["InvoiceText"]))
                elements.append(Spacer(1, 0.1*inch))
                
            if payment_instructions:
                elements.append(Paragraph("Payment Instructions:", self.styles["InvoiceSubheading"]))
                elements.append(Paragraph(payment_instructions, self.styles["InvoiceText"]))
        
        # Build PDF
        doc.build(elements)
