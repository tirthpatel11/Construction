from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Project, Partner, ProjectExpense, ProjectPayment, ProjectTimeline, ProjectProgressSnapshot
from .forms import ProjectForm, PartnerFormSet, ProjectExpenseForm
from django.db import transaction
from engineering.models import ProjectSchedule, ScheduleActivity
from django.utils import timezone


@login_required
def create_project(request):
    """Create a new project with partners"""
    if request.method == 'POST':
        project_form = ProjectForm(request.POST)
        
        if project_form.is_valid():
            try:
                with transaction.atomic():
                    project = project_form.save(commit=False)
                    project.created_by = request.user
                    project.save()
                    
                    partner_formset = PartnerFormSet(request.POST, instance=project)
                    if partner_formset.is_valid():
                        partner_formset.save()
                        messages.success(request, 'Project created successfully!')
                        return redirect('projects:detail', project_id=project.id)
                    else:
                        messages.error(request, 'Please correct the partner information.')
            except Exception as e:
                messages.error(request, f'Error creating project: {str(e)}')
    else:
        project_form = ProjectForm()
        partner_formset = PartnerFormSet()
    
    context = {
        'project_form': project_form,
        'partner_formset': partner_formset,
    }
    
    return render(request, 'projects/create.html', context)


@login_required
def project_list(request):
    """List all user projects"""
    projects = Project.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'projects': projects,
    }
    
    return render(request, 'projects/list.html', context)


@login_required
def project_detail(request, project_id):
    """Project detail view with analytics"""
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    
    # Get project analytics
    expenses = ProjectExpense.objects.filter(project=project)
    payments = ProjectPayment.objects.filter(project=project)
    timeline_events = ProjectTimeline.objects.filter(project=project)
    # Activities for EVM
    schedules = ProjectSchedule.objects.filter(project=project)
    activities = ScheduleActivity.objects.filter(schedule__in=schedules)
    
    # Calculate basic cost metrics
    total_expenses = sum(expense.amount for expense in expenses)
    total_payments = sum(payment.amount for payment in payments if payment.status == 'completed')
    pending_payments = payments.filter(status='pending')
    
    # Update actual cost
    project.actual_cost = total_expenses
    project.save()
    
    # EVM-based progress calculation
    # Weights by planned duration; EV by completion%; PV by time elapsed vs planned duration
    overall_progress = 0.0
    spi = None
    cpi = None
    if activities.exists():
        planned_total = sum(a.duration_days for a in activities if a.duration_days > 0) or 0
        if planned_total > 0:
            # Earned Value proxy as weighted completion
            earned_weight = 0.0
            planned_weight = 0.0
            today = timezone.now().date()
            for a in activities:
                duration = max(1, a.duration_days)
                weight = duration / planned_total
                earned_weight += weight * (a.completion_percentage / 100.0)
                # Planned value share based on how much of the activity should have been done by today
                if a.planned_start and a.planned_end:
                    total_days = max(1, (a.planned_end - a.planned_start).days)
                    elapsed_days = 0
                    if today >= a.planned_end:
                        elapsed_days = total_days
                    elif today <= a.planned_start:
                        elapsed_days = 0
                    else:
                        elapsed_days = (today - a.planned_start).days
                    planned_completion = min(1.0, max(0.0, elapsed_days / total_days))
                    planned_weight += weight * planned_completion
            overall_progress = round(earned_weight * 100.0, 1)
            # SPI as EV/PV; use small epsilon
            epsilon = 1e-6
            spi = round((earned_weight + epsilon) / (planned_weight + epsilon), 2)
    else:
        # Fallback: cost-based progress if no activities configured
        if project.estimated_budget and project.estimated_budget > 0:
            overall_progress = round(min(100.0, (float(project.actual_cost) / float(project.estimated_budget)) * 100.0), 1)
    
    # CPI as Budgeted/Actual for completed work if available
    if project.actual_cost and project.actual_cost > 0 and project.estimated_budget and project.estimated_budget > 0:
        cpi = round(float(project.estimated_budget) / float(project.actual_cost), 2)
    
    context = {
        'project': project,
        'partners': project.partners.all(),
        'expenses': expenses,
        'payments': payments,
        'timeline_events': timeline_events,
        'total_expenses': total_expenses,
        'total_payments': total_payments,
        'pending_payments': pending_payments,
        'profit_margin': project.profit_margin,
        'overall_progress': overall_progress,
        'spi': spi,
        'cpi': cpi,
        'progress_spark': list(ProjectProgressSnapshot.objects.filter(project=project).order_by('-snapshot_date')[:14].values_list('progress_percent', flat=True))[::-1],
    }
    
    return render(request, 'projects/detail.html', context)


