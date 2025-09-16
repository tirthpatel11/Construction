from django import forms
from .models import (
    Building, Wing, UnitType, SalableUnit, ParkingUnit, PriceList,
    Customer, SaleBooking, PaymentSchedule, Payment
)
from projects.models import Project


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['project', 'name', 'description', 'total_floors', 'total_units']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Building name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'total_floors': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of floors'}),
            'total_units': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total units'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['project'].queryset = Project.objects.filter(created_by=user)


class SalableUnitForm(forms.ModelForm):
    class Meta:
        model = SalableUnit
        fields = [
            'project', 'building', 'wing', 'unit_type', 'unit_number', 'floor_number',
            'carpet_area', 'built_up_area', 'super_built_up_area', 'base_price',
            'current_price', 'facing', 'amenities'
        ]
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'building': forms.Select(attrs={'class': 'form-select'}),
            'wing': forms.Select(attrs={'class': 'form-select'}),
            'unit_type': forms.Select(attrs={'class': 'form-select'}),
            'unit_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unit number'}),
            'floor_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Floor number'}),
            'carpet_area': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'built_up_area': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'super_built_up_area': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'current_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'facing': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Facing direction'}),
            'amenities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Amenities'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['project'].queryset = Project.objects.filter(created_by=user)


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_type', 'first_name', 'last_name', 'company_name', 'email', 'phone',
            'alternate_phone', 'address', 'city', 'state', 'pincode', 'pan_number',
            'aadhar_number', 'gst_number', 'date_of_birth', 'occupation', 'annual_income'
        ]
        widgets = {
            'customer_type': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alternate phone'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PAN number'}),
            'aadhar_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Aadhar number'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'GST number'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}),
            'annual_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }


class SaleBookingForm(forms.ModelForm):
    class Meta:
        model = SaleBooking
        fields = ['customer', 'unit', 'booking_date', 'agreement_value', 'booking_amount']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'booking_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'agreement_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'booking_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }


class PaymentScheduleForm(forms.ModelForm):
    class Meta:
        model = PaymentSchedule
        fields = ['payment_type', 'description', 'due_date', 'amount', 'percentage']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }


PaymentScheduleFormSet = forms.inlineformset_factory(
    SaleBooking, PaymentSchedule, form=PaymentScheduleForm, extra=1, can_delete=True
)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_schedule', 'payment_date', 'amount', 'payment_method', 'reference_number', 'bank_name', 'status', 'remarks']
        widgets = {
            'payment_schedule': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reference number'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank name'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Remarks'}),
        }


class PriceListForm(forms.ModelForm):
    class Meta:
        model = PriceList
        fields = [
            'name', 'project', 'unit_type', 'base_price', 'price_per_sqft',
            'floor_rise', 'corner_premium', 'view_premium', 'valid_from', 'valid_to'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Price list name'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'unit_type': forms.Select(attrs={'class': 'form-select'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'price_per_sqft': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'floor_rise': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'corner_premium': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'view_premium': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'valid_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['project'].queryset = Project.objects.filter(created_by=user)
