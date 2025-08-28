from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Lead

@csrf_exempt
@require_http_methods(["POST"])
def create_lead(request):
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['name', 'email', 'user_type']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Create the lead
        lead = Lead.objects.create(
            name=data['name'],
            email=data['email'],
            user_type=data['user_type'],
            source=data.get('source', 'demo_signup')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Lead created successfully',
            'lead_id': lead.id
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500) 