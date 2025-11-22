from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from projects.models import Project, Partner, ProjectExpense, ProjectPayment
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json


@login_required
def home(request):
    """Main dashboard view with analytics"""
    user_projects = Project.objects.filter(created_by=request.user)
    
    # Project statistics
    total_projects = user_projects.count()
    active_projects = user_projects.filter(status='active').count()
    completed_projects = user_projects.filter(status='completed').count()
    
    # Budget analytics
    total_budget = user_projects.aggregate(Sum('estimated_budget'))['estimated_budget__sum'] or 0
    total_spent = ProjectExpense.objects.filter(project__in=user_projects).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Recent projects
    recent_projects = user_projects.order_by('-created_at')[:5]
    
    # Upcoming payments
    upcoming_payments = ProjectPayment.objects.filter(
        project__in=user_projects,
        due_date__gte=timezone.now(),
        status='pending'
    ).order_by('due_date')[:5]
    
    # Cash flow data for chart (last 6 months)
    cash_flow_data = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        income = ProjectPayment.objects.filter(
            project__in=user_projects,
            payment_date__range=[month_start, month_end],
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        expenses = ProjectExpense.objects.filter(
            project__in=user_projects,
            date__range=[month_start, month_end]
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        cash_flow_data.append({
            'month': month_start.strftime('%b %Y'),
            'income': float(income),
            'expenses': float(expenses),
            'net': float(income - expenses)
        })
    
    cash_flow_data.reverse()
    
    # Cost breakdown data (coerce Decimal -> float for JSON)
    cost_breakdown_qs = ProjectExpense.objects.filter(
        project__in=user_projects
    ).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    cost_breakdown = [
        {
            'category': row['category'],
            'total': float(row['total'] or 0)
        }
        for row in cost_breakdown_qs
    ]
    
    context = {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'budget_utilization': (total_spent / total_budget * 100) if total_budget > 0 else 0,
        'recent_projects': recent_projects,
        'upcoming_payments': upcoming_payments,
        'cash_flow_data': json.dumps(cash_flow_data),
        'cost_breakdown': json.dumps(cost_breakdown),
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def project_selection(request):
    """Project selection page with comprehensive project analytics"""
    user_projects = Project.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Calculate basic project statistics
    total_projects = user_projects.count()
    active_projects = user_projects.filter(status='active').count()
    total_budget = user_projects.aggregate(total=Sum('estimated_budget'))['total'] or 0
    avg_progress = user_projects.aggregate(avg=Avg('completion_percentage'))['avg'] or 0
    
    # Calculate advanced analytics
    completed_projects = user_projects.filter(status='completed').count()
    completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
    
    # Calculate on-time rate (projects completed within estimated time)
    on_time_projects = user_projects.filter(
        status='completed',
        completion_percentage=100
    ).count()
    on_time_rate = (on_time_projects / completed_projects * 100) if completed_projects > 0 else 0
    
    # Calculate budget utilization
    total_actual_cost = user_projects.aggregate(total=Sum('actual_cost'))['total'] or 0
    budget_utilization = (total_actual_cost / total_budget * 100) if total_budget > 0 else 0
    
    # Calculate project velocity (average progress per month)
    from datetime import datetime, timedelta
    six_months_ago = timezone.now() - timedelta(days=180)
    recent_projects = user_projects.filter(created_at__gte=six_months_ago)
    project_velocity = recent_projects.aggregate(avg=Avg('completion_percentage'))['avg'] or 0
    
    # Risk assessment
    budget_risk = 'low'
    if budget_utilization > 90:
        budget_risk = 'high'
    elif budget_utilization > 70:
        budget_risk = 'medium'
    
    schedule_risk = 'low'
    if avg_progress < 30:
        schedule_risk = 'high'
    elif avg_progress < 60:
        schedule_risk = 'medium'
    
    resource_risk = 'low'
    if active_projects > 5:
        resource_risk = 'high'
    elif active_projects > 3:
        resource_risk = 'medium'
    
    # Top performers (projects with highest completion percentage)
    top_performers = user_projects.filter(completion_percentage__gt=0).order_by('-completion_percentage')
    
    context = {
        'projects': user_projects,
        'active_projects': active_projects,
        'total_budget': total_budget,
        'avg_progress': avg_progress,
        'completion_rate': completion_rate,
        'on_time_rate': on_time_rate,
        'budget_utilization': budget_utilization,
        'project_velocity': project_velocity,
        'budget_risk': budget_risk,
        'schedule_risk': schedule_risk,
        'resource_risk': resource_risk,
        'top_performers': top_performers,
    }
    
    return render(request, 'dashboard/project_selection.html', context)


@login_required
def analytics_data(request):
    """API endpoint for dashboard analytics data"""
    user_projects = Project.objects.filter(created_by=request.user)
    
    # Project completion data
    completion_data = []
    for project in user_projects:
        completion_data.append({
            'name': project.name,
            'completion': project.completion_percentage,
            'status': project.status
        })
    
    # Resource utilization (real data based on project expenses)
    resource_data = []
    resources = ['Labor', 'Materials', 'Equipment', 'Subcontractors']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    
    # Get actual expense data for resource utilization
    for resource in resources:
        for i, month in enumerate(months):
            # Calculate utilization based on actual expenses
            month_start = timezone.now().replace(day=1) - timedelta(days=30*(5-i))
            month_end = month_start + timedelta(days=30)
            
            # Map resource categories to expense categories
            category_mapping = {
                'Labor': 'labor',
                'Materials': 'materials', 
                'Equipment': 'equipment',
                'Subcontractors': 'subcontractor'
            }
            
            expenses = ProjectExpense.objects.filter(
                project__in=user_projects,
                category=category_mapping[resource],
                date__range=[month_start, month_end]
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Calculate utilization percentage (assuming max budget per resource per month)
            max_budget = 50000  # This could be made dynamic based on project budgets
            utilization = min(100, (float(expenses) / max_budget) * 100) if max_budget > 0 else 0
            
            resource_data.append({
                'resource': resource,
                'month': month,
                'utilization': round(utilization, 1)
            })
    
    return JsonResponse({
        'completion_data': completion_data,
        'resource_data': resource_data,
    })


@login_required
def settings_view(request):
    """Settings page for appearance and account management."""
    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'appearance')
        
        if form_type == 'appearance':
            # Handle appearance settings
            theme = request.POST.get('theme', 'light')
            currency = request.POST.get('currency', 'INR')
            request.session['ui_theme'] = theme
            request.session['currency'] = currency
            request.session.modified = True  # Ensure session is saved
            messages.success(request, f'Appearance settings saved successfully! Theme: {theme}, Currency: {currency}')
            
        elif form_type == 'account':
            # Handle account changes
            user = request.user
            user_changed = False
            
            # Update email if provided
            new_email = request.POST.get('email', '').strip()
            if new_email and new_email != user.email:
                # Validate email format
                try:
                    validate_email(new_email)
                    # Check if email is already taken
                    if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                        messages.error(request, 'This email is already registered. Please use a different email.')
                    else:
                        user.email = new_email
                        user_changed = True
                        messages.success(request, 'Email updated successfully!')
                except ValidationError:
                    messages.error(request, 'Please enter a valid email address.')
            
            # Update password if provided
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if new_password:
                if not current_password:
                    messages.error(request, 'Please enter your current password to change it.')
                elif not user.check_password(current_password):
                    messages.error(request, 'Current password is incorrect.')
                elif new_password != confirm_password:
                    messages.error(request, 'New password and confirm password do not match.')
                elif len(new_password) < 8:
                    messages.error(request, 'Password must be at least 8 characters long.')
                else:
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)  # Keep user logged in
                    messages.success(request, 'Password changed successfully!')
                    user_changed = False  # Already saved above
            
            # Save user changes if email was updated
            if user_changed:
                user.save()
        
        return redirect('dashboard:settings')
    
    context = {
        'theme': request.session.get('ui_theme', 'light'),
        'currency': request.session.get('currency', 'INR'),
    }
    return render(request, 'dashboard/settings.html', context)