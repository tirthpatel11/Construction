from django.contrib import admin
from .models import ReportRequest

@admin.register(ReportRequest)
class ReportRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'report_type', 'format', 'status', 'created_at']
    list_filter = ['report_type', 'format', 'status', 'created_at']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'report_type', 'format', 'status')
        }),
        ('Filter Parameters', {
            'fields': ('date_from', 'date_to', 'project_ids', 'include_charts', 'include_details')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
