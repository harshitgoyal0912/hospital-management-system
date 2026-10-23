"""
Hospital Discharge Report Management System
==========================================

This module provides comprehensive management for discharge reports including:
- Report generation and storage
- Report retrieval and download
- Report search and filtering
- Report archiving and cleanup

Author: Hospital Management System
Date: August 7, 2025
"""

import os
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import uuid
import re

# PDF generation imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import markdown2

from database import SessionLocal, DischargeReport, Patient, User
from discharge_service import PatientDischargeReportGenerator


class ReportManager:
    """Manages discharge reports - storage, retrieval, and download."""
    
    def __init__(self):
        self.session = SessionLocal()
        self.reports_dir = Path("reports/discharge")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (self.reports_dir / "current").mkdir(exist_ok=True)
        (self.reports_dir / "archive").mkdir(exist_ok=True)
        (self.reports_dir / "downloads").mkdir(exist_ok=True)
    
    def save_report(self, report_data: Dict[str, Any], report_content: str) -> Dict[str, Any]:
        """
        Save a discharge report to the file system and database.
        
        Args:
            report_data: Report metadata
            report_content: The actual report content (markdown)
            
        Returns:
            Dictionary with save result and file paths
        """
        try:
            # Create unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_number = report_data.get('report_number', f'DR-{timestamp}')
            filename = f"{report_number}_{timestamp}.md"
            filepath = self.reports_dir / "current" / filename
            
            # Save markdown content to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # Create JSON metadata file
            metadata = {
                "report_number": report_number,
                "patient_name": report_data.get('patient_name', ''),
                "patient_id": report_data.get('patient_id', ''),
                "generated_at": datetime.now().isoformat(),
                "generated_by": report_data.get('generated_by', ''),
                "discharge_date": report_data.get('discharge_date', ''),
                "file_path": str(filepath),
                "file_size": os.path.getsize(filepath),
                "report_type": "discharge",
                "status": "current"
            }
            
            metadata_filepath = self.reports_dir / "current" / f"{report_number}_{timestamp}_metadata.json"
            with open(metadata_filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return {
                "success": True,
                "report_number": report_number,
                "filepath": str(filepath),
                "metadata_filepath": str(metadata_filepath),
                "message": "Report saved successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save report"
            }
    
    def get_report_by_number(self, report_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a report by its report number.
        
        Args:
            report_number: The report number to search for
            
        Returns:
            Report data if found, None otherwise
        """
        try:
            # First check the database for the report
            db_report = self.session.query(DischargeReport).filter(
                DischargeReport.report_number == report_number
            ).first()
            
            if db_report:
                # Convert database report to expected format
                report_data = {
                    "id": str(db_report.id),
                    "report_number": db_report.report_number,
                    "patient_id": str(db_report.patient_id),
                    "bed_id": str(db_report.bed_id),
                    "generated_by": str(db_report.generated_by) if db_report.generated_by else None,
                    "admission_date": db_report.admission_date.isoformat() if db_report.admission_date else None,
                    "discharge_date": db_report.discharge_date.isoformat() if db_report.discharge_date else None,
                    "length_of_stay_days": db_report.length_of_stay_days,
                    "patient_summary": json.loads(db_report.patient_summary) if db_report.patient_summary else {},
                    "treatment_summary": json.loads(db_report.treatment_summary) if db_report.treatment_summary else [],
                    "equipment_summary": json.loads(db_report.equipment_summary) if db_report.equipment_summary else [],
                    "staff_summary": json.loads(db_report.staff_summary) if db_report.staff_summary else [],
                    "medications": json.loads(db_report.medications) if db_report.medications else [],
                    "procedures": json.loads(db_report.procedures) if db_report.procedures else [],
                    "discharge_instructions": db_report.discharge_instructions or "",
                    "follow_up_required": db_report.follow_up_required or "",
                    "discharge_condition": db_report.discharge_condition,
                    "discharge_destination": db_report.discharge_destination,
                    "created_at": db_report.created_at.isoformat(),
                    "source": "database"
                }
                
                # Generate markdown content from the database data
                report_data['content'] = self._generate_markdown_content(report_data)
                return report_data
            
            # Search in current reports first (file system fallback)
            current_dir = self.reports_dir / "current"
            for metadata_file in current_dir.glob(f"{report_number}_*_metadata.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Read the report content
                report_filepath = Path(metadata['file_path'])
                if report_filepath.exists():
                    with open(report_filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    metadata['content'] = content
                    metadata['source'] = "file_system"
                    return metadata
            
            # Search in archive if not found in current
            archive_dir = self.reports_dir / "archive"
            for metadata_file in archive_dir.glob(f"{report_number}_*_metadata.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                report_filepath = Path(metadata['file_path'])
                if report_filepath.exists():
                    with open(report_filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    metadata['content'] = content
                    metadata['status'] = 'archived'
                    return metadata
            
            return None
            
        except Exception as e:
            print(f"Error retrieving report {report_number}: {e}")
            return None
    
    def _generate_markdown_content(self, report_data: Dict[str, Any]) -> str:
        """Generate markdown content from database report data."""
        try:
            patient_summary = report_data.get('patient_summary', {})
            treatments = report_data.get('treatment_summary', [])
            equipment_usage = report_data.get('equipment_summary', [])
            staff_assignments = report_data.get('staff_summary', [])
            medications = report_data.get('medications', [])
            procedures = report_data.get('procedures', [])

            # Backward-compatible resolution of bed, room and department
            bed_no = patient_summary.get('bed_number') or (patient_summary.get('bed_info', {}) or {}).get('bed_number') or 'N/A'
            room_no = patient_summary.get('room_number') or (patient_summary.get('bed_info', {}) or {}).get('room') or 'N/A'
            dept_name = patient_summary.get('department') or (patient_summary.get('bed_info', {}) or {}).get('department') or 'N/A'
            
            markdown_content = f"""# PATIENT DISCHARGE REPORT

**Report Number:** {report_data.get('report_number', 'N/A')}  
**Generated:** {report_data.get('created_at', 'N/A')}  

## PATIENT INFORMATION

- **Name:** {patient_summary.get('name', 'N/A')}
- **Patient Number:** {patient_summary.get('patient_number', 'N/A')}
- **Date of Birth:** {patient_summary.get('date_of_birth', 'N/A')}
- **Gender:** {patient_summary.get('gender', 'N/A')}
- **Blood Type:** {patient_summary.get('blood_type', 'N/A')}

## ADMISSION DETAILS

- **Admission Date:** {report_data.get('admission_date', 'N/A')}
- **Discharge Date:** {report_data.get('discharge_date', 'N/A')}
- **Length of Stay:** {report_data.get('length_of_stay_days', 'N/A')} days
- **Bed:** {bed_no}
- **Room:** {room_no}
- **Department:** {dept_name}

## TREATMENTS ADMINISTERED

"""
            if treatments:
                for treatment in treatments:
                    markdown_content += f"### {treatment.get('treatment_name', 'Unknown Treatment')}\n"
                    markdown_content += f"- **Type:** {treatment.get('treatment_type', 'N/A')}\n"
                    markdown_content += f"- **Description:** {treatment.get('description', 'N/A')}\n"
                    markdown_content += f"- **Doctor:** {treatment.get('doctor', 'N/A')}\n"
                    markdown_content += f"- **Status:** {treatment.get('status', 'N/A')}\n\n"
            else:
                markdown_content += "No treatments recorded.\n\n"

            markdown_content += """## EQUIPMENT USAGE

"""
            if equipment_usage:
                for equipment in equipment_usage:
                    markdown_content += f"### {equipment.get('equipment_name', 'Unknown Equipment')}\n"
                    markdown_content += f"- **Type:** {equipment.get('equipment_type', 'N/A')}\n"
                    markdown_content += f"- **Purpose:** {equipment.get('purpose', 'N/A')}\n"
                    markdown_content += f"- **Operated By:** {equipment.get('operated_by', 'N/A')}\n"
                    markdown_content += f"- **Duration:** {equipment.get('duration_minutes', 'N/A')} minutes\n\n"
            else:
                markdown_content += "No equipment usage recorded.\n\n"

            markdown_content += """## STAFF ASSIGNMENTS

"""
            if staff_assignments:
                for staff in staff_assignments:
                    markdown_content += f"### {staff.get('staff_name', 'Unknown Staff')}\n"
                    markdown_content += f"- **Position:** {staff.get('position', 'N/A')}\n"
                    markdown_content += f"- **Department:** {staff.get('department', 'N/A')}\n"
                    markdown_content += f"- **Assignment Type:** {staff.get('assignment_type', 'N/A')}\n"
                    markdown_content += f"- **Responsibilities:** {staff.get('responsibilities', 'N/A')}\n\n"
            else:
                markdown_content += "No staff assignments recorded.\n\n"

            markdown_content += """## MEDICATIONS

"""
            if medications:
                for medication in medications:
                    markdown_content += f"### {medication.get('medication_name', 'Unknown Medication')}\n"
                    markdown_content += f"- **Dosage:** {medication.get('dosage', 'N/A')}\n"
                    markdown_content += f"- **Frequency:** {medication.get('frequency', 'N/A')}\n"
                    markdown_content += f"- **Duration:** {medication.get('duration', 'N/A')}\n"
                    markdown_content += f"- **Prescribed By:** {medication.get('prescribed_by', 'N/A')}\n\n"
            else:
                markdown_content += "No medications recorded.\n\n"

            markdown_content += f"""## DISCHARGE INFORMATION

**Discharge Condition:** {report_data.get('discharge_condition', 'N/A')}  
**Discharge Destination:** {report_data.get('discharge_destination', 'N/A')}  

### Discharge Instructions
{report_data.get('discharge_instructions', 'No specific instructions provided.')}

### Follow-up Required
{report_data.get('follow_up_required', 'No follow-up specified.')}

---
*Report generated by Hospital Management System*
"""
            return markdown_content
            
        except Exception as e:
            return f"Error generating markdown content: {str(e)}"
    
    def list_reports(self, 
                    status: str = "all", 
                    patient_name: str = None,
                    from_date: str = None,
                    to_date: str = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        """
        List discharge reports with optional filtering.
        
        Args:
            status: "current", "archived", or "all"
            patient_name: Filter by patient name (partial match)
            from_date: Start date filter (YYYY-MM-DD)
            to_date: End date filter (YYYY-MM-DD)
            limit: Maximum number of reports to return
            
        Returns:
            List of report metadata
        """
        reports = []
        
        try:
            # Determine which directories to search
            dirs_to_search = []
            if status in ["all", "current"]:
                dirs_to_search.append(self.reports_dir / "current")
            if status in ["all", "archived"]:
                dirs_to_search.append(self.reports_dir / "archive")
            
            for search_dir in dirs_to_search:
                if not search_dir.exists():
                    continue
                    
                for metadata_file in search_dir.glob("*_metadata.json"):
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # Apply filters
                    if patient_name and patient_name.lower() not in metadata.get('patient_name', '').lower():
                        continue
                    
                    if from_date:
                        report_date = datetime.fromisoformat(metadata['generated_at']).date()
                        if report_date < datetime.strptime(from_date, '%Y-%m-%d').date():
                            continue
                    
                    if to_date:
                        report_date = datetime.fromisoformat(metadata['generated_at']).date()
                        if report_date > datetime.strptime(to_date, '%Y-%m-%d').date():
                            continue
                    
                    # Add status information
                    metadata['status'] = 'archived' if 'archive' in str(search_dir) else 'current'
                    reports.append(metadata)
            
            # Sort by generation date (newest first) and apply limit
            reports.sort(key=lambda x: x['generated_at'], reverse=True)
            return reports[:limit]
            
        except Exception as e:
            print(f"Error listing reports: {e}")
            return []
    
    def download_report(self, report_number: str, download_format: str = "pdf") -> Dict[str, Any]:
        """
        Prepare a report for download in specified format.
        
        Args:
            report_number: The report number to download
            download_format: "pdf", "markdown", or "zip"
            
        Returns:
            Download information including file path
        """
        try:
            # Get the report
            report_data = self.get_report_by_number(report_number)
            if not report_data:
                return {
                    "success": False,
                    "error": "Report not found",
                    "message": f"Report {report_number} not found"
                }
            
            downloads_dir = self.reports_dir / "downloads"
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if download_format == "markdown":
                # Copy markdown file to downloads
                download_filename = f"{report_number}_{timestamp}.md"
                download_path = downloads_dir / download_filename
                
                with open(download_path, 'w', encoding='utf-8') as f:
                    f.write(report_data['content'])
                
                return {
                    "success": True,
                    "download_path": str(download_path),
                    "filename": download_filename,
                    "format": "markdown",
                    "size": os.path.getsize(download_path)
                }
            
            elif download_format == "zip":
                # Create ZIP with both markdown and metadata
                download_filename = f"{report_number}_{timestamp}.zip"
                download_path = downloads_dir / download_filename
                
                with zipfile.ZipFile(download_path, 'w') as zipf:
                    # Add markdown content
                    zipf.writestr(f"{report_number}.md", report_data['content'])
                    
                    # Add metadata
                    metadata_clean = {k: v for k, v in report_data.items() if k != 'content'}
                    zipf.writestr(f"{report_number}_metadata.json", 
                                json.dumps(metadata_clean, indent=2))
                
                return {
                    "success": True,
                    "download_path": str(download_path),
                    "filename": download_filename,
                    "format": "zip",
                    "size": os.path.getsize(download_path)
                }
            
            elif download_format == "pdf":
                # Generate PDF from markdown content
                download_filename = f"{report_number}_{timestamp}.pdf"
                download_path = downloads_dir / download_filename
                
                # Convert markdown to PDF
                pdf_success = self._generate_pdf(report_data['content'], str(download_path), report_data)
                
                if pdf_success:
                    return {
                        "success": True,
                        "download_path": str(download_path),
                        "filename": download_filename,
                        "format": "pdf",
                        "file_size": os.path.getsize(download_path)
                    }
                else:
                    return {
                        "success": False,
                        "error": "PDF generation failed",
                        "message": "Failed to generate PDF from report content"
                    }
            
            else:
                return {
                    "success": False,
                    "error": "Unsupported format",
                    "message": f"Format '{download_format}' not supported. Use 'pdf', 'markdown' or 'zip'."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to prepare download"
            }
    
    def archive_old_reports(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Archive reports older than specified days.
        
        Args:
            days_old: Reports older than this many days will be archived
            
        Returns:
            Archive operation result
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            archived_count = 0
            current_dir = self.reports_dir / "current"
            archive_dir = self.reports_dir / "archive"
            
            for metadata_file in current_dir.glob("*_metadata.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                report_date = datetime.fromisoformat(metadata['generated_at'])
                
                if report_date < cutoff_date:
                    # Move both metadata and report files to archive
                    report_filepath = Path(metadata['file_path'])
                    
                    if report_filepath.exists():
                        # Move report file
                        archive_report_path = archive_dir / report_filepath.name
                        shutil.move(str(report_filepath), str(archive_report_path))
                        
                        # Update metadata with new path
                        metadata['file_path'] = str(archive_report_path)
                        metadata['status'] = 'archived'
                        metadata['archived_at'] = datetime.now().isoformat()
                        
                        # Move metadata file
                        archive_metadata_path = archive_dir / metadata_file.name
                        with open(archive_metadata_path, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=2)
                        
                        # Remove original metadata file
                        metadata_file.unlink()
                        
                        archived_count += 1
            
            return {
                "success": True,
                "archived_count": archived_count,
                "cutoff_date": cutoff_date.isoformat(),
                "message": f"Archived {archived_count} reports older than {days_old} days"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to archive reports"
            }
    
    def cleanup_downloads(self, hours_old: int = 24) -> Dict[str, Any]:
        """
        Clean up old download files.
        
        Args:
            hours_old: Delete download files older than this many hours
            
        Returns:
            Cleanup operation result
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_old)
            cleaned_count = 0
            downloads_dir = self.reports_dir / "downloads"
            
            for download_file in downloads_dir.glob("*"):
                if download_file.is_file():
                    file_time = datetime.fromtimestamp(download_file.stat().st_mtime)
                    
                    if file_time < cutoff_time:
                        download_file.unlink()
                        cleaned_count += 1
            
            return {
                "success": True,
                "cleaned_count": cleaned_count,
                "cutoff_time": cutoff_time.isoformat(),
                "message": f"Cleaned up {cleaned_count} download files older than {hours_old} hours"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to cleanup downloads"
            }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for the report system."""
        try:
            stats = {
                "current_reports": 0,
                "archived_reports": 0,
                "download_files": 0,
                "total_size_mb": 0,
                "current_size_mb": 0,
                "archived_size_mb": 0,
                "downloads_size_mb": 0
            }
            
            # Count current reports
            current_dir = self.reports_dir / "current"
            if current_dir.exists():
                stats["current_reports"] = len(list(current_dir.glob("*.md")))
                for file in current_dir.glob("*"):
                    stats["current_size_mb"] += file.stat().st_size / (1024 * 1024)
            
            # Count archived reports
            archive_dir = self.reports_dir / "archive"
            if archive_dir.exists():
                stats["archived_reports"] = len(list(archive_dir.glob("*.md")))
                for file in archive_dir.glob("*"):
                    stats["archived_size_mb"] += file.stat().st_size / (1024 * 1024)
            
            # Count download files
            downloads_dir = self.reports_dir / "downloads"
            if downloads_dir.exists():
                stats["download_files"] = len(list(downloads_dir.glob("*")))
                for file in downloads_dir.glob("*"):
                    stats["downloads_size_mb"] += file.stat().st_size / (1024 * 1024)
            
            stats["total_size_mb"] = (stats["current_size_mb"] + 
                                    stats["archived_size_mb"] + 
                                    stats["downloads_size_mb"])
            
            # Round to 2 decimal places
            for key in ["total_size_mb", "current_size_mb", "archived_size_mb", "downloads_size_mb"]:
                stats[key] = round(stats[key], 2)
            
            return {
                "success": True,
                "stats": stats
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get storage stats"
            }
    
    def _generate_pdf(self, markdown_content: str, output_path: str, report_data: Dict[str, Any]) -> bool:
        """
        Generate a professional PDF from markdown content with letterhead and footer.
        
        Args:
            markdown_content: The markdown content to convert
            output_path: Path where PDF should be saved
            report_data: Report metadata for enhanced formatting
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create PDF document with margins
            doc = SimpleDocTemplate(
                output_path, 
                pagesize=A4,
                topMargin=1*inch,
                bottomMargin=1*inch,
                leftMargin=0.8*inch,
                rightMargin=0.8*inch
            )
            
            styles = getSampleStyleSheet()
            story = []
            
            # Add professional letterhead
            story.extend(self._create_letterhead())
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=20,
                spaceBefore=10,
                textColor=colors.Color(0.1, 0.3, 0.6),  # Professional blue
                alignment=1,  # Center alignment
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=15,
                textColor=colors.Color(0.1, 0.3, 0.6),
                fontName='Helvetica-Bold',
                borderWidth=1,
                borderColor=colors.Color(0.8, 0.8, 0.9),
                borderPadding=8,
                backColor=colors.Color(0.95, 0.95, 0.98)
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                leading=14,
                fontName='Helvetica'
            )
            
            field_style = ParagraphStyle(
                'FieldStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=4,
                leading=12,
                leftIndent=20,
                fontName='Helvetica'
            )
            
            # Parse markdown content into sections
            lines = markdown_content.strip().split('\n')
            current_paragraph = []
            in_list = False
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    if current_paragraph:
                        formatted_text = self._format_text(' '.join(current_paragraph))
                        story.append(Paragraph(formatted_text, normal_style))
                        current_paragraph = []
                    if not in_list:
                        story.append(Spacer(1, 8))
                    continue
                
                # Handle main title
                if line.startswith('# '):
                    if current_paragraph:
                        formatted_text = self._format_text(' '.join(current_paragraph))
                        story.append(Paragraph(formatted_text, normal_style))
                        current_paragraph = []
                    title_text = self._clean_formatting(line[2:])
                    story.append(Paragraph(title_text, title_style))
                    story.append(Spacer(1, 15))
                    in_list = False
                    
                elif line.startswith('## '):
                    if current_paragraph:
                        formatted_text = self._format_text(' '.join(current_paragraph))
                        story.append(Paragraph(formatted_text, normal_style))
                        current_paragraph = []
                    heading_text = self._clean_formatting(line[3:])
                    story.append(Paragraph(heading_text, heading_style))
                    story.append(Spacer(1, 10))
                    in_list = False
                    
                elif line.startswith('### '):
                    if current_paragraph:
                        formatted_text = self._format_text(' '.join(current_paragraph))
                        story.append(Paragraph(formatted_text, normal_style))
                        current_paragraph = []
                    subheading_text = self._clean_formatting(line[4:])
                    subheading_style = ParagraphStyle(
                        'SubHeading',
                        parent=normal_style,
                        fontSize=12,
                        fontName='Helvetica-Bold',
                        spaceAfter=8,
                        spaceBefore=12,
                        textColor=colors.Color(0.2, 0.2, 0.2)
                    )
                    story.append(Paragraph(subheading_text, subheading_style))
                    story.append(Spacer(1, 6))
                    in_list = False
                    
                elif line.startswith('- ') or line.startswith('* '):
                    # Bullet points - handle field formatting
                    if current_paragraph:
                        formatted_text = self._format_text(' '.join(current_paragraph))
                        story.append(Paragraph(formatted_text, normal_style))
                        current_paragraph = []
                    
                    bullet_text = line[2:] if line.startswith('- ') else line[2:]
                    formatted_bullet = self._format_field(bullet_text)
                    story.append(Paragraph(f"• {formatted_bullet}", field_style))
                    in_list = True
                    
                elif line.startswith('---'):
                    # Separator line
                    if current_paragraph:
                        formatted_text = self._format_text(' '.join(current_paragraph))
                        story.append(Paragraph(formatted_text, normal_style))
                        current_paragraph = []
                    story.append(Spacer(1, 15))
                    in_list = False
                    
                else:
                    # Regular content - clean all formatting
                    cleaned_line = self._clean_formatting(line)
                    if cleaned_line:  # Only add non-empty lines
                        current_paragraph.append(cleaned_line)
                    in_list = False
            
            # Add any remaining paragraph
            if current_paragraph:
                formatted_text = self._format_text(' '.join(current_paragraph))
                story.append(Paragraph(formatted_text, normal_style))
            
            # Add professional footer
            story.extend(self._create_footer(report_data))
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"PDF generation error: {e}")
            return False
    
    def _create_letterhead(self):
        """Create professional letterhead with real logo image."""
        elements = []
        
        # Create a table for the header with logo and hospital info
        from reportlab.platypus import Table, TableStyle, Image
        from reportlab.lib.colors import Color
        import os
        
        # Define colors to match the healthcare logo design
        logo_blue = Color(0.0, 0.4, 0.8)        # Primary logo blue
        dark_blue = Color(0.15, 0.25, 0.55)     # Dark navy for hospital name
        light_blue = Color(0.4, 0.75, 0.9)      # Light blue accent  
        gray_text = Color(0.4, 0.4, 0.4)        # Professional gray for contact info
        
        # Load the real healthcare logo
        logo_path = os.path.join("reports", "discharge", "archive", "image.png")
        try:
            # Create logo image with proper sizing
            logo_img = Image(logo_path, width=0.7*inch, height=0.7*inch)
        except Exception as e:
            print(f"Could not load logo image: {e}")
            # Fallback to text logo if image fails
            logo_img = "◉\n♡"
        
        # Header content with real logo - three columns layout
        header_data = [
            # Single row: Logo, Hospital Name + Subtitle, Address + Contact Info
            [logo_img, "GENERAL HOSPITAL\nHealth Care", "123 Healthcare Ave., Medical City, MC 12345\n+123-456-7890\nhello@metrohospital.com\nwww.metrohospital.com"]
        ]
        
        # Create the main header table with better proportions for three columns
        header_table = Table(header_data, colWidths=[0.8*inch, 3.2*inch, 2.6*inch])
        
        header_table.setStyle(TableStyle([
            # Logo styling - center the image (Column 1)
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('VALIGN', (0, 0), (0, -1), 'MIDDLE'),
            
            # Hospital name + subtitle styling (Column 2)
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 16),
            ('TEXTCOLOR', (1, 0), (1, 0), dark_blue),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
            ('LEADING', (1, 0), (1, 0), 18),  # Line spacing between hospital name and subtitle
            
            # Address + contact info styling (Column 3)
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica'),
            ('FONTSIZE', (2, 0), (2, 0), 8),
            ('TEXTCOLOR', (2, 0), (2, 0), gray_text),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (2, 0), (2, 0), 'TOP'),
            ('LEADING', (2, 0), (2, 0), 10),  # Tight line spacing for contact info
            
            # Clean spacing - no borders, reduced padding
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 10))  # Reduced spacing after header
        
        # Professional accent line
        line_data = [["", ""]]
        accent_line_table = Table(line_data, colWidths=[4.0*inch, 2.6*inch])
        accent_line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), light_blue),
            ('BACKGROUND', (1, 0), (1, 0), dark_blue),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 3),  # Reduced padding
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),  # Reduced padding
        ]))
        
        elements.append(accent_line_table)
        # Reduced spacing to prevent overlapping but keep content closer
        elements.append(Spacer(1, 25))  
        
        return elements
    
    def _create_footer(self, report_data: Dict[str, Any]):
        """Create professional footer  template."""
        elements = []
        
        # Add minimal space before footer to save space
        elements.append(Spacer(1, 15))  # Reduced from 30
        
        # Create a signature area with professional layout
        from reportlab.platypus import Table, TableStyle, Image
        from reportlab.lib.colors import Color
        import os
        
        # Define colors for footer
        dark_blue = Color(0.15, 0.25, 0.55)
        gray_text = Color(0.4, 0.4, 0.4)
        light_gray = Color(0.8, 0.8, 0.8)
        
        # Create a more compact signature area
        signature_data = [
            ["Discharge authorized by:", ""],
            ["", ""],
            ["Dr. _________________________________", "Date: ____________________"],
            ["Attending Physician", ""],
            ["Signature: _____________________________", ""]
        ]
        
        signature_table = Table(signature_data, colWidths=[4*inch, 2*inch])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),  # Reduced padding
            ('TOPPADDING', (0, 0), (-1, -1), 3),     # Reduced padding
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 20))  # Reduced spacing
        
        # Professional footer separator line (like DAYA template)
        footer_line_data = [["", ""]]
        footer_line_table = Table(footer_line_data, colWidths=[6.5*inch])
        footer_line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        elements.append(footer_line_table)
        elements.append(Spacer(1, 5))  # Reduced from 10
        
        # Footer with logo and contact information - smaller logo for compactness
        logo_path = os.path.join("reports", "discharge", "archive", "image.png")
        try:
            # Create smaller logo for footer to save space
            footer_logo = Image(logo_path, width=0.3*inch, height=0.3*inch)  # Reduced from 0.4
        except Exception as e:
            print(f"Could not load footer logo: {e}")
            footer_logo = "◉"
        
        # Footer content matching DAYA template layout
        generation_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        # Compact footer content without "DAYA" and reduced gaps
        footer_data = [
            # Row 1: All contact info in one line, hospital name, and logo
            ["Viyyur, Thrissur | 0487 3501000, 0487 2475100\nEmergency Hotline: 0487 2323000\nwww.dayageneralhospital.com", "GENERAL HOSPITAL", footer_logo],
            # Row 2: Centered document information
            ["This is an official medical document. Please retain for your records.", "", ""],
            ["General Hospital - Patient Discharge Summary", "", ""]
        ]
        
        footer_table = Table(footer_data, colWidths=[3.5*inch, 2.0*inch, 1.0*inch])
        footer_table.setStyle(TableStyle([
            # Contact info styling (left column) - compact with no gaps between lines
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica'),
            ('FONTSIZE', (0, 0), (0, 0), 8),
            ('TEXTCOLOR', (0, 0), (0, 0), gray_text),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('LEADING', (0, 0), (0, 0), 9),  # Tight line spacing for contact info
            
            # Hospital name styling (middle column) - reduced size
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 11),  # Reduced from 12
            ('TEXTCOLOR', (1, 0), (1, 0), dark_blue),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
            
            # Logo styling (right column)
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),
            ('VALIGN', (2, 0), (2, 0), 'MIDDLE'),
            
            # Document metadata styling (rows 2-3) - centered across all columns
            ('FONTNAME', (0, 1), (0, 2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, 2), 8),  # Smaller font size
            ('TEXTCOLOR', (0, 1), (0, 2), Color(0.5, 0.5, 0.5)),
            ('ALIGN', (0, 1), (2, 2), 'CENTER'),  # Center across all 3 columns
            ('VALIGN', (0, 1), (0, 2), 'MIDDLE'),
            ('SPAN', (0, 1), (2, 1)),  # Span first metadata line across all columns
            ('SPAN', (0, 2), (2, 2)),  # Span second metadata line across all columns
            
            # Minimal borders and very compact padding
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 3),     # Very compact
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            
            # Minimal extra spacing for metadata rows
            ('TOPPADDING', (0, 1), (2, 2), 6),  # Reduced from 15
            ('BOTTOMPADDING', (0, 1), (2, 2), 3), # Reduced from 10
        ]))
        
        elements.append(footer_table)
        
        return elements
    
    def _clean_formatting(self, text: str) -> str:
        """Remove ALL markdown formatting marks but preserve the text."""
        if not text:
            return ""
        
        # Remove ** formatting (multiple passes to catch nested cases)
        text = re.sub(r'\*\*([^*]*?)\*\*', r'\1', text)
        text = re.sub(r'\*\*([^*]*)', r'\1', text)  # Handle cases where ** is at start
        text = re.sub(r'([^*]*)\*\*', r'\1', text)  # Handle cases where ** is at end
        text = text.replace('**', '')  # Remove any remaining **
        
        # Remove single * formatting
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', text)
        text = text.replace('*', '')  # Remove any remaining *
        
        # Remove ### formatting
        text = re.sub(r'###\s*', '', text)
        
        return text.strip()
    
    def _format_text(self, text: str) -> str:
        """Format text for PDF, converting markdown to HTML-like tags and removing all ** marks."""
        if not text:
            return ""
        
        # First, convert **text** to bold HTML tags
        text = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', text)
        
        # Remove any remaining ** that weren't converted
        text = text.replace('**', '')
        
        # Convert *text* to italic (but not ** cases)
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)
        
        # Remove any remaining single *
        text = text.replace('*', '')
        
        return text
    
    def _format_field(self, text: str) -> str:
        """Format field entries (like Name: John Doe) with better styling."""
        if not text:
            return ""
        
        # Handle field: value patterns
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) == 2:
                field_name = self._clean_formatting(parts[0].strip())
                field_value = self._clean_formatting(parts[1].strip())
                return f"<b>{field_name}:</b> {field_value}"
        
        # Clean any remaining formatting
        return self._clean_formatting(text)
    
    def __del__(self):
        """Close database session when object is destroyed."""
        if hasattr(self, 'session'):
            self.session.close()


