"""Report document generator."""

import os
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from .pdf_generator import PDFGenerator
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

logger = logging.getLogger(__name__)

class ReportGenerator(PDFGenerator):
    """Generator for report documents."""

    def __init__(self, document_base_path: str, document_base_url: str):
        """Initialize the report generator.

        Args:
            document_base_path: Base path for document storage
            document_base_url: Base URL for document access
        """
        super().__init__(document_base_path, document_base_url)
        
        # Add report-specific styles
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=20,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceBefore=12,
            spaceAfter=6,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReportHeading1',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceBefore=12,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReportHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=10,
            spaceAfter=4
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReportHeading3',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=8,
            spaceAfter=4
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReportText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReportFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReportCaption',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique',
            alignment=1  # Center alignment
        ))

    async def generate(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate a report document.

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
        
        # Generate report PDF
        self._generate_report_pdf(document_id, document_data, template, file_path)
        
        # Create preview
        self.create_preview(file_path, document_id)
        
        # Track metrics
        self.track_metrics(file_path, "report", template)
        
        return file_path, file_url, preview_url

    def _generate_report_pdf(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]],
        output_path: str
    ) -> None:
        """Generate a report PDF.

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
        
        # Get report data
        title = document_data.get("title", "Report")
        subtitle = document_data.get("subtitle", "")
        author = document_data.get("author", "")
        date = document_data.get("date", datetime.now().strftime("%B %d, %Y"))
        company_name = document_data.get("company_name", "")
        company_logo = document_data.get("company_logo", "")
        sections = document_data.get("sections", [])
        executive_summary = document_data.get("executive_summary", "")
        conclusion = document_data.get("conclusion", "")
        appendices = document_data.get("appendices", [])
        include_toc = document_data.get("include_toc", True)
        include_cover_page = document_data.get("include_cover_page", True)
        
        # Apply template if provided
        if template:
            if not title and "title" in template:
                title = template["title"]
                
            if not subtitle and "subtitle" in template:
                subtitle = template["subtitle"]
                
            if not author and "author" in template:
                author = template["author"]
                
            if not company_name and "company_name" in template:
                company_name = template["company_name"]
                
            if not company_logo and "company_logo" in template:
                company_logo = template["company_logo"]
                
            if not sections and "sections" in template:
                sections = template["sections"]
                
            if not executive_summary and "executive_summary" in template:
                executive_summary = template["executive_summary"]
                
            if not conclusion and "conclusion" in template:
                conclusion = template["conclusion"]
                
            if not appendices and "appendices" in template:
                appendices = template["appendices"]
        
        # Build document elements
        elements = []
        
        # Add cover page if requested
        if include_cover_page:
            self._add_cover_page(elements, title, subtitle, author, date, company_name, company_logo)
            elements.append(PageBreak())
        
        # Add table of contents if requested
        if include_toc:
            elements.append(Paragraph("Table of Contents", self.styles["ReportHeading1"]))
            elements.append(Spacer(1, 0.25*inch))
            
            # Add placeholder for TOC (would be filled in by a real implementation)
            toc_entries = []
            
            # Add executive summary to TOC if present
            if executive_summary:
                toc_entries.append(["Executive Summary", "3"])
            
            # Add sections to TOC
            page_num = 4 if executive_summary else 3
            for i, section in enumerate(sections):
                section_title = section.get("title", f"Section {i+1}")
                toc_entries.append([section_title, str(page_num)])
                page_num += 1
                
                # Add subsections to TOC if present
                subsections = section.get("subsections", [])
                for j, subsection in enumerate(subsections):
                    subsection_title = subsection.get("title", f"Subsection {i+1}.{j+1}")
                    toc_entries.append([f"    {subsection_title}", str(page_num)])
                    page_num += 1
            
            # Add conclusion to TOC if present
            if conclusion:
                toc_entries.append(["Conclusion", str(page_num)])
                page_num += 1
            
            # Add appendices to TOC if present
            if appendices:
                toc_entries.append(["Appendices", str(page_num)])
                for k, appendix in enumerate(appendices):
                    appendix_title = appendix.get("title", f"Appendix {chr(65+k)}")
                    toc_entries.append([f"    {appendix_title}", str(page_num + k + 1)])
            
            # Create TOC table
            if toc_entries:
                toc_table = Table(toc_entries, colWidths=[5*inch, 0.5*inch])
                toc_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(toc_table)
            
            elements.append(PageBreak())
        
        # Add executive summary if present
        if executive_summary:
            elements.append(Paragraph("Executive Summary", self.styles["ReportHeading1"]))
            elements.append(Spacer(1, 0.1*inch))
            
            # Split executive summary into paragraphs
            paragraphs = executive_summary.split("\n\n")
            for paragraph in paragraphs:
                if paragraph.strip():
                    elements.append(Paragraph(paragraph, self.styles["ReportText"]))
                    elements.append(Spacer(1, 0.1*inch))
            
            elements.append(PageBreak())
        
        # Add sections
        for i, section in enumerate(sections):
            section_title = section.get("title", f"Section {i+1}")
            section_content = section.get("content", "")
            section_image = section.get("image", "")
            section_chart_data = section.get("chart_data", {})
            section_table_data = section.get("table_data", {})
            subsections = section.get("subsections", [])
            
            # Add section title
            elements.append(Paragraph(section_title, self.styles["ReportHeading1"]))
            elements.append(Spacer(1, 0.1*inch))
            
            # Add section content
            if section_content:
                # Split content into paragraphs
                paragraphs = section_content.split("\n\n")
                for paragraph in paragraphs:
                    if paragraph.strip():
                        elements.append(Paragraph(paragraph, self.styles["ReportText"]))
                        elements.append(Spacer(1, 0.1*inch))
            
            # Add section image if present
            if section_image and os.path.exists(section_image):
                elements.append(Image(section_image, width=6*inch, height=3*inch))
                elements.append(Paragraph(f"Figure {i+1}: {section_title}", self.styles["ReportCaption"]))
                elements.append(Spacer(1, 0.2*inch))
            
            # Add chart if data is provided
            if section_chart_data:
                # In a real implementation, this would generate a chart using a library like matplotlib
                # For this example, we'll just add a placeholder
                elements.append(Paragraph("Chart placeholder", self.styles["ReportCaption"]))
                elements.append(Spacer(1, 0.2*inch))
            
            # Add table if data is provided
            if section_table_data:
                table_title = section_table_data.get("title", f"Table {i+1}")
                table_headers = section_table_data.get("headers", [])
                table_rows = section_table_data.get("rows", [])
                
                if table_headers and table_rows:
                    # Create table data with headers
                    table_data = [table_headers]
                    table_data.extend(table_rows)
                    
                    # Calculate column widths
                    col_count = len(table_headers)
                    col_width = 6.5 / col_count
                    
                    # Create table
                    table = Table(table_data, colWidths=[col_width*inch] * col_count)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    
                    elements.append(table)
                    elements.append(Paragraph(table_title, self.styles["ReportCaption"]))
                    elements.append(Spacer(1, 0.2*inch))
            
            # Add subsections
            for j, subsection in enumerate(subsections):
                subsection_title = subsection.get("title", f"Subsection {i+1}.{j+1}")
                subsection_content = subsection.get("content", "")
                
                elements.append(Paragraph(subsection_title, self.styles["ReportHeading2"]))
                elements.append(Spacer(1, 0.1*inch))
                
                if subsection_content:
                    # Split content into paragraphs
                    paragraphs = subsection_content.split("\n\n")
                    for paragraph in paragraphs:
                        if paragraph.strip():
                            elements.append(Paragraph(paragraph, self.styles["ReportText"]))
                            elements.append(Spacer(1, 0.1*inch))
            
            # Add page break after each section except the last one
            if i < len(sections) - 1:
                elements.append(PageBreak())
        
        # Add conclusion if present
        if conclusion:
            elements.append(Paragraph("Conclusion", self.styles["ReportHeading1"]))
            elements.append(Spacer(1, 0.1*inch))
            
            # Split conclusion into paragraphs
            paragraphs = conclusion.split("\n\n")
            for paragraph in paragraphs:
                if paragraph.strip():
                    elements.append(Paragraph(paragraph, self.styles["ReportText"]))
                    elements.append(Spacer(1, 0.1*inch))
            
            elements.append(PageBreak())
        
        # Add appendices if present
        if appendices:
            elements.append(Paragraph("Appendices", self.styles["ReportHeading1"]))
            elements.append(Spacer(1, 0.1*inch))
            
            for k, appendix in enumerate(appendices):
                appendix_title = appendix.get("title", f"Appendix {chr(65+k)}")
                appendix_content = appendix.get("content", "")
                
                elements.append(Paragraph(appendix_title, self.styles["ReportHeading2"]))
                elements.append(Spacer(1, 0.1*inch))
                
                if appendix_content:
                    # Split content into paragraphs
                    paragraphs = appendix_content.split("\n\n")
                    for paragraph in paragraphs:
                        if paragraph.strip():
                            elements.append(Paragraph(paragraph, self.styles["ReportText"]))
                            elements.append(Spacer(1, 0.1*inch))
                
                # Add page break after each appendix except the last one
                if k < len(appendices) - 1:
                    elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)

    def _add_cover_page(
        self,
        elements: List[Any],
        title: str,
        subtitle: str,
        author: str,
        date: str,
        company_name: str,
        company_logo: str
    ) -> None:
        """Add a cover page to the report.

        Args:
            elements: List of document elements
            title: Report title
            subtitle: Report subtitle
            author: Report author
            date: Report date
            company_name: Company name
            company_logo: Path to company logo
        """
        # Add company logo if provided
        if company_logo and os.path.exists(company_logo):
            elements.append(Image(company_logo, width=2*inch, height=1*inch))
            elements.append(Spacer(1, 0.5*inch))
        
        # Add title
        elements.append(Paragraph(title, self.styles["ReportTitle"]))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add subtitle if provided
        if subtitle:
            elements.append(Paragraph(subtitle, self.styles["ReportSubtitle"]))
            elements.append(Spacer(1, 0.5*inch))
        else:
            elements.append(Spacer(1, 0.75*inch))
        
        # Add company name if provided
        if company_name:
            elements.append(Paragraph(company_name, self.styles["ReportHeading2"]))
            elements.append(Spacer(1, 0.5*inch))
        
        # Add author and date
        if author:
            elements.append(Paragraph(f"Prepared by: {author}", self.styles["ReportText"]))
            elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph(f"Date: {date}", self.styles["ReportText"]))
