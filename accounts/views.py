from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum
from projects.models import Project
from .models import (
    ChartOfAccounts, JournalEntry, JournalEntryLine, Budget, BudgetItem,
    TrialBalance, TrialBalanceItem, ProfitLossStatement, BalanceSheet, CashFlow
)
from .forms import (
    ChartOfAccountsForm, JournalEntryForm, JournalEntryLineFormSet,
    BudgetForm, BudgetItemFormSet
)


@login_required
def dashboard(request):
    """Accounts dashboard"""
    from django.utils import timezone
    from datetime import timedelta, datetime
    
    projects = Project.objects.filter(created_by=request.user)
    recent_entries = JournalEntry.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    budgets = Budget.objects.filter(approved_by=request.user)
    
    # Calculate totals
    total_debit = JournalEntry.objects.filter(created_by=request.user).aggregate(Sum('total_debit'))['total_debit__sum'] or 0
    total_credit = JournalEntry.objects.filter(created_by=request.user).aggregate(Sum('total_credit'))['total_credit__sum'] or 0
    net_balance = total_debit - total_credit
    
    # Monthly statistics
    current_month = timezone.now().replace(day=1)
    monthly_entries = JournalEntry.objects.filter(
        created_by=request.user,
        entry_date__gte=current_month
    ).count()
    
    monthly_debit = JournalEntry.objects.filter(
        created_by=request.user,
        entry_date__gte=current_month
    ).aggregate(Sum('total_debit'))['total_debit__sum'] or 0
    
    monthly_credit = JournalEntry.objects.filter(
        created_by=request.user,
        entry_date__gte=current_month
    ).aggregate(Sum('total_credit'))['total_credit__sum'] or 0
    
    # Budget statistics
    total_budget_value = budgets.aggregate(Sum('total_budget'))['total_budget__sum'] or 0
    budget_used = total_debit  # Simplified: using total debit as budget used
    budget_remaining = total_budget_value - budget_used
    budget_utilization = (budget_used / total_budget_value * 100) if total_budget_value > 0 else 0
    
    # Account statistics
    accounts_count = ChartOfAccounts.objects.filter(is_active=True).count()
    pending_entries = JournalEntry.objects.filter(
        created_by=request.user,
        is_posted=False
    ).count()
    
    # Cash flow data for charts
    cash_flow_data = []
    for i in range(6):
        month_date = timezone.now() - timedelta(days=30*i)
        month_name = month_date.strftime('%b %Y')
        
        # Get income from credit entries (posted entries only)
        month_income = JournalEntry.objects.filter(
            created_by=request.user,
            entry_date__year=month_date.year,
            entry_date__month=month_date.month,
            total_credit__gt=0,
            is_posted=True
        ).aggregate(Sum('total_credit'))['total_credit__sum'] or 0
        
        # Get expenses from debit entries (posted entries only)
        month_expenses = JournalEntry.objects.filter(
            created_by=request.user,
            entry_date__year=month_date.year,
            entry_date__month=month_date.month,
            total_debit__gt=0,
            is_posted=True
        ).aggregate(Sum('total_debit'))['total_debit__sum'] or 0
        
        cash_flow_data.append({
            'month': month_name,
            'income': float(month_income),
            'expenses': float(month_expenses),
            'net': float(month_income - month_expenses)
        })
    
    cash_flow_data.reverse()  # Show oldest to newest
    
    # Account balance data - using real account balances
    account_balance_data = []
    account_types = ['asset', 'liability', 'equity', 'income', 'expense']
    
    for account_type in account_types:
        # Get balance for each account type
        accounts = ChartOfAccounts.objects.filter(account_type=account_type, is_active=True)
        total_balance = 0
        
        for account in accounts:
            # Get debit balance
            debit_balance = JournalEntryLine.objects.filter(
                account=account,
                journal_entry__created_by=request.user,
                journal_entry__is_posted=True
            ).aggregate(Sum('debit_amount'))['debit_amount__sum'] or 0
            
            # Get credit balance
            credit_balance = JournalEntryLine.objects.filter(
                account=account,
                journal_entry__created_by=request.user,
                journal_entry__is_posted=True
            ).aggregate(Sum('credit_amount'))['credit_amount__sum'] or 0
            
            # Calculate net balance
            if account_type in ['asset', 'expense']:
                balance = debit_balance - credit_balance
            else:  # liability, equity, income
                balance = credit_balance - debit_balance
            
            total_balance += balance
        
        if total_balance != 0:
            account_balance_data.append({
                'account_type': account_type.title(),
                'balance': float(total_balance)
            })
    
    # If no real data, show default distribution
    if not account_balance_data:
        account_balance_data = [
            {'account_type': 'Assets', 'balance': float(total_debit * 0.6)},
            {'account_type': 'Liabilities', 'balance': float(total_credit * 0.4)},
            {'account_type': 'Equity', 'balance': float(total_credit * 0.3)},
            {'account_type': 'Revenue', 'balance': float(total_credit * 0.2)},
            {'account_type': 'Expenses', 'balance': float(total_debit * 0.4)}
        ]
    
    context = {
        'projects': projects,
        'recent_entries': recent_entries,
        'budgets': budgets,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'net_balance': net_balance,
        'monthly_entries': monthly_entries,
        'monthly_debit': monthly_debit,
        'monthly_credit': monthly_credit,
        'total_budget_value': total_budget_value,
        'budget_used': budget_used,
        'budget_remaining': budget_remaining,
        'budget_utilization': budget_utilization,
        'accounts_count': accounts_count,
        'pending_entries': pending_entries,
        'cash_flow_data': cash_flow_data,
        'account_balance_data': account_balance_data,
    }
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def chart_of_accounts(request):
    """Chart of accounts view"""
    accounts = ChartOfAccounts.objects.filter(is_active=True).order_by('account_code')
    
    context = {
        'accounts': accounts,
    }
    
    return render(request, 'accounts/chart_of_accounts.html', context)


