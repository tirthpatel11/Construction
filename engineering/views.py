from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from projects.models import Project
from .models import (
    Estimation, EstimationItem, ProjectBudget, BudgetItem,
    ProjectSchedule, ScheduleActivity, CostControl
)
from .forms import EstimationForm, EstimationItemFormSet, BudgetForm, BudgetItemFormSet, ScheduleForm, CostControlForm


@login_required
def dashboard(request):
    """Engineering dashboard"""
    from django.db.models import Sum, Count, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    projects = Project.objects.filter(created_by=request.user)
    estimations = Estimation.objects.filter(project__created_by=request.user, is_active=True)
    budgets = ProjectBudget.objects.filter(project__created_by=request.user)
    schedules = ProjectSchedule.objects.filter(project__created_by=request.user)
    
    # Calculate statistics
    total_estimation_value = float(estimations.aggregate(Sum('total_estimated_cost'))['total_estimated_cost__sum'] or 0)
    total_budget_value = float(budgets.aggregate(Sum('total_budget'))['total_budget__sum'] or 0)
    active_projects = projects.filter(status='active').count()
    
    # Schedule statistics
    total_activities = ScheduleActivity.objects.filter(schedule__project__created_by=request.user).count()
    completed_activities = ScheduleActivity.objects.filter(
        schedule__project__created_by=request.user, 
        completion_percentage=100
    ).count()
    schedule_progress = float((completed_activities / total_activities * 100) if total_activities > 0 else 0)
    
    # Recent data
    recent_projects = projects.order_by('-created_at')[:5]
    recent_estimations = estimations.order_by('-created_at')[:5]
    recent_budgets = budgets.order_by('-created_at')[:5]
    
    # Cost analysis data for charts - using real project data
    cost_analysis_data = []
    for project in projects[:5]:  # Top 5 projects
        project_estimations = estimations.filter(project=project)
        project_budgets = budgets.filter(project=project)
        
        # Get estimated cost from estimations
        estimated_cost = project_estimations.aggregate(Sum('total_estimated_cost'))['total_estimated_cost__sum'] or 0
        
        # Get actual cost from project expenses and budgets
        project_expenses = project.expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        budget_actual = project_budgets.aggregate(Sum('total_budget'))['total_budget__sum'] or 0
        actual_cost = max(project_expenses, budget_actual)  # Use the higher value
        
        if estimated_cost > 0 or actual_cost > 0:  # Only include projects with data
            cost_analysis_data.append({
                'project_name': project.name[:20] + '...' if len(project.name) > 20 else project.name,
                'estimated_cost': float(estimated_cost),
                'actual_cost': float(actual_cost)
            })
    
    # Budget utilization data - using real expense categories
    expense_categories = ['materials', 'labor', 'equipment', 'permits', 'utilities', 'subcontractor', 'other']
    budget_utilization_data = []
    
    for category in expense_categories:
        category_expenses = sum([
            project.expenses.filter(category=category).aggregate(Sum('amount'))['amount__sum'] or 0
            for project in projects
        ])
        if category_expenses > 0:
            budget_utilization_data.append({
                'category': category.title(),
                'amount': float(category_expenses)
            })
    
    # If no real data, show default distribution
    if not budget_utilization_data and total_budget_value > 0:
        budget_utilization_data = [
            {'category': 'Labor', 'amount': float(total_budget_value * 0.4)},
            {'category': 'Materials', 'amount': float(total_budget_value * 0.35)},
            {'category': 'Equipment', 'amount': float(total_budget_value * 0.15)},
            {'category': 'Overhead', 'amount': float(total_budget_value * 0.1)}
        ]
    
    import json
    context = {
        'projects': projects,
        'estimations': estimations,
        'budgets': budgets,
        'schedules': schedules,
        'total_estimation_value': total_estimation_value,
        'total_budget_value': total_budget_value,
        'active_projects': active_projects,
        'total_activities': total_activities,
        'completed_activities': completed_activities,
        'schedule_progress': schedule_progress,
        'recent_projects': recent_projects,
        'recent_estimations': recent_estimations,
        'recent_budgets': recent_budgets,
        'cost_analysis_data': json.dumps(cost_analysis_data),
        'budget_utilization_data': json.dumps(budget_utilization_data),
    }
    
    return render(request, 'engineering/dashboard.html', context)


