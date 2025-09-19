from django import template
from projects.models import Project

register = template.Library()

@register.simple_tag
def get_recent_projects(user, limit=5):
    """Get recent projects for a user"""
    return Project.objects.filter(created_by=user).order_by('-created_at')[:limit]
