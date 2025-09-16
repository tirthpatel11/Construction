from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Building, Wing, SalableUnit, Customer
from projects.models import Project


@login_required
def get_buildings(request):
    """API endpoint to get buildings for a specific project"""
    project_id = request.GET.get('project')
    if not project_id:
        return JsonResponse({'buildings': []})
    
    try:
        project = Project.objects.get(id=project_id, created_by=request.user)
        buildings = Building.objects.filter(project=project).values('id', 'name')
        return JsonResponse({'buildings': list(buildings)})
    except Project.DoesNotExist:
        return JsonResponse({'buildings': []})


@login_required
def get_wings(request):
    """API endpoint to get wings for a specific building"""
    building_id = request.GET.get('building')
    if not building_id:
        return JsonResponse({'wings': []})
    
    try:
        building = Building.objects.get(id=building_id, project__created_by=request.user)
        wings = Wing.objects.filter(building=building).values('id', 'name')
        return JsonResponse({'wings': list(wings)})
    except Building.DoesNotExist:
        return JsonResponse({'wings': []})


@login_required
def get_units(request):
    """API endpoint to get all available units"""
    try:
        units = SalableUnit.objects.filter(
            project__created_by=request.user,
            status='available'
        ).select_related('project', 'building', 'unit_type').values(
            'id', 'unit_number', 'floor_number', 'super_built_up_area', 
            'current_price', 'project__name', 'building__name', 'unit_type__name'
        )
        
        # Convert to dictionary format for easier lookup
        units_dict = {}
        for unit in units:
            units_dict[unit['id']] = unit
            
        return JsonResponse({'units': units_dict})
    except Exception as e:
        return JsonResponse({'units': {}})


@login_required
def get_customers(request):
    """API endpoint to get all customers"""
    try:
        customers = Customer.objects.filter(
            created_by=request.user
        ).values(
            'id', 'first_name', 'last_name', 'email', 'phone', 'customer_type'
        )
        
        # Convert to dictionary format for easier lookup
        customers_dict = {}
        for customer in customers:
            customers_dict[customer['id']] = customer
            
        return JsonResponse({'customers': customers_dict})
    except Exception as e:
        return JsonResponse({'customers': {}})