@login_required
def journal_entry_list(request):
    """List all journal entries"""
    entries = JournalEntry.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'entries': entries,
    }
    
    return render(request, 'accounts/journal_entry_list.html', context)


@login_required
def journal_entry_create(request):
    """Create new journal entry"""
    if request.method == 'POST':
        form = JournalEntryForm(request.POST, user=request.user)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.save()
            messages.success(request, 'Journal entry created successfully!')
            return redirect('accounts:journal_entry_detail', entry_id=entry.id)
    else:
        form = JournalEntryForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/journal_entry_form.html', context)


@login_required
def journal_entry_detail(request, entry_id):
    """Journal entry detail view"""
    entry = get_object_or_404(JournalEntry, id=entry_id, created_by=request.user)
    lines = entry.journal_lines.all()
    
    context = {
        'entry': entry,
        'lines': lines,
    }
    
    return render(request, 'accounts/journal_entry_detail.html', context)


@login_required
def budget_list(request):
    """List all budgets"""
    budgets = Budget.objects.filter(approved_by=request.user).order_by('-created_at')
    
    context = {
        'budgets': budgets,
    }
    
    return render(request, 'accounts/budget_list.html', context)


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
            return redirect('accounts:budget_detail', budget_id=budget.id)
    else:
        form = BudgetForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/budget_form.html', context)


@login_required
def budget_detail(request, budget_id):
    """Budget detail view"""
    budget = get_object_or_404(Budget, id=budget_id, approved_by=request.user)
    items = budget.items.all()
    
    context = {
        'budget': budget,
        'items': items,
    }
    
    return render(request, 'accounts/budget_detail.html', context)


@login_required
def trial_balance(request):
    """Trial balance view"""
    # This would typically generate trial balance from journal entries
    # For now, showing a placeholder
    accounts = ChartOfAccounts.objects.filter(is_active=True)
    
    context = {
        'accounts': accounts,
    }
    
    return render(request, 'accounts/trial_balance.html', context)


@login_required
def profit_loss(request):
    """Profit & Loss statement view"""
    # This would typically generate P&L from journal entries
    # For now, showing a placeholder
    context = {}
    
    return render(request, 'accounts/profit_loss.html', context)


@login_required
def balance_sheet(request):
    """Balance sheet view"""
    # This would typically generate balance sheet from journal entries
    # For now, showing a placeholder
    context = {}
    
    return render(request, 'accounts/balance_sheet.html', context)


@login_required
def cash_flow(request):
    """Cash flow statement view"""
    # This would typically generate cash flow from journal entries
    # For now, showing a placeholder
    context = {}
    
    return render(request, 'accounts/cash_flow.html', context)