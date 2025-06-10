from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.gis.geos import Point, LineString
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from .models import RouteRiskScore

class RouteRiskScoreView(View):
    """View for retrieving and calculating route risk scores"""
    
    def get(self, request, route_id=None):
        """Get risk score for a specific route or list all routes"""
        if route_id:
            try:
                route = RouteRiskScore.objects.get(route_id=route_id)
                data = {
                    'route_id': route.route_id,
                    'source': route.source,
                    'destination': route.destination,
                    'traffic_score': route.traffic_score,
                    'crime_score': route.crime_score,
                    'weather_score': route.weather_score,
                    'final_score': route.final_score,
                    'created_at': route.created_at.isoformat(),
                }
                return JsonResponse(data)
            except RouteRiskScore.DoesNotExist:
                return JsonResponse({'error': 'Route not found'}, status=404)
        else:
            # List all routes (with pagination)
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 10))
            start = (page - 1) * limit
            end = page * limit
            
            routes = RouteRiskScore.objects.filter(is_active=True).order_by('-created_at')[start:end]
            routes_data = []
            
            for route in routes:
                routes_data.append({
                    'route_id': route.route_id,
                    'source': route.source,
                    'destination': route.destination,
                    'final_score': route.final_score,
                    'created_at': route.created_at.isoformat(),
                })
            
            return JsonResponse({'routes': routes_data})
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Create a new route risk score or update if exists"""
        try:
            data = json.loads(request.body)
            
            # Extract required fields
            route_id = data.get('route_id')
            source = data.get('source')
            destination = data.get('destination')
            traffic_score = data.get('traffic_score')
            crime_score = data.get('crime_score')
            weather_score = data.get('weather_score')
            
            # Optional spatial data
            source_coords = data.get('source_coords')  # [lng, lat]
            dest_coords = data.get('destination_coords')  # [lng, lat]
            route_geometry_coords = data.get('route_geometry')  # [[lng, lat], ...]
            
            # Validate required fields
            if not all([route_id, source, destination, 
                      isinstance(traffic_score, (int, float)),
                      isinstance(crime_score, (int, float)), 
                      isinstance(weather_score, (int, float))]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            # Create or update route
            route, created = RouteRiskScore.objects.update_or_create(
                route_id=route_id,
                defaults={
                    'source': source,
                    'destination': destination,
                    'traffic_score': traffic_score,
                    'crime_score': crime_score,
                    'weather_score': weather_score,
                    'is_active': True
                }
            )
            
            # Add spatial data if provided
            if source_coords and len(source_coords) == 2:
                route.source_point = Point(source_coords[0], source_coords[1])
            
            if dest_coords and len(dest_coords) == 2:
                route.destination_point = Point(dest_coords[0], dest_coords[1])
            
            if route_geometry_coords and len(route_geometry_coords) >= 2:
                route.route_geometry = LineString(route_geometry_coords)
            
            # Calculate final score
            route.calculate_final_score()
            route.save()
            
            return JsonResponse({
                'success': True,
                'route_id': route.route_id,
                'final_score': route.final_score,
                'created': created
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class RouteRiskComparisonView(View):
    """View for comparing multiple routes by risk score"""
    
    def get(self, request):
        """Get and compare routes between source and destination"""
        source = request.GET.get('source')
        destination = request.GET.get('destination')
        
        if not source or not destination:
            return JsonResponse({'error': 'Source and destination are required'}, status=400)
        
        # Find routes matching the source and destination
        routes = RouteRiskScore.objects.filter(
            source=source,
            destination=destination,
            is_active=True
        ).order_by('final_score')  # Lower score = higher risk
        
        if not routes:
            return JsonResponse({'error': 'No routes found'}, status=404)
        
        routes_data = []
        for route in routes:
            routes_data.append({
                'route_id': route.route_id,
                'traffic_score': route.traffic_score,
                'crime_score': route.crime_score,
                'weather_score': route.weather_score,
                'final_score': route.final_score,
                'created_at': route.created_at.isoformat(),
            })
        
        return JsonResponse({
            'source': source,
            'destination': destination,
            'routes': routes_data,
            'safest_route_id': routes.last().route_id if routes else None,
            'riskiest_route_id': routes.first().route_id if routes else None,
        })
