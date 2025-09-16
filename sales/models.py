from django.db import models
from django.contrib.auth.models import User
from projects.models import Project
from decimal import Decimal
from datetime import date


class Building(models.Model):
    """Building information"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='buildings')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    total_floors = models.IntegerField(default=1)
    total_units = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.project.name} - {self.name}"


class Wing(models.Model):
    """Wing information within a building"""
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='wings')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    total_units = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.building.name} - {self.name}"


class UnitType(models.Model):
    """Unit types (1BHK, 2BHK, 3BHK, etc.)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    bedrooms = models.IntegerField(default=1)
    bathrooms = models.IntegerField(default=1)
    carpet_area = models.DecimalField(max_digits=10, decimal_places=2)
    built_up_area = models.DecimalField(max_digits=10, decimal_places=2)
    super_built_up_area = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name


class SalableUnit(models.Model):
    """Salable units (apartments, shops, etc.)"""
    UNIT_STATUS = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('sold', 'Sold'),
        ('reserved', 'Reserved'),
        ('blocked', 'Blocked'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='salable_units')
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='units')
    wing = models.ForeignKey(Wing, on_delete=models.CASCADE, related_name='units', null=True, blank=True)
    unit_type = models.ForeignKey(UnitType, on_delete=models.CASCADE)
    unit_number = models.CharField(max_length=50)
    floor_number = models.IntegerField()
    carpet_area = models.DecimalField(max_digits=10, decimal_places=2)
    built_up_area = models.DecimalField(max_digits=10, decimal_places=2)
    super_built_up_area = models.DecimalField(max_digits=10, decimal_places=2)
    base_price = models.DecimalField(max_digits=15, decimal_places=2)
    current_price = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=UNIT_STATUS, default='available')
    facing = models.CharField(max_length=100, blank=True)
    amenities = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.building.name} - {self.unit_number}"
    
    @property
    def price_per_sqft(self):
        if self.super_built_up_area > 0:
            return self.current_price / self.super_built_up_area
        return 0


class ParkingUnit(models.Model):
    """Parking units"""
    PARKING_TYPES = [
        ('covered', 'Covered'),
        ('open', 'Open'),
        ('basement', 'Basement'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='parking_units')
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='parking_units')
    parking_number = models.CharField(max_length=50)
    parking_type = models.CharField(max_length=20, choices=PARKING_TYPES)
    area = models.DecimalField(max_digits=10, decimal_places=2)
    base_price = models.DecimalField(max_digits=15, decimal_places=2)
    current_price = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=SalableUnit.UNIT_STATUS, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.building.name} - Parking {self.parking_number}"


class PriceList(models.Model):
    """Price lists for different unit types"""
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='price_lists')
    unit_type = models.ForeignKey(UnitType, on_delete=models.CASCADE)
    base_price = models.DecimalField(max_digits=15, decimal_places=2)
    price_per_sqft = models.DecimalField(max_digits=10, decimal_places=2)
    floor_rise = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    corner_premium = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    view_premium = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.unit_type.name}"


class Customer(models.Model):
    """Customer information"""
    CUSTOMER_TYPES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('nri', 'NRI'),
    ]
    
    customer_id = models.CharField(max_length=50, unique=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='individual')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    pan_number = models.CharField(max_length=10, blank=True)
    aadhar_number = models.CharField(max_length=12, blank=True)
    gst_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    annual_income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.customer_id:
            # Generate customer ID: CUST + 6-digit number
            # Use a more robust method to avoid race conditions
            import time
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    # Get the highest customer ID number
                    last_customer = Customer.objects.filter(
                        customer_id__startswith='CUST'
                    ).order_by('-customer_id').first()
                    
                    if last_customer and last_customer.customer_id:
                        try:
                            last_number = int(last_customer.customer_id.replace('CUST', ''))
                            next_number = last_number + 1
                        except (ValueError, AttributeError):
                            next_number = 1
                    else:
                        next_number = 1
                    
                    self.customer_id = f"CUST{next_number:06d}"
                    
                    # Try to save, if it fails due to unique constraint, try next number
                    super().save(*args, **kwargs)
                    break
                    
                except Exception as e:
                    if 'UNIQUE constraint failed' in str(e) and attempt < max_attempts - 1:
                        # If unique constraint failed, try next number
                        next_number += 1
                        self.customer_id = f"CUST{next_number:06d}"
                        time.sleep(0.1)  # Small delay to avoid rapid retries
                        continue
                    else:
                        raise e
        else:
            super().save(*args, **kwargs)
    
    def __str__(self):
        if self.customer_type == 'company':
            return f"{self.company_name} ({self.customer_id})"
        return f"{self.first_name} {self.last_name} ({self.customer_id})"
    
    @property
    def full_name(self):
        if self.customer_type == 'company':
            return self.company_name
        return f"{self.first_name} {self.last_name}"


class SaleBooking(models.Model):
    """Sale booking with payment schedule"""
    BOOKING_STATUS = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    booking_number = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='bookings')
    unit = models.ForeignKey(SalableUnit, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    agreement_value = models.DecimalField(max_digits=15, decimal_places=2)
    booking_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='draft')
    sales_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_bookings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            # Generate booking number: BK + 6-digit number
            last_booking = SaleBooking.objects.order_by('-id').first()
            if last_booking and last_booking.booking_number:
                try:
                    last_number = int(last_booking.booking_number.replace('BK', ''))
                    next_number = last_number + 1
                except (ValueError, AttributeError):
                    next_number = 1
            else:
                next_number = 1
            self.booking_number = f"BK{next_number:06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Booking-{self.booking_number} - {self.customer.full_name}"
    
    @property
    def booking_percentage(self):
        if self.agreement_value > 0:
            return (self.booking_amount / self.agreement_value) * 100
        return 0
    
    @property
    def outstanding_amount(self):
        total_paid = sum(payment.amount for payment in self.payments.filter(status='paid'))
        return self.agreement_value - total_paid


class PaymentSchedule(models.Model):
    """Payment schedule for sale bookings"""
    PAYMENT_TYPES = [
        ('booking', 'Booking Amount'),
        ('down_payment', 'Down Payment'),
        ('construction', 'Construction Linked'),
        ('possession', 'Possession'),
        ('registration', 'Registration'),
        ('other', 'Other'),
    ]
    
    booking = models.ForeignKey(SaleBooking, on_delete=models.CASCADE, related_name='payment_schedule')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    description = models.CharField(max_length=255)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.booking.booking_number} - {self.get_payment_type_display()}"


class Payment(models.Model):
    """Payment records"""
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('dd', 'Demand Draft'),
        ('neft', 'NEFT'),
        ('rtgs', 'RTGS'),
        ('upi', 'UPI'),
        ('card', 'Card'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('bounced', 'Bounced'),
        ('cancelled', 'Cancelled'),
    ]
    
    booking = models.ForeignKey(SaleBooking, on_delete=models.CASCADE, related_name='payments')
    payment_schedule = models.ForeignKey(PaymentSchedule, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='paid')
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment-{self.id} - {self.amount}"


class SalesReport(models.Model):
    """Sales reports and analytics"""
    report_date = models.DateField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sales_reports')
    total_units = models.IntegerField(default=0)
    sold_units = models.IntegerField(default=0)
    booked_units = models.IntegerField(default=0)
    available_units = models.IntegerField(default=0)
    total_sales_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_collection = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    outstanding_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Sales Report - {self.project.name} - {self.report_date}"