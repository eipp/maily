"""PDF document generator."""

import os
import logging
import io
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import Flowable, PageBreak

from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)

class PDFGenerator(BaseGenerator):
    """Generator for PDF documents."""

    def __init__(self, document_base_path: str, document_base_url: str):
        """Initialize the PDF generator.

        Args:
            document_base_path: Base path for document storage
            document_base_url: Base URL for document access
        """
        super().__init__(document_base_path, document_base_url)
        self.styles = getSampleStyleSheet()
        
        # Add custom styles
        self.styles.add(ParagraphStyle(
            name='Title',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=12,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='Normal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8
        ))

    async def generate(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate a PDF document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Generate PDF content
        pdf_data = self._generate_pdf(document_data, template)
        
        # Define file paths
        file_name = f"{document_id}.pdf"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"
        
        # Ensure directories exist
        self.ensure_directories(os.path.dirname(file_path))
        
        # Save PDF to file
        with open(file_path, "wb") as f:
            f.write(pdf_data)
        
        # Create preview
        self.create_preview(file_path, document_id)
        
        # Track metrics
        self.track_metrics(file_path, "pdf", template)
        
        return file_path, file_url, preview_url

    def _generate_pdf(
        self,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate PDF content.

        Args:
            document_data: Document data
            template: Optional template data

        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()
        
        # Get page size from template or use default
        page_size = letter
        if template and "page_size" in template:
            page_size_name = template["page_size"]
            if page_size_name == "a4":
                from reportlab.lib.pagesizes import A4
                page_size = A4
            elif page_size_name == "legal":
                from reportlab.lib.pagesizes import LEGAL
                page_size = LEGAL
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Get document content
        title = document_data.get("title", "")
        subtitle = document_data.get("subtitle", "")
        content = document_data.get("content", "")
        sections = document_data.get("sections", [])
        
        # Apply template if provided
        if template:
            if not title and "title" in template:
                title = template["title"]
                
            if not subtitle and "subtitle" in template:
                subtitle = template["subtitle"]
                
            if not content and "content" in template:
                content = template["content"]
                
            if not sections and "sections" in template:
                sections = template["sections"]
        
        # Build document elements
        elements = []
        
        # Add title if provided
        if title:
            elements.append(Paragraph(title, self.styles["Title"]))
            
        # Add subtitle if provided
        if subtitle:
            elements.append(Paragraph(subtitle, self.styles["Subtitle"]))
            
        # Add spacer after title/subtitle
        if title or subtitle:
            elements.append(Spacer(1, 0.25*inch))
        
        # Add content if provided
        if content:
            # Split content into paragraphs
            paragraphs = content.split("\n\n")
            for paragraph in paragraphs:
                if paragraph.strip():
                    elements.append(Paragraph(paragraph, self.styles["Normal"]))
        
        # Add sections if provided
        for section in sections:
            # Add section heading
            if "heading" in section:
                elements.append(Paragraph(section["heading"], self.styles["SectionHeading"]))
            
            # Add section content
            if "content" in section:
                if isinstance(section["content"], str):
                    # Split content into paragraphs
                    paragraphs = section["content"].split("\n\n")
                    for paragraph in paragraphs:
                        if paragraph.strip():
                            elements.append(Paragraph(paragraph, self.styles["Normal"]))
                elif isinstance(section["content"], list):
                    # Handle list of paragraphs
                    for paragraph in section["content"]:
                        if paragraph.strip():
                            elements.append(Paragraph(paragraph, self.styles["Normal"]))
            
            # Add section table if provided
            if "table" in section:
                table_data = section["table"]
                if table_data and isinstance(table_data, list):
                    table = Table(table_data)
                    
                    # Add basic table styling
                    table_style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ])
                    table.setStyle(table_style)
                    elements.append(table)
                    elements.append(Spacer(1, 0.1*inch))
            
            # Add section image if provided
            if "image" in section:
                image_path = section["image"]
                if os.path.exists(image_path):
                    img = Image(image_path, width=6*inch, height=4*inch)
                    elements.append(img)
                    elements.append(Spacer(1, 0.1*inch))
            
            # Add page break if requested
            if section.get("page_break", False):
                elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
