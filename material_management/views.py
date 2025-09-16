from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, F
from projects.models import Project
from .models import (
    Supplier, Material, MaterialStock, MaterialTransaction,
    PurchaseOrder, MaterialRequisition
)
from .forms import (
    SupplierForm, MaterialForm, PurchaseOrderForm, PurchaseOrderItemFormSet,
    MaterialRequisitionForm, MaterialRequisitionItemFormSet
)


@login_required
def dashboard(request):
    """Material Management dashboard"""
    from django.utils import timezone
    from datetime import timedelta
    
    projects = Project.objects.filter(created_by=request.user)
    suppliers = Supplier.objects.filter(is_active=True)
    materials = Material.objects.filter(is_active=True)
    purchase_orders = PurchaseOrder.objects.filter(project__created_by=request.user)
    requisitions = MaterialRequisition.objects.filter(project__created_by=request.user)
    
    # Calculate statistics
    total_suppliers = suppliers.count()
    total_materials = materials.count()
    # Calculate inventory value from stock records
    total_inventory_value = MaterialStock.objects.filter(
        project__created_by=request.user
    ).aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_po_value = purchase_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Monthly statistics
    current_month = timezone.now().replace(day=1)
    new_suppliers_this_month = suppliers.filter(created_at__gte=current_month).count()
    
    # Stock level statistics - simplified for now
    low_stock_materials = materials.filter(reorder_level__gt=0).count()  # Simplified
    in_stock_materials = materials.count() - low_stock_materials
    stock_health_score = (in_stock_materials / total_materials * 100) if total_materials > 0 else 0
    
    # Requisition statistics
    pending_requisitions = requisitions.filter(status='pending').count()
    
    # Recent data
    recent_purchase_orders = purchase_orders.order_by('-created_at')[:5]
    
    # Inventory analysis data for charts
    inventory_analysis_data = []
    for i in range(6):
        month_date = timezone.now() - timedelta(days=30*i)
        month_name = month_date.strftime('%b %Y')
        
        # Get real material transactions for the month
        month_transactions = MaterialTransaction.objects.filter(
            project__created_by=request.user,
            transaction_date__year=month_date.year,
            transaction_date__month=month_date.month
        )
        
        # Calculate consumed materials (stock out)
        consumed = month_transactions.filter(transaction_type='out').aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        # Calculate received materials (stock in)
        received = month_transactions.filter(transaction_type='in').aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        # Calculate current stock level
        stock_level = MaterialStock.objects.filter(
            project__created_by=request.user,
            received_date__lte=month_date
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        inventory_analysis_data.append({
            'month': month_name,
            'consumed': float(consumed),
            'received': float(received),
            'stock_level': float(stock_level)
        })
    
    inventory_analysis_data.reverse()  # Show oldest to newest
    
    # Material categories data
    material_categories_data = [
        {'category': 'Steel', 'count': materials.filter(category__name__icontains='steel').count()},
        {'category': 'Cement', 'count': materials.filter(category__name__icontains='cement').count()},
        {'category': 'Bricks', 'count': materials.filter(category__name__icontains='brick').count()},
        {'category': 'Electrical', 'count': materials.filter(category__name__icontains='electrical').count()},
        {'category': 'Plumbing', 'count': materials.filter(category__name__icontains='plumbing').count()},
        {'category': 'Other', 'count': materials.exclude(category__name__icontains='steel').exclude(category__name__icontains='cement').exclude(category__name__icontains='brick').exclude(category__name__icontains='electrical').exclude(category__name__icontains='plumbing').count()}
    ]
    
    # Top suppliers performance - using real data
    top_suppliers = []
    for supplier in suppliers[:5]:
        supplier_pos = purchase_orders.filter(supplier=supplier)
        
        # Calculate real performance metrics
        total_pos = supplier_pos.count()
        completed_pos = supplier_pos.filter(status='completed').count()
        total_value = supplier_pos.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Calculate performance score based on completion rate and value
        completion_rate = (completed_pos / total_pos * 100) if total_pos > 0 else 0
        value_score = min(100, (float(total_value) / 100000) * 10)  # Scale based on total value
        performance_score = (completion_rate * 0.7) + (value_score * 0.3)
        
        top_suppliers.append({
            'name': supplier.name,
            'performance_score': float(performance_score),
            'total_orders': total_pos,
            'completed_orders': completed_pos,
            'total_value': float(total_value)
        })
    
    # Calculate average delivery time from purchase orders
    completed_pos = purchase_orders.filter(status='completed')
    if completed_pos.exists():
        delivery_times = []
        for po in completed_pos:
            if po.expected_delivery_date and po.created_at:
                delivery_days = (po.expected_delivery_date - po.created_at.date()).days
                if delivery_days > 0:
                    delivery_times.append(delivery_days)
        avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 7
    else:
        avg_delivery_time = 7  # Default if no completed orders
    
    context = {
        'projects': projects,
        'suppliers': suppliers,
        'materials': materials,
        'purchase_orders': purchase_orders,
        'requisitions': requisitions,
        'total_suppliers': total_suppliers,
        'total_materials': total_materials,
        'total_inventory_value': total_inventory_value,
        'total_po_value': total_po_value,
        'new_suppliers_this_month': new_suppliers_this_month,
        'low_stock_materials': low_stock_materials,
        'in_stock_materials': in_stock_materials,
        'stock_health_score': stock_health_score,
        'pending_requisitions': pending_requisitions,
        'recent_purchase_orders': recent_purchase_orders,
        'inventory_analysis_data': inventory_analysis_data,
        'material_categories_data': material_categories_data,
        'top_suppliers': top_suppliers,
        'avg_delivery_time': avg_delivery_time,
    }
    
    return render(request, 'material_management/dashboard.html', context)


@login_required
def supplier_list(request):
    """List all suppliers"""
    suppliers = Supplier.objects.all().order_by('name')
    
    context = {
        'suppliers': suppliers,
    }
    
    return render(request, 'material_management/supplier_list.html', context)


@login_required
def supplier_create(request):
    """Create new supplier"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier created successfully!')
            return redirect('material_management:supplier_list')
    else:
        form = SupplierForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'material_management/supplier_form.html', context)


@login_required
def supplier_detail(request, supplier_id):
    """Supplier detail view"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    purchase_orders = PurchaseOrder.objects.filter(supplier=supplier)
    
    context = {
        'supplier': supplier,
        'purchase_orders': purchase_orders,
    }
    
    return render(request, 'material_management/supplier_detail.html', context)


@login_required
def material_list(request):
    """List all materials"""
    materials = Material.objects.all().order_by('name')
    
    context = {
        'materials': materials,
    }
    
    return render(request, 'material_management/material_list.html', context)


@login_required
def material_create(request):
    """Create new material"""
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material created successfully!')
            return redirect('material_management:material_list')
    else:
        form = MaterialForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'material_management/material_form.html', context)


