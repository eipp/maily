"""Form document generator."""

import os
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import json

from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)

class FormGenerator(BaseGenerator):
    """Generator for HTML form documents."""

    def __init__(self, document_base_path: str, document_base_url: str):
        """Initialize the form generator.

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
        """Generate an HTML form document.

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
        
        # Generate form HTML
        html_content = self._generate_form_html(document_id, document_data, template)
        
        # Ensure directory exists
        self.ensure_directories(os.path.dirname(file_path))
        
        # Save HTML to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Create preview
        self.create_preview(file_path, document_id)
        
        # Track metrics
        self.track_metrics(file_path, "form", template)
        
        return file_path, file_url, preview_url

    def _generate_form_html(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        template: Optional[Dict[str, Any]]
    ) -> str:
        """Generate HTML form content.

        Args:
            document_id: Document ID
            document_data: Document data
            template: Optional template data

        Returns:
            HTML content
        """
        # Get form data
        title = document_data.get("title", "Form")
        description = document_data.get("description", "")
        fields = document_data.get("fields", [])
        submit_url = document_data.get("submit_url", "#")
        submit_text = document_data.get("submit_text", "Submit")
        success_message = document_data.get("success_message", "Form submitted successfully!")
        css_theme = document_data.get("css_theme", "default")
        
        # Apply template if provided
        if template:
            if not title and "title" in template:
                title = template["title"]
                
            if not description and "description" in template:
                description = template["description"]
                
            if not fields and "fields" in template:
                fields = template["fields"]
                
            if not submit_url and "submit_url" in template:
                submit_url = template["submit_url"]
                
            if not submit_text and "submit_text" in template:
                submit_text = template["submit_text"]
                
            if not success_message and "success_message" in template:
                success_message = template["success_message"]
                
            if not css_theme and "css_theme" in template:
                css_theme = template["css_theme"]
        
        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {self._get_css_theme(css_theme)}
    </style>
</head>
<body>
    <div class="form-container">
        <h1>{title}</h1>
        <p class="form-description">{description}</p>
        
        <form id="dynamic-form" action="{submit_url}" method="POST">
            <input type="hidden" name="form_id" value="{document_id}">
            
            {self._generate_form_fields(fields)}
            
            <div class="form-group form-buttons">
                <button type="submit" class="submit-button">{submit_text}</button>
                <button type="reset" class="reset-button">Reset</button>
            </div>
        </form>
        
        <div id="success-message" class="success-message" style="display: none;">
            {success_message}
        </div>
    </div>
    
    <script>
        {self._get_form_javascript(document_id)}
    </script>
