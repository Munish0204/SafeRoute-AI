from django.db import models
from django.contrib.gis.db import models as gis_models

class RouteRiskScore(models.Model):
    route_id = models.CharField(max_length=100, unique=True)
    source = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    source_point = gis_models.PointField(null=True, blank=True, srid=4326)
    destination_point = gis_models.PointField(null=True, blank=True, srid=4326)
    route_geometry = gis_models.LineStringField(null=True, blank=True, srid=4326)
    
    # Risk scores
    traffic_score = models.FloatField()
    crime_score = models.FloatField()
    weather_score = models.FloatField()
    final_score = models.FloatField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['route_id']),
            models.Index(fields=['source', 'destination']),
            models.Index(fields=['created_at']),
            models.Index(fields=['final_score']),
        ]
    
    def __str__(self):
        return f"Route: {self.source} to {self.destination} (Score: {self.final_score})"
    
    def calculate_final_score(self, weights=None):
        """
        Calculate the final risk score based on weighted component scores
        Lower score = higher risk
        """
        if weights is None:
            weights = {
                'traffic': 0.3, 
                'crime': 0.5, 
                'weather': 0.2
            }
            
        self.final_score = (
            weights['traffic'] * self.traffic_score +
            weights['crime'] * self.crime_score + 
            weights['weather'] * self.weather_score
        )
        return self.final_score