@login_required
def material_detail(request, material_id):
    """Material detail view"""
    material = get_object_or_404(Material, id=material_id)
    stock = MaterialStock.objects.filter(material=material)
    transactions = MaterialTransaction.objects.filter(material=material)
    
    context = {
        'material': material,
        'stock': stock,
        'transactions': transactions,
    }
    
    return render(request, 'material_management/material_detail.html', context)


@login_required
def inventory_list(request):
    """List inventory for all projects"""
    projects = Project.objects.filter(created_by=request.user)
    
    context = {
        'projects': projects,
    }
    
    return render(request, 'material_management/inventory_list.html', context)


@login_required
def inventory_detail(request, project_id):
    """Inventory detail for a project"""
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    stock = MaterialStock.objects.filter(project=project)
    
    context = {
        'project': project,
        'stock': stock,
    }
    
    return render(request, 'material_management/inventory_detail.html', context)


@login_required
def purchase_order_list(request):
    """List all purchase orders"""
    purchase_orders = PurchaseOrder.objects.filter(project__created_by=request.user).order_by('-created_at')
    
    context = {
        'purchase_orders': purchase_orders,
    }
    
    return render(request, 'material_management/purchase_order_list.html', context)


@login_required
def purchase_order_create(request):
    """Create new purchase order"""
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, user=request.user)
        if form.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()
            messages.success(request, 'Purchase order created successfully!')
            return redirect('material_management:purchase_order_detail', po_id=po.id)
    else:
        form = PurchaseOrderForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'material_management/purchase_order_form.html', context)


@login_required
def purchase_order_detail(request, po_id):
    """Purchase order detail view"""
    po = get_object_or_404(PurchaseOrder, id=po_id, project__created_by=request.user)
    items = po.items.all()
    
    context = {
        'purchase_order': po,
        'items': items,
    }
    
    return render(request, 'material_management/purchase_order_detail.html', context)


@login_required
def requisition_list(request):
    """List all material requisitions"""
    requisitions = MaterialRequisition.objects.filter(project__created_by=request.user).order_by('-requested_date')
    
    context = {
        'requisitions': requisitions,
    }
    
    return render(request, 'material_management/requisition_list.html', context)


@login_required
def requisition_create(request):
    """Create new material requisition"""
    if request.method == 'POST':
        form = MaterialRequisitionForm(request.POST, user=request.user)
        if form.is_valid():
            req = form.save(commit=False)
            req.requested_by = request.user
            req.save()
            messages.success(request, 'Material requisition created successfully!')
            return redirect('material_management:requisition_detail', req_id=req.id)
    else:
        form = MaterialRequisitionForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'material_management/requisition_form.html', context)


@login_required
def requisition_detail(request, req_id):
    """Material requisition detail view"""
    req = get_object_or_404(MaterialRequisition, id=req_id, project__created_by=request.user)
    items = req.items.all()
    
    context = {
        'requisition': req,
        'items': items,
    }
    
    return render(request, 'material_management/requisition_detail.html', context)