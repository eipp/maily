"""Contract document generator."""

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

class ContractGenerator(PDFGenerator):
    """Generator for contract documents."""

    def __init__(self, document_base_path: str, document_base_url: str):
        """Initialize the contract generator.

        Args:
            document_base_path: Base path for document storage
            document_base_url: Base URL for document access
        """
        super().__init__(document_base_path, document_base_url)
        
        # Add contract-specific styles
        self.styles.add(ParagraphStyle(
            name='Heading3',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='ContractClause',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=6,
            spaceAfter=6,
            leftIndent=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='ContractSignature',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=30,
            spaceAfter=0
        ))

    async def generate(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate a contract document.

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
        
        # Generate contract PDF
        self._generate_contract_pdf(document_id, document_data, template, file_path)
        
        # Create preview
        self.create_preview(file_path, document_id)
        
        # Track metrics
        self.track_metrics(file_path, "contract", template)
        
        return file_path, file_url, preview_url

    def _generate_contract_pdf(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]],
        output_path: str
    ) -> None:
        """Generate a contract PDF.

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
            leftMargin=1*inch,
            rightMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        # Get contract data
        title = document_data.get("title", "Contract Agreement")
        parties = document_data.get("parties", [])
        effective_date = document_data.get("effective_date", datetime.now().strftime("%B %d, %Y"))
        clauses = document_data.get("clauses", [])
        signatures = document_data.get("signatures", [])
        
        # Apply template if provided
        if template:
            if not title and "title" in template:
                title = template["title"]
                
            if not parties and "parties" in template:
                parties = template["parties"]
                
            if not effective_date and "effective_date" in template:
                effective_date = template["effective_date"]
                
            if not clauses and "clauses" in template:
                clauses = template["clauses"]
                
            if not signatures and "signatures" in template:
                signatures = template["signatures"]
        
        # Build document elements
        elements = []
        
        # Add title
        elements.append(Paragraph(title, self.styles["Title"]))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add effective date
        elements.append(Paragraph(f"Effective Date: {effective_date}", self.styles["Normal"]))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add parties
        if parties:
            elements.append(Paragraph("BETWEEN:", self.styles["Heading2"]))
            
            for i, party in enumerate(parties):
                party_name = party.get("name", f"Party {i+1}")
                party_details = party.get("details", "")
                
                elements.append(Paragraph(party_name, self.styles["Heading3"]))
                elements.append(Paragraph(party_details, self.styles["Normal"]))
                elements.append(Spacer(1, 0.1*inch))
            
            elements.append(Spacer(1, 0.25*inch))
        
        # Add agreement text
        elements.append(Paragraph("AGREEMENT:", self.styles["Heading2"]))
        elements.append(Paragraph(
            "This Agreement is entered into on the Effective Date by and between the parties listed above. "
            "The parties agree as follows:",
            self.styles["Normal"]
        ))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add clauses
        for i, clause in enumerate(clauses):
            clause_title = clause.get("title", f"Clause {i+1}")
            clause_content = clause.get("content", "")
            
            elements.append(Paragraph(f"{i+1}. {clause_title}", self.styles["Heading3"]))
            
            # Split content into paragraphs
            if isinstance(clause_content, str):
                paragraphs = clause_content.split("\n\n")
                for paragraph in paragraphs:
                    if paragraph.strip():
                        elements.append(Paragraph(paragraph, self.styles["ContractClause"]))
            elif isinstance(clause_content, list):
                for paragraph in clause_content:
                    if paragraph.strip():
                        elements.append(Paragraph(paragraph, self.styles["ContractClause"]))
            
            elements.append(Spacer(1, 0.1*inch))
        
        # Add signatures
        if signatures:
            elements.append(Spacer(1, 0.5*inch))
            elements.append(Paragraph("SIGNATURES:", self.styles["Heading2"]))
            elements.append(Spacer(1, 0.25*inch))
            
            # Create signature table
            signature_data = []
            
            for signature in signatures:
                signature_data.append([
                    Paragraph(f"For: {signature.get('party', '')}", self.styles["Normal"]),
                    Paragraph(f"For: {signature.get('counterparty', '')}", self.styles["Normal"])
                ])
                
                signature_data.append([
                    Paragraph("Signature: _______________________", self.styles["ContractSignature"]),
                    Paragraph("Signature: _______________________", self.styles["ContractSignature"])
                ])
                
                signature_data.append([
                    Paragraph(f"Name: {signature.get('name', '')}", self.styles["Normal"]),
                    Paragraph(f"Name: {signature.get('counterparty_name', '')}", self.styles["Normal"])
                ])
                
                signature_data.append([
                    Paragraph(f"Title: {signature.get('title', '')}", self.styles["Normal"]),
                    Paragraph(f"Title: {signature.get('counterparty_title', '')}", self.styles["Normal"])
                ])
                
                signature_data.append([
                    Paragraph(f"Date: {signature.get('date', '')}", self.styles["Normal"]),
                    Paragraph(f"Date: {signature.get('counterparty_date', '')}", self.styles["Normal"])
                ])
            
            # Create table
            signature_table = Table(signature_data, colWidths=[2.5*inch, 2.5*inch])
            signature_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(signature_table)
        
        # Build PDF
        doc.build(elements)
