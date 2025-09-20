from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db.models import Q
from .models import ReportRequest
from .utils import get_report_data, generate_pdf_report, generate_excel_report, generate_csv_report
from projects.models import Project
import os
import mimetypes

@login_required
def reports_dashboard(request):
    """Main reports dashboard"""
    # Get user's report requests
    report_requests = ReportRequest.objects.filter(user=request.user)[:10]
    
    # Get recent projects for filtering
    recent_projects = Project.objects.filter(created_by=request.user)[:5]
    
    # Statistics
    total_reports = ReportRequest.objects.filter(user=request.user).count()
    completed_reports = ReportRequest.objects.filter(user=request.user, status='completed').count()
    pending_reports = ReportRequest.objects.filter(user=request.user, status='pending').count()
    
    context = {
        'report_requests': report_requests,
        'recent_projects': recent_projects,
        'total_reports': total_reports,
        'completed_reports': completed_reports,
        'pending_reports': pending_reports,
        'report_types': ReportRequest.REPORT_TYPES,
        'format_choices': ReportRequest.FORMAT_CHOICES,
    }
    
    return render(request, 'reports/dashboard.html', context)

@login_required
def create_report_request(request):
    """Create a new report request"""
    if request.method == 'POST':
        # Get form data
        report_type = request.POST.get('report_type')
        format_type = request.POST.get('format')
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        date_from = request.POST.get('date_from') or None
        date_to = request.POST.get('date_to') or None
        project_ids = request.POST.getlist('project_ids')
        include_charts = request.POST.get('include_charts') == 'on'
        include_details = request.POST.get('include_details') == 'on'
        
        # Validate required fields
        if not report_type or not format_type:
            messages.error(request, 'Please select both report type and format.')
            return redirect('reports:dashboard')
        
        # Create report request
        report_request = ReportRequest.objects.create(
            user=request.user,
            report_type=report_type,
            format=format_type,
            title=title or f"{dict(ReportRequest.REPORT_TYPES)[report_type]} - {timezone.now().strftime('%Y-%m-%d')}",
            description=description,
            date_from=date_from,
            date_to=date_to,
            project_ids=[int(pid) for pid in project_ids if pid],
            include_charts=include_charts,
            include_details=include_details,
            status='pending'
        )
        
        # Generate report immediately (in a real app, this would be queued)
        try:
            generate_and_save_report(report_request)
            messages.success(request, f'Report "{report_request.title}" has been generated successfully!')
        except Exception as e:
            report_request.mark_failed()
            messages.error(request, f'Failed to generate report: {str(e)}')
        
        return redirect('reports:dashboard')
    
    return redirect('reports:dashboard')

@login_required
def download_report(request, report_id):
    """Download a completed report"""
    report_request = get_object_or_404(ReportRequest, id=report_id, user=request.user)
    
    if not report_request.is_completed or not report_request.file_path:
        messages.error(request, 'Report is not ready for download.')
        return redirect('reports:dashboard')
    
    try:
        # Check if file exists
        if default_storage.exists(report_request.file_path):
            file_path = report_request.file_path
        else:
            # Try to regenerate if file is missing
            generate_and_save_report(report_request)
            if not default_storage.exists(report_request.file_path):
                raise FileNotFoundError("Report file not found")
            file_path = report_request.file_path
        
        # Get file content
        file_content = default_storage.open(file_path).read()
        
        # Determine content type
        if report_request.format == 'pdf':
            content_type = 'application/pdf'
        elif report_request.format == 'excel':
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:  # csv
            content_type = 'text/csv'
        
        # Create response
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{report_request.title}.{report_request.format}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error downloading report: {str(e)}')
        return redirect('reports:dashboard')

@login_required
def delete_report(request, report_id):
    """Delete a report request"""
    report_request = get_object_or_404(ReportRequest, id=report_id, user=request.user)
    
    # Delete file if it exists
    if report_request.file_path and default_storage.exists(report_request.file_path):
        default_storage.delete(report_request.file_path)
    
    report_request.delete()
    messages.success(request, 'Report deleted successfully.')
    return redirect('reports:dashboard')

def generate_and_save_report(report_request):
    """Generate and save a report file"""
    # Mark as processing
    report_request.status = 'processing'
    report_request.save()
    
    try:
        # Get report data
        report_data = get_report_data(
            report_type=report_request.report_type,
            user=report_request.user,
            date_from=report_request.date_from,
            date_to=report_request.date_to,
            project_ids=report_request.project_ids
        )
        
        # Generate file based on format
        if report_request.format == 'pdf':
            if not REPORTLAB_AVAILABLE:
                raise ImportError("ReportLab is not installed. Install with: pip install reportlab")
            file_buffer = generate_pdf_report(report_data, report_request)
            file_extension = 'pdf'
            content_type = 'application/pdf'
        elif report_request.format == 'excel':
            if not OPENPYXL_AVAILABLE:
                raise ImportError("OpenPyXL is not installed. Install with: pip install openpyxl")
            file_buffer = generate_excel_report(report_data, report_request)
            file_extension = 'xlsx'
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:  # csv
            file_buffer = generate_csv_report(report_data, report_request)
            file_extension = 'csv'
            content_type = 'text/csv'
        
        # Save file
        filename = f"report_{report_request.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        file_path = f"reports/{filename}"
        
        # Save to storage
        if report_request.format == 'csv':
            file_content = ContentFile(file_buffer.getvalue().encode('utf-8'))
        else:
            file_content = ContentFile(file_buffer.getvalue())
        
        saved_path = default_storage.save(file_path, file_content)
        
        # Update report request
        report_request.mark_completed(
            file_path=saved_path,
            file_size=len(file_content)
        )
        
    except Exception as e:
        report_request.mark_failed()
        raise e

# Import availability flags
try:
    from .utils import REPORTLAB_AVAILABLE, OPENPYXL_AVAILABLE
except ImportError:
    REPORTLAB_AVAILABLE = False
    OPENPYXL_AVAILABLE = False
