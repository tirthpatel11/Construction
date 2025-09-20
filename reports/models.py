from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ReportRequest(models.Model):
    REPORT_TYPES = [
        ('project_summary', 'Project Summary Report'),
        ('financial_overview', 'Financial Overview Report'),
        ('project_progress', 'Project Progress Report'),
        ('material_usage', 'Material Usage Report'),
        ('cost_analysis', 'Cost Analysis Report'),
        ('timeline_report', 'Project Timeline Report'),
        ('budget_variance', 'Budget Variance Report'),
        ('quality_metrics', 'Quality Metrics Report'),
        ('resource_utilization', 'Resource Utilization Report'),
        ('custom', 'Custom Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_requests')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Filter parameters
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    project_ids = models.JSONField(default=list, blank=True)
    include_charts = models.BooleanField(default=True)
    include_details = models.BooleanField(default=True)
    
    # File information
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report Request'
        verbose_name_plural = 'Report Requests'
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.title} ({self.get_status_display()})"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_processing(self):
        return self.status == 'processing'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    def mark_completed(self, file_path=None, file_size=None):
        self.status = 'completed'
        self.completed_at = timezone.now()
        if file_path:
            self.file_path = file_path
        if file_size:
            self.file_size = file_size
        self.save()
    
    def mark_failed(self):
        self.status = 'failed'
        self.save()