</body>
</html>"""
        
        return html

    def _generate_form_fields(self, fields: List[Dict[str, Any]]) -> str:
        """Generate HTML for form fields.

        Args:
            fields: List of field definitions

        Returns:
            HTML for form fields
        """
        html = ""
        
        for field in fields:
            field_type = field.get("type", "text")
            field_id = field.get("id", f"field_{len(html)}")
            field_name = field.get("name", field_id)
            field_label = field.get("label", field_name.capitalize())
            field_placeholder = field.get("placeholder", "")
            field_required = field.get("required", False)
            field_options = field.get("options", [])
            field_value = field.get("default_value", "")
            field_help = field.get("help_text", "")
            field_validation = field.get("validation", {})
            
            required_attr = 'required="required"' if field_required else ""
            
            html += f'<div class="form-group">\n'
            html += f'    <label for="{field_id}">{field_label}</label>\n'
            
            if field_type == "text" or field_type == "email" or field_type == "password" or field_type == "number" or field_type == "date":
                html += f'    <input type="{field_type}" id="{field_id}" name="{field_name}" placeholder="{field_placeholder}" value="{field_value}" {required_attr}>\n'
            
            elif field_type == "textarea":
                html += f'    <textarea id="{field_id}" name="{field_name}" placeholder="{field_placeholder}" {required_attr}>{field_value}</textarea>\n'
            
            elif field_type == "select":
                html += f'    <select id="{field_id}" name="{field_name}" {required_attr}>\n'
                
                if field_placeholder:
                    html += f'        <option value="" disabled {" selected" if not field_value else ""}>{field_placeholder}</option>\n'
                
                for option in field_options:
                    option_value = option.get("value", "")
                    option_label = option.get("label", option_value)
                    selected = " selected" if option_value == field_value else ""
                    
                    html += f'        <option value="{option_value}"{selected}>{option_label}</option>\n'
                
                html += '    </select>\n'
            
            elif field_type == "radio":
                for option in field_options:
                    option_value = option.get("value", "")
                    option_label = option.get("label", option_value)
                    option_id = f"{field_id}_{option_value}"
                    checked = " checked" if option_value == field_value else ""
                    
                    html += f'    <div class="radio-option">\n'
                    html += f'        <input type="radio" id="{option_id}" name="{field_name}" value="{option_value}"{checked} {required_attr}>\n'
                    html += f'        <label for="{option_id}" class="radio-label">{option_label}</label>\n'
                    html += f'    </div>\n'
            
            elif field_type == "checkbox":
                if field_options:
                    # Multiple checkboxes
                    for option in field_options:
                        option_value = option.get("value", "")
                        option_label = option.get("label", option_value)
                        option_id = f"{field_id}_{option_value}"
                        checked = " checked" if option_value in field_value else ""
                        
                        html += f'    <div class="checkbox-option">\n'
                        html += f'        <input type="checkbox" id="{option_id}" name="{field_name}[]" value="{option_value}"{checked}>\n'
                        html += f'        <label for="{option_id}" class="checkbox-label">{option_label}</label>\n'
                        html += f'    </div>\n'
                else:
                    # Single checkbox
                    checked = " checked" if field_value else ""
                    html += f'    <div class="checkbox-option">\n'
                    html += f'        <input type="checkbox" id="{field_id}" name="{field_name}" value="1"{checked} {required_attr}>\n'
                    html += f'        <label for="{field_id}" class="checkbox-label">{field_label}</label>\n'
                    html += f'    </div>\n'
            
            elif field_type == "file":
                accept = field.get("accept", "")
                accept_attr = f' accept="{accept}"' if accept else ""
                multiple = field.get("multiple", False)
                multiple_attr = ' multiple="multiple"' if multiple else ""
                
                html += f'    <input type="file" id="{field_id}" name="{field_name}" {accept_attr}{multiple_attr} {required_attr}>\n'
            
            # Add help text if provided
            if field_help:
                html += f'    <p class="help-text">{field_help}</p>\n'
            
            html += '</div>\n'
        
        return html

    def _get_css_theme(self, theme: str) -> str:
        """Get CSS for the specified theme.

        Args:
            theme: Theme name

        Returns:
            CSS content
        """
        # Default theme
        if theme == "default":
            return """
            * {
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }
            
            body {
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
            }
            
            .form-container {
                max-width: 800px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            h1 {
                color: #333;
                margin-top: 0;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .form-description {
                color: #666;
                margin-bottom: 30px;
                text-align: center;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: bold;
                color: #333;
            }
            
            input[type="text"],
            input[type="email"],
            input[type="password"],
            input[type="number"],
            input[type="date"],
            textarea,
            select {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            input[type="text"]:focus,
            input[type="email"]:focus,
            input[type="password"]:focus,
            input[type="number"]:focus,
            input[type="date"]:focus,
            textarea:focus,
            select:focus {
                border-color: #4a90e2;
                outline: none;
            }
            
            textarea {
                min-height: 120px;
                resize: vertical;
            }
            
            .radio-option,
            .checkbox-option {
                margin-bottom: 10px;
            }
            
            .radio-label,
            .checkbox-label {
                display: inline;
                font-weight: normal;
                margin-left: 8px;
            }
            
            .help-text {
                color: #666;
                font-size: 14px;
                margin-top: 5px;
                margin-bottom: 0;
            }
            
            .form-buttons {
                display: flex;
                justify-content: space-between;
                margin-top: 30px;
            }
            
            .submit-button,
            .reset-button {
                padding: 12px 24px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            
            .submit-button {
                background-color: #4a90e2;
                color: white;
                flex-grow: 2;
                margin-right: 10px;
            }
            
            .submit-button:hover {
                background-color: #3a7bc8;
            }
            
            .reset-button {
                background-color: #f5f5f5;
                color: #333;
                border: 1px solid #ddd;
                flex-grow: 1;
            }
            
            .reset-button:hover {
                background-color: #e5e5e5;
            }
            
            .success-message {
                background-color: #dff0d8;
                color: #3c763d;
                padding: 15px;
                border-radius: 4px;
                margin-top: 20px;
                text-align: center;
            }
            
            @media (max-width: 600px) {
                .form-container {
                    padding: 20px;
                }
                
                .form-buttons {
                    flex-direction: column;
                }
                
                .submit-button,
                .reset-button {
                    width: 100%;
                    margin-right: 0;
                }
                
                .submit-button {
                    margin-bottom: 10px;
                }
            }
            """
        
        # Dark theme
        elif theme == "dark":
            return """
            * {
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }
            
            body {
                background-color: #2c2c2c;
                margin: 0;
                padding: 20px;
                color: #e0e0e0;
            }
            
            .form-container {
                max-width: 800px;
                margin: 0 auto;
                background-color: #333;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            }
            
            h1 {
                color: #fff;
                margin-top: 0;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .form-description {
                color: #bbb;
                margin-bottom: 30px;
                text-align: center;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: bold;
                color: #e0e0e0;
            }
            
            input[type="text"],
            input[type="email"],
            input[type="password"],
            input[type="number"],
            input[type="date"],
            textarea,
            select {
                width: 100%;
                padding: 12px;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 16px;
                background-color: #444;
                color: #e0e0e0;
                transition: border-color 0.3s;
            }
            
            input[type="text"]:focus,
            input[type="email"]:focus,
            input[type="password"]:focus,
            input[type="number"]:focus,
            input[type="date"]:focus,
            textarea:focus,
            select:focus {
                border-color: #4a90e2;
                outline: none;
            }
            
            textarea {
                min-height: 120px;
                resize: vertical;
            }
            
            .radio-option,
            .checkbox-option {
                margin-bottom: 10px;
            }
            
            .radio-label,
            .checkbox-label {
                display: inline;
                font-weight: normal;
                margin-left: 8px;
            }
            
            .help-text {
                color: #bbb;
                font-size: 14px;
                margin-top: 5px;
                margin-bottom: 0;
            }
            
            .form-buttons {
                display: flex;
                justify-content: space-between;
                margin-top: 30px;
            }
            
            .submit-button,
            .reset-button {
                padding: 12px 24px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            
            .submit-button {
                background-color: #4a90e2;
                color: white;
                flex-grow: 2;
                margin-right: 10px;
            }
            
            .submit-button:hover {
                background-color: #3a7bc8;
            }
            
            .reset-button {
                background-color: #555;
                color: #e0e0e0;
                border: 1px solid #666;
                flex-grow: 1;
            }
            
            .reset-button:hover {
                background-color: #444;
            }
            
            .success-message {
                background-color: #2e4132;
                color: #8bc34a;
                padding: 15px;
                border-radius: 4px;
                margin-top: 20px;
                text-align: center;
            }
            
            @media (max-width: 600px) {
                .form-container {
                    padding: 20px;
                }
                
                .form-buttons {
                    flex-direction: column;
                }
                
                .submit-button,
                .reset-button {
                    width: 100%;
                    margin-right: 0;
                }
                
                .submit-button {
                    margin-bottom: 10px;
                }
            }
            """
        
        # Minimal theme
        elif theme == "minimal":
            return """
            * {
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            }
            
            body {
                background-color: #fff;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            
            .form-container {
                max-width: 600px;
                margin: 0 auto;
                padding: 20px 0;
            }
            
            h1 {
                color: #333;
                margin-top: 0;
                margin-bottom: 20px;
                font-weight: 300;
            }
            
            .form-description {
                color: #666;
                margin-bottom: 30px;
            }
            
            .form-group {
                margin-bottom: 25px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #333;
            }
            
            input[type="text"],
            input[type="email"],
            input[type="password"],
            input[type="number"],
            input[type="date"],
            textarea,
            select {
                width: 100%;
                padding: 10px 0;
                border: none;
                border-bottom: 1px solid #ddd;
                font-size: 16px;
                background-color: transparent;
                transition: border-color 0.3s;
            }
            
            input[type="text"]:focus,
            input[type="email"]:focus,
            input[type="password"]:focus,
            input[type="number"]:focus,
            input[type="date"]:focus,
            textarea:focus,
            select:focus {
                border-color: #333;
                outline: none;
            }
            
            textarea {
                min-height: 100px;
                resize: vertical;
            }
            
            .radio-option,
            .checkbox-option {
                margin-bottom: 10px;
            }
            
            .radio-label,
            .checkbox-label {
                display: inline;
                font-weight: normal;
                margin-left: 8px;
            }
            
            .help-text {
                color: #999;
                font-size: 14px;
                margin-top: 5px;
                margin-bottom: 0;
            }
            
            .form-buttons {
                display: flex;
                justify-content: flex-end;
                margin-top: 30px;
            }
            
            .submit-button,
            .reset-button {
                padding: 10px 20px;
                border: none;
                font-size: 16px;
                cursor: pointer;
                transition: opacity 0.3s;
            }
            
            .submit-button {
                background-color: #333;
                color: white;
                margin-left: 10px;
            }
            
            .submit-button:hover {
                opacity: 0.9;
            }
            
            .reset-button {
                background-color: transparent;
                color: #333;
            }
            
            .reset-button:hover {
                opacity: 0.7;
            }
            
            .success-message {
                color: #4caf50;
                margin-top: 20px;
                text-align: center;
            }
            """
        
        # Default to basic CSS if theme not recognized
        return """
        * { box-sizing: border-box; }
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .form-container { max-width: 800px; margin: 0 auto; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input, textarea, select { width: 100%; padding: 8px; }
        .submit-button { padding: 10px 15px; background-color: #4a90e2; color: white; border: none; cursor: pointer; }
        .success-message { color: green; margin-top: 15px; }
        """

    def _get_form_javascript(self, form_id: str) -> str:
        """Get JavaScript for form functionality.

        Args:
            form_id: Form ID

        Returns:
            JavaScript content
        """
        return f"""
        document.addEventListener('DOMContentLoaded', function() {{
            const form = document.getElementById('dynamic-form');
            const successMessage = document.getElementById('success-message');
            
            form.addEventListener('submit', function(event) {{
                event.preventDefault();
                
                // Basic form validation
                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;
                
                requiredFields.forEach(function(field) {{
                    if (!field.value.trim()) {{
                        isValid = false;
                        field.classList.add('error');
                    }} else {{
                        field.classList.remove('error');
                    }}
                }});
                
                if (!isValid) {{
                    return false;
                }}
                
                // Collect form data
                const formData = new FormData(form);
                
                // Here you would typically send the data to the server
                // For this example, we'll just simulate a successful submission
                
                // Show success message
                form.style.display = 'none';
                successMessage.style.display = 'block';
                
                // Log form data for debugging
                console.log('Form {form_id} submitted with data:');
                for (let [key, value] of formData.entries()) {{
                    console.log(key + ': ' + value);
                }}
                
                return false;
            }});
        }});
        """