@login_required
def estimation_list(request):
    """List all estimations"""
    estimations = Estimation.objects.filter(project__created_by=request.user).order_by('-created_at')
    
    context = {
        'estimations': estimations,
    }
    
    return render(request, 'engineering/estimation_list.html', context)


@login_required
def estimation_create(request):
    """Create new estimation"""
    if request.method == 'POST':
        form = EstimationForm(request.POST, user=request.user)
        if form.is_valid():
            estimation = form.save(commit=False)
            estimation.created_by = request.user
            estimation.save()
            messages.success(request, 'Estimation created successfully!')
            return redirect('engineering:estimation_detail', estimation_id=estimation.id)
    else:
        form = EstimationForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'engineering/estimation_form.html', context)


@login_required
def estimation_detail(request, estimation_id):
    """Estimation detail view"""
    estimation = get_object_or_404(Estimation, id=estimation_id, project__created_by=request.user)
    items = estimation.items.all()
    
    context = {
        'estimation': estimation,
        'items': items,
    }
    
    return render(request, 'engineering/estimation_detail.html', context)


@login_required
def budget_list(request):
    """List all budgets"""
    budgets = ProjectBudget.objects.filter(project__created_by=request.user).order_by('-created_at')
    
    context = {
        'budgets': budgets,
    }
    
    return render(request, 'engineering/budget_list.html', context)


@login_required
def budget_create(request):
    """Create new budget"""
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.approved_by = request.user
            budget.save()
            messages.success(request, 'Budget created successfully!')
            return redirect('engineering:budget_detail', budget_id=budget.id)
    else:
        form = BudgetForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'engineering/budget_form.html', context)


@login_required
def budget_detail(request, budget_id):
    """Budget detail view"""
    budget = get_object_or_404(ProjectBudget, id=budget_id, project__created_by=request.user)
    items = budget.items.all()
    
    context = {
        'budget': budget,
        'items': items,
    }
    
    return render(request, 'engineering/budget_detail.html', context)


@login_required
def schedule_list(request):
    """List all schedules"""
    schedules = ProjectSchedule.objects.filter(project__created_by=request.user).order_by('-created_at')
    
    context = {
        'schedules': schedules,
    }
    
    return render(request, 'engineering/schedule_list.html', context)


@login_required
def schedule_create(request):
    """Create new schedule"""
    if request.method == 'POST':
        form = ScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            messages.success(request, 'Schedule created successfully!')
            return redirect('engineering:schedule_detail', schedule_id=schedule.id)
    else:
        form = ScheduleForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'engineering/schedule_form.html', context)


@login_required
def schedule_detail(request, schedule_id):
    """Schedule detail view"""
    schedule = get_object_or_404(ProjectSchedule, id=schedule_id, project__created_by=request.user)
    activities = schedule.activities.all()
    
    context = {
        'schedule': schedule,
        'activities': activities,
    }
    
    return render(request, 'engineering/schedule_detail.html', context)


@login_required
def cost_control_list(request):
    """List cost control for all projects"""
    projects = Project.objects.filter(created_by=request.user)
    
    context = {
        'projects': projects,
    }
    
    return render(request, 'engineering/cost_control_list.html', context)


@login_required
def cost_control_detail(request, project_id):
    """Cost control detail for a project"""
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    cost_controls = CostControl.objects.filter(project=project)
    
    context = {
        'project': project,
        'cost_controls': cost_controls,
    }
    
    return render(request, 'engineering/cost_control_detail.html', context)