@login_required
def edit_project(request, project_id):
    """Edit an existing project with partners"""
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    if request.method == 'POST':
        project_form = ProjectForm(request.POST, instance=project)
        partner_formset = PartnerFormSet(request.POST, instance=project)
        if project_form.is_valid() and partner_formset.is_valid():
            try:
                with transaction.atomic():
                    project_form.save()
                    partner_formset.save()
                    messages.success(request, 'Project updated successfully!')
                    return redirect('projects:detail', project_id=project.id)
            except Exception as e:
                messages.error(request, f'Error updating project: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        project_form = ProjectForm(instance=project)
        partner_formset = PartnerFormSet(instance=project)
    return render(request, 'projects/create.html', {
        'project_form': project_form,
        'partner_formset': partner_formset,
        'project': project,
        'is_edit': True,
    })


@login_required
def delete_project(request, project_id):
    """Delete a project (POST confirms)."""
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully!')
        return redirect('projects:list')
    return render(request, 'projects/confirm_delete.html', {
        'project': project,
    })


@login_required
def project_analytics(request, project_id):
    """API endpoint for project-specific analytics"""
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    
    # Expense breakdown by category
    expenses = ProjectExpense.objects.filter(project=project)
    expense_breakdown = {}
    for expense in expenses:
        category = expense.get_category_display()
        expense_breakdown[category] = expense_breakdown.get(category, 0) + float(expense.amount)
    
    # Timeline data
    timeline_data = []
    for event in project.timeline_events.all():
        timeline_data.append({
            'title': event.title,
            'date': event.date.isoformat(),
            'is_milestone': event.is_milestone,
            'is_completed': event.is_completed,
        })
    
    return JsonResponse({
        'expense_breakdown': expense_breakdown,
        'timeline_data': timeline_data,
        'completion_percentage': project.completion_percentage,
        'budget_utilization': float(project.actual_cost / project.estimated_budget * 100) if project.estimated_budget > 0 else 0,
    })


@login_required
def expense_create(request, project_id):
    """Create a new expense for a project"""
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    if request.method == 'POST':
        form = ProjectExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.project = project
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('projects:detail', project_id=project.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectExpenseForm()
    return render(request, 'projects/expense_form.html', {
        'project': project,
        'form': form,
        'is_edit': False,
    })


@login_required
def expense_edit(request, project_id, expense_id):
    """Edit an existing expense"""
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    expense = get_object_or_404(ProjectExpense, id=expense_id, project=project)
    if request.method == 'POST':
        form = ProjectExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('projects:detail', project_id=project.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectExpenseForm(instance=expense)
    return render(request, 'projects/expense_form.html', {
        'project': project,
        'form': form,
        'is_edit': True,
        'expense': expense,
    })


@login_required
def expense_delete(request, project_id, expense_id):
    """Delete an expense (POST only)"""
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    expense = get_object_or_404(ProjectExpense, id=expense_id, project=project)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('projects:detail', project_id=project.id)
    # For non-POST requests, redirect back without action
    return redirect('projects:detail', project_id=project.id)