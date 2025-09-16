from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date


class Project(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    project_address = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    estimated_budget = models.DecimalField(max_digits=15, decimal_places=2)
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    completion_percentage = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.company_name}"
    
    @property
    def budget_variance(self):
        return float(self.actual_cost - self.estimated_budget)
    
    @property
    def profit_margin(self):
        if self.estimated_budget > 0:
            return ((self.estimated_budget - self.actual_cost) / self.estimated_budget) * 100
        return 0


class Partner(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='partners')
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    proportion = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage (0-100)")
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.project.name}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))


class ProjectExpense(models.Model):
    CATEGORY_CHOICES = [
        ('materials', 'Materials'),
        ('labor', 'Labor'),
        ('equipment', 'Equipment'),
        ('permits', 'Permits'),
        ('utilities', 'Utilities'),
        ('subcontractor', 'Subcontractor'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.project.name} - {self.category} - ₹{self.amount}"


class ProjectPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payments')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    client_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.project.name} - Payment - ₹{self.amount}"


class ProjectTimeline(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='timeline_events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date = models.DateField()
    is_milestone = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        return f"{self.project.name} - {self.title}"


class ProjectProgressSnapshot(models.Model):
    """Daily snapshot of computed project progress and EVM metrics."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='progress_snapshots')
    snapshot_date = models.DateField(default=timezone.now)
    progress_percent = models.DecimalField(max_digits=6, decimal_places=2)
    spi = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cpi = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'snapshot_date')
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"{self.project.name} - {self.snapshot_date} - {self.progress_percent}%"