from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg
from projects.models import Project
from .models import (
    Building, Wing, UnitType, SalableUnit, ParkingUnit, PriceList,
    Customer, SaleBooking, PaymentSchedule, Payment, SalesReport
)
from .forms import (
    BuildingForm, SalableUnitForm, CustomerForm, SaleBookingForm,
    PaymentScheduleFormSet, PriceListForm, PaymentForm
)


@login_required
def dashboard(request):
    """Sales dashboard"""
    from django.utils import timezone
    from datetime import timedelta
    
    projects = Project.objects.filter(created_by=request.user)
    buildings = Building.objects.filter(project__created_by=request.user)
    units = SalableUnit.objects.filter(project__created_by=request.user)
    customers = Customer.objects.all()
    bookings = SaleBooking.objects.filter(sales_person=request.user)
    
    # Calculate totals
    total_units = units.count()
    sold_units = units.filter(status='sold').count()
    booked_units = units.filter(status='booked').count()
    available_units = units.filter(status='available').count()
    
    total_sales_value = float(bookings.aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0)
    total_collection = float(Payment.objects.filter(booking__sales_person=request.user, status='paid').aggregate(Sum('amount'))['amount__sum'] or 0)
    
    # Calculate conversion rates
    sales_conversion_rate = float((sold_units / total_units * 100) if total_units > 0 else 0)
    booking_conversion_rate = float((booked_units / total_units * 100) if total_units > 0 else 0)
    conversion_rate = float((sold_units / (sold_units + booked_units) * 100) if (sold_units + booked_units) > 0 else 0)
    
    # Monthly statistics
    current_month = timezone.now().replace(day=1)
    new_customers_this_month = customers.filter(created_at__gte=current_month).count()
    active_customers = customers.filter(bookings__isnull=False).distinct().count()
    
    # Average booking value
    avg_booking_value = float(bookings.aggregate(Avg('agreement_value'))['agreement_value__avg'] or 0)
    
    # Revenue targets and achievement
    revenue_target = total_sales_value * 1.2  # 20% above current sales
    revenue_achievement = float((total_collection / revenue_target * 100) if revenue_target > 0 else 0)
    
    # Recent data
    recent_bookings = bookings.order_by('-created_at')[:5]
    
    # Sales performance data for charts - using real booking data
    sales_performance_data = []
    for i in range(6):
        month_date = timezone.now() - timedelta(days=30*i)
        month_name = month_date.strftime('%b %Y')
        
        month_bookings = bookings.filter(
            booking_date__year=month_date.year,
            booking_date__month=month_date.month
        )
        
        # Count actual sales (confirmed bookings)
        units_sold = month_bookings.filter(status='confirmed').count()
        
        # Get revenue from confirmed bookings
        revenue = month_bookings.filter(status='confirmed').aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0
        
        # Get collection from payments
        month_payments = Payment.objects.filter(
            booking__in=month_bookings,
            status='paid',
            payment_date__year=month_date.year,
            payment_date__month=month_date.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        sales_performance_data.append({
            'month': month_name,
            'units_sold': units_sold,
            'revenue': float(revenue),
            'collection': float(month_payments)
        })
    
    sales_performance_data.reverse()  # Show oldest to newest
    
    # Unit status data
    unit_status_data = [
        {'status': 'Sold', 'count': sold_units},
        {'status': 'Booked', 'count': booked_units},
        {'status': 'Available', 'count': available_units},
        {'status': 'Reserved', 'count': units.filter(status='reserved').count()}
    ]
    
    # Top performing buildings
    top_buildings = []
    for building in buildings[:5]:
        building_units = units.filter(building=building)
        occupied_units = building_units.filter(status__in=['sold', 'booked']).count()
        occupancy_rate = (occupied_units / building_units.count() * 100) if building_units.count() > 0 else 0
        
        top_buildings.append({
            'name': building.name,
            'occupancy_rate': float(occupancy_rate)
        })
    
    context = {
        'projects': projects,
        'buildings': buildings,
        'units': units,
        'customers': customers,
        'bookings': bookings,
        'total_units': total_units,
        'sold_units': sold_units,
        'booked_units': booked_units,
        'available_units': available_units,
        'total_sales_value': total_sales_value,
        'total_collection': total_collection,
        'sales_conversion_rate': sales_conversion_rate,
        'booking_conversion_rate': booking_conversion_rate,
        'conversion_rate': conversion_rate,
        'new_customers_this_month': new_customers_this_month,
        'active_customers': active_customers,
        'avg_booking_value': avg_booking_value,
        'revenue_target': revenue_target,
        'revenue_achievement': revenue_achievement,
        'recent_bookings': recent_bookings,
        'sales_performance_data': sales_performance_data,
        'unit_status_data': unit_status_data,
        'top_buildings': top_buildings,
    }
    
    return render(request, 'sales/dashboard.html', context)


@login_required
def building_list(request):
    """List all buildings"""
    buildings = Building.objects.filter(project__created_by=request.user).order_by('name')
    
    context = {
        'buildings': buildings,
    }
    
    return render(request, 'sales/building_list.html', context)


@login_required
def building_create(request):
    """Create new building"""
    if request.method == 'POST':
        form = BuildingForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Building created successfully!')
            return redirect('sales:building_list')
    else:
        form = BuildingForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'sales/building_form.html', context)


@login_required
def building_detail(request, building_id):
    """Building detail view"""
    building = get_object_or_404(Building, id=building_id, project__created_by=request.user)
    units = building.units.all()
    wings = building.wings.all()
    
    context = {
        'building': building,
        'units': units,
        'wings': wings,
    }
    
    return render(request, 'sales/building_detail.html', context)


@login_required
def unit_list(request):
    """List all salable units"""
    units = SalableUnit.objects.filter(project__created_by=request.user).order_by('building__name', 'unit_number')
    
    context = {
        'units': units,
    }
    
    return render(request, 'sales/unit_list.html', context)


@login_required
def unit_create(request):
    """Create new salable unit"""
    if request.method == 'POST':
        form = SalableUnitForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unit created successfully!')
            return redirect('sales:unit_list')
    else:
        form = SalableUnitForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'sales/unit_form.html', context)


@login_required
def unit_detail(request, unit_id):
    """Unit detail view"""
    unit = get_object_or_404(SalableUnit, id=unit_id, project__created_by=request.user)
    bookings = unit.bookings.all()
    
    context = {
        'unit': unit,
        'bookings': bookings,
    }
    
    return render(request, 'sales/unit_detail.html', context)


@login_required
def unit_edit(request, unit_id):
    """Edit unit"""
    unit = get_object_or_404(SalableUnit, id=unit_id, project__created_by=request.user)
    
    if request.method == 'POST':
        form = SalableUnitForm(request.POST, instance=unit, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unit updated successfully!')
            return redirect('sales:unit_detail', unit_id=unit.id)
    else:
        form = SalableUnitForm(instance=unit, user=request.user)
    
    context = {
        'form': form,
        'unit': unit,
    }
    
    return render(request, 'sales/unit_form.html', context)


@login_required
def customer_list(request):
    """List all customers"""
    customers = Customer.objects.all().order_by('first_name', 'last_name')
    
    context = {
        'customers': customers,
    }
    
    return render(request, 'sales/customer_list.html', context)


@login_required
def customer_create(request):
    """Create new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer created successfully!')
            return redirect('sales:customer_list')
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'sales/customer_form.html', context)


@login_required
def customer_edit(request, customer_id):
    """Edit customer"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully!')
            return redirect('sales:customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
    }
    
    return render(request, 'sales/customer_form.html', context)


@login_required
def customer_detail(request, customer_id):
    """Customer detail view"""
    customer = get_object_or_404(Customer, id=customer_id)
    bookings = customer.bookings.all()
    
    context = {
        'customer': customer,
        'bookings': bookings,
    }
    
    return render(request, 'sales/customer_detail.html', context)


@login_required
def booking_list(request):
    """List all sale bookings"""
    bookings = SaleBooking.objects.filter(sales_person=request.user).order_by('-created_at')
    
    context = {
        'bookings': bookings,
    }
    
    return render(request, 'sales/booking_list.html', context)


@login_required
def booking_create(request):
    """Create new sale booking"""
    if request.method == 'POST':
        form = SaleBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.sales_person = request.user
            booking.save()
            messages.success(request, 'Sale booking created successfully!')
            return redirect('sales:booking_detail', booking_id=booking.id)
    else:
        form = SaleBookingForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'sales/booking_form.html', context)


@login_required
def booking_detail(request, booking_id):
    """Sale booking detail view"""
    booking = get_object_or_404(SaleBooking, id=booking_id, sales_person=request.user)
    payment_schedule = booking.payment_schedule.all()
    payments = booking.payments.all()
    
    context = {
        'booking': booking,
        'payment_schedule': payment_schedule,
        'payments': payments,
    }
    
    return render(request, 'sales/booking_detail.html', context)


@login_required
def booking_edit(request, booking_id):
    """Edit booking"""
    booking = get_object_or_404(SaleBooking, id=booking_id, sales_person=request.user)
    
    if request.method == 'POST':
        form = SaleBookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Booking updated successfully!')
            return redirect('sales:booking_detail', booking_id=booking.id)
    else:
        form = SaleBookingForm(instance=booking)
    
    context = {
        'form': form,
        'booking': booking,
    }
    
    return render(request, 'sales/booking_form.html', context)


@login_required
def booking_delete(request, booking_id):
    """Delete a booking"""
    booking = get_object_or_404(SaleBooking, id=booking_id, sales_person=request.user)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'Booking deleted successfully!')
        return redirect('sales:booking_list')
    return render(request, 'projects/confirm_delete.html', {
        'object': booking,
        'cancel_url': 'sales:booking_list'
    })


@login_required
def payment_create(request, booking_id):
    """Create payment for booking"""
    booking = get_object_or_404(SaleBooking, id=booking_id, sales_person=request.user)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.booking = booking
            payment.save()
            messages.success(request, 'Payment created successfully!')
            return redirect('sales:booking_detail', booking_id=booking.id)
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'booking': booking,
    }
    
    return render(request, 'sales/payment_form.html', context)


@login_required
def price_list_view(request):
    """List all price lists"""
    price_lists = PriceList.objects.filter(project__created_by=request.user).order_by('-created_at')
    
    context = {
        'price_lists': price_lists,
    }
    
    return render(request, 'sales/price_list.html', context)


@login_required
def price_list_create(request):
    """Create new price list"""
    if request.method == 'POST':
        form = PriceListForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Price list created successfully!')
            return redirect('sales:price_list')
    else:
        form = PriceListForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'sales/price_list_form.html', context)


@login_required
def sales_reports(request):
    """Sales reports and analytics"""
    projects = Project.objects.filter(created_by=request.user)
    
    context = {
        'projects': projects,
    }
    
    return render(request, 'sales/sales_reports.html', context)