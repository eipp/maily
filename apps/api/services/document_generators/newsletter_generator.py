"""Newsletter document generator."""

import os
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import json

from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)

class NewsletterGenerator(BaseGenerator):
    """Generator for HTML newsletter documents."""

    def __init__(self, document_base_path: str, document_base_url: str):
        """Initialize the newsletter generator.

        Args:
            document_base_path: Base path for document storage
            document_base_url: Base URL for document access
        """
        super().__init__(document_base_path, document_base_url)

    async def generate(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """Generate an HTML newsletter document.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            Tuple of (file_path, file_url, preview_url)
        """
        # Define file paths
        file_name = f"{document_id}.html"
        file_path = os.path.join(self.document_base_path, file_name)
        file_url = f"{self.document_base_url}/{file_name}"
        preview_url = f"{self.document_base_url}/previews/{document_id}_preview.png"
        
        # Generate newsletter HTML
        html_content = self._generate_newsletter_html(document_id, document_data, template)
        
        # Ensure directory exists
        self.ensure_directories(os.path.dirname(file_path))
        
        # Save HTML to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Create preview
        self.create_preview(file_path, document_id)
        
        # Track metrics
        self.track_metrics(file_path, "newsletter", template)
        
        return file_path, file_url, preview_url

    def _generate_newsletter_html(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]]
    ) -> str:
        """Generate HTML newsletter content.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            HTML content
        """
        # Get newsletter data
        title = document_data.get("title", "Newsletter")
        subtitle = document_data.get("subtitle", "")
        header_image = document_data.get("header_image", "")
        date = document_data.get("date", datetime.now().strftime("%B %d, %Y"))
        company_name = document_data.get("company_name", "")
        company_logo = document_data.get("company_logo", "")
        sections = document_data.get("sections", [])
        footer_text = document_data.get("footer_text", "")
        unsubscribe_link = document_data.get("unsubscribe_link", "#unsubscribe")
        color_theme = document_data.get("color_theme", {
            "primary": "#4a90e2",
            "secondary": "#f5f5f5",
            "text": "#333333",
            "background": "#ffffff",
            "accent": "#5cb85c"
        })
        
        # Apply template if provided
        if template:
            if not title and "title" in template:
                title = template["title"]
                
            if not subtitle and "subtitle" in template:
                subtitle = template["subtitle"]
                
            if not header_image and "header_image" in template:
                header_image = template["header_image"]
                
            if not company_name and "company_name" in template:
                company_name = template["company_name"]
                
            if not company_logo and "company_logo" in template:
                company_logo = template["company_logo"]
                
            if not sections and "sections" in template:
                sections = template["sections"]
                
            if not footer_text and "footer_text" in template:
                footer_text = template["footer_text"]
                
            if not color_theme and "color_theme" in template:
                color_theme = template["color_theme"]
        
        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        /* Reset styles */
        body, html {{
            margin: 0;
            padding: 0;
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.6;
            color: {color_theme.get("text", "#333333")};
            background-color: #f9f9f9;
        }}
        
        /* Container */
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: {color_theme.get("background", "#ffffff")};
        }}
        
        /* Header */
        .header {{
            padding: 20px;
            text-align: center;
            background-color: {color_theme.get("primary", "#4a90e2")};
            color: white;
        }}
        
        .header img.logo {{
            max-height: 60px;
            margin-bottom: 10px;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 28px;
            color: white;
        }}
        
        .header p {{
            margin: 5px 0 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        
        /* Header Image */
        .header-image {{
            width: 100%;
            max-height: 300px;
            object-fit: cover;
        }}
        
        /* Content */
        .content {{
            padding: 20px;
        }}
        
        /* Section */
        .section {{
            margin-bottom: 30px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }}
        
        .section:last-child {{
            border-bottom: none;
        }}
        
        .section h2 {{
            color: {color_theme.get("primary", "#4a90e2")};
            margin-top: 0;
            font-size: 22px;
        }}
        
        .section img {{
            max-width: 100%;
            height: auto;
            margin: 10px 0;
        }}
        
        .section .cta-button {{
            display: inline-block;
            padding: 10px 20px;
            background-color: {color_theme.get("accent", "#5cb85c")};
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 10px 0;
            font-weight: bold;
        }}
        
        /* Two Column Layout */
        .two-column {{
            display: table;
            width: 100%;
        }}
        
        .column {{
            display: table-cell;
            width: 50%;
            padding: 10px;
            vertical-align: top;
        }}
        
        /* Footer */
        .footer {{
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
            background-color: {color_theme.get("secondary", "#f5f5f5")};
        }}
        
        .footer a {{
            color: {color_theme.get("primary", "#4a90e2")};
            text-decoration: none;
        }}
        
        /* Responsive */
        @media screen and (max-width: 600px) {{
            .two-column .column {{
                display: block;
                width: 100%;
                padding: 0;
                margin-bottom: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            {f'<img src="{company_logo}" alt="{company_name}" class="logo">' if company_logo else ''}
            <h1>{title}</h1>
            {f'<p>{subtitle}</p>' if subtitle else ''}
            <p>{date}</p>
        </div>
        
        {f'<img src="{header_image}" alt="Header" class="header-image">' if header_image else ''}
        
        <!-- Content -->
        <div class="content">
            {self._generate_newsletter_sections(sections)}
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>{footer_text}</p>
            <p>&copy; {datetime.now().year} {company_name}</p>
            <p><a href="{unsubscribe_link}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>"""
        
        return html

    def _generate_newsletter_sections(self, sections: List[Dict[str, Any]]) -> str:
        """Generate HTML for newsletter sections.

        Args:
            sections: List of section definitions

        Returns:
            HTML for newsletter sections
        """
        if not sections:
            # Default section if none provided
            return """
            <div class="section">
                <h2>Welcome to our Newsletter</h2>
                <p>This is a sample newsletter section. You can customize this content with your own.</p>
            </div>
            """
        
        html = ""
        
        for section in sections:
            section_type = section.get("type", "standard")
            section_title = section.get("title", "")
            section_content = section.get("content", "")
            section_image = section.get("image", "")
            section_cta = section.get("cta", {})
            
            html += '<div class="section">\n'
            
            if section_title:
                html += f'    <h2>{section_title}</h2>\n'
            
            if section_type == "standard":
                # Standard section with optional image
                if section_image:
                    html += f'    <img src="{section_image}" alt="{section_title}">\n'
                
                if section_content:
                    html += f'    <div>{section_content}</div>\n'
                
                if section_cta:
                    cta_text = section_cta.get("text", "Learn More")
                    cta_url = section_cta.get("url", "#")
                    html += f'    <a href="{cta_url}" class="cta-button">{cta_text}</a>\n'
            
            elif section_type == "two-column":
                # Two column layout
                left_content = section.get("left_content", "")
                right_content = section.get("right_content", "")
                left_image = section.get("left_image", "")
                right_image = section.get("right_image", "")
                
                html += '    <div class="two-column">\n'
                
                # Left column
                html += '        <div class="column">\n'
                if left_image:
                    html += f'            <img src="{left_image}" alt="Left column image">\n'
                if left_content:
                    html += f'            <div>{left_content}</div>\n'
                html += '        </div>\n'
                
                # Right column
                html += '        <div class="column">\n'
                if right_image:
                    html += f'            <img src="{right_image}" alt="Right column image">\n'
                if right_content:
                    html += f'            <div>{right_content}</div>\n'
                html += '        </div>\n'
                
                html += '    </div>\n'
            
            elif section_type == "featured":
                # Featured section with prominent image and styling
                if section_image:
                    html += f'    <img src="{section_image}" alt="{section_title}" style="width:100%;">\n'
                
                if section_content:
                    html += f'    <div style="padding:15px; background-color:#f9f9f9; border-left:4px solid #4a90e2;">{section_content}</div>\n'
                
                if section_cta:
                    cta_text = section_cta.get("text", "Learn More")
                    cta_url = section_cta.get("url", "#")
                    html += f'    <div style="text-align:center; margin-top:15px;"><a href="{cta_url}" class="cta-button">{cta_text}</a></div>\n'
            
            html += '</div>\n'
        
        return html