# Convenience functions for easy integration
def save_discharge_report(report_data: Dict[str, Any], report_content: str) -> Dict[str, Any]:
    """Save a discharge report using the report manager."""
    manager = ReportManager()
    return manager.save_report(report_data, report_content)


def get_discharge_report(report_number: str) -> Optional[Dict[str, Any]]:
    """Get a discharge report by number."""
    manager = ReportManager()
    return manager.get_report_by_number(report_number)


def download_discharge_report(report_number: str, format: str = "markdown") -> Dict[str, Any]:
    """Download a discharge report in specified format."""
    manager = ReportManager()
    return manager.download_report(report_number, format)


def list_discharge_reports(**kwargs) -> List[Dict[str, Any]]:
    """List discharge reports with filtering options."""
    manager = ReportManager()
    return manager.list_reports(**kwargs)


if __name__ == "__main__":
    # Test the report manager
    manager = ReportManager()
    
    # Get storage stats
    stats = manager.get_storage_stats()
    print("Storage Stats:", json.dumps(stats, indent=2))
    
    # List current reports
    reports = manager.list_reports(status="current", limit=10)
    print(f"\nFound {len(reports)} current reports")
    
    for report in reports:
        print(f"- {report['report_number']}: {report['patient_name']} ({report['generated_at'][:10]})")
