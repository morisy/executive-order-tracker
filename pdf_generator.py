from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import datetime
import os
from typing import Dict, Optional
from io import BytesIO
from PyPDF2 import PdfWriter, PdfReader

class PDFGenerator:
    """Generate PDFs for Executive Orders with metadata"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='OrderTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#000080'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=6
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='OrderBody',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        ))
    
    def generate_pdf(self, order_data: Dict, output_path: Optional[str] = None) -> bytes:
        """Generate a PDF for an executive order"""
        # Create PDF in memory if no output path specified
        if output_path:
            pdf_buffer = output_path
        else:
            pdf_buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Add header
        elements.append(Paragraph("EXECUTIVE ORDER", self.styles['OrderTitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add title
        title = order_data.get('title', 'Untitled Executive Order')
        elements.append(Paragraph(title, self.styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add metadata table
        metadata_data = []
        
        if order_data.get('order_number'):
            metadata_data.append(['Order Number:', f"EO {order_data['order_number']}"])
        
        if order_data.get('date_str'):
            metadata_data.append(['Issue Date:', order_data['date_str']])
        elif order_data.get('metadata', {}).get('issue_date'):
            metadata_data.append(['Issue Date:', order_data['metadata']['issue_date']])
        
        metadata_data.append(['Source URL:', order_data.get('url', 'N/A')])
        metadata_data.append(['Archived:', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')])
        
        if order_data.get('metadata', {}).get('categories'):
            categories = ', '.join(order_data['metadata']['categories'])
            metadata_data.append(['Categories:', categories])
        
        # Create metadata table
        if metadata_data:
            t = Table(metadata_data, colWidths=[1.5*inch, 4.5*inch])
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 0.3*inch))
        
        # Add separator line
        elements.append(Paragraph('_' * 80, self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add main content
        full_text = order_data.get('full_text', 'No content available.')
        
        # Split text into paragraphs and process
        paragraphs = full_text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Clean up the paragraph
                para = para.strip()
                
                # Check if it's a section header (all caps or starts with Roman numerals)
                if para.isupper() or para.startswith(('I.', 'II.', 'III.', 'IV.', 'V.')):
                    elements.append(Paragraph(para, self.styles['Heading3']))
                else:
                    elements.append(Paragraph(para, self.styles['OrderBody']))
                
                elements.append(Spacer(1, 0.1*inch))
        
        # Add footer
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph('_' * 80, self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        footer_text = (
            f"This document was automatically archived by DocumentCloud's Executive Orders Monitor<br/>"
            f"Original source: <link href='{order_data.get('url', '#')}'>whitehouse.gov</link><br/>"
            f"Archive timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        elements.append(Paragraph(footer_text, self.styles['Footer']))
        
        # Build PDF
        doc.build(elements)
        
        # Add metadata to PDF
        if not output_path:
            pdf_buffer.seek(0)
            pdf_with_metadata = self._add_pdf_metadata(pdf_buffer, order_data)
            return pdf_with_metadata
        else:
            # If file was written to disk, read it back and add metadata
            with open(output_path, 'rb') as f:
                pdf_with_metadata = self._add_pdf_metadata(f, order_data)
            with open(output_path, 'wb') as f:
                f.write(pdf_with_metadata)
            return pdf_with_metadata
    
    def _add_pdf_metadata(self, pdf_file, order_data: Dict) -> bytes:
        """Add metadata to PDF file"""
        reader = PdfReader(pdf_file)
        writer = PdfWriter()
        
        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)
        
        # Add metadata
        metadata = {
            '/Title': order_data.get('title', 'Executive Order'),
            '/Author': 'The White House',
            '/Subject': 'Executive Order',
            '/Keywords': 'executive order, white house, presidential action',
            '/Creator': 'DocumentCloud Executive Orders Monitor',
            '/Producer': 'DocumentCloud / ReportLab',
            '/CreationDate': datetime.now().strftime('D:%Y%m%d%H%M%S'),
            '/SourceURL': order_data.get('url', ''),
        }
        
        if order_data.get('order_number'):
            metadata['/Keywords'] += f", EO {order_data['order_number']}"
        
        writer.add_metadata(metadata)
        
        # Write to bytes
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        return output_buffer.read()