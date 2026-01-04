from django.contrib import admin
from .models import PlayerMetric, MetricsHistory, MetricsRange, PlayerProfile

@admin.register(PlayerMetric)
class PlayerMetricAdmin(admin.ModelAdmin):
    list_display = ('metricType', 'metric', 'playerAge', 'created_at', 'user__username')
    list_filter = ('metricType',)
    search_fields = ('metric', 'playerAge', 'user__username')
    date_hierarchy = None
    ordering = ('-created_at',)

@admin.register(MetricsHistory)
class MetricsHistoryAdmin(admin.ModelAdmin):
    list_display = ('player_id', 'event_id', 'event_date', 'height', 'weight', 'exitVelo', 'sixtyyard', 'maxFB')
    list_filter = ('event_date', 'gradYear', 'event_id')
    search_fields = ('player_id', 'event_id')
    date_hierarchy = 'event_date'
    ordering = ('-event_date', 'player_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Player Information', {
            'fields': ('player_id', 'height', 'weight', 'gradYear')
        }),
        ('Velocity Metrics', {
            'fields': ('ifVelo', 'ofVelo', 'cVelo', 'exitVelo', 'maxFB')
        }),
        ('Time Metrics', {
            'fields': ('popTime', 'sixtyyard')
        }),
        ('Pitch Velocities', {
            'fields': ('changeUp', 'curve', 'slider')
        }),
        ('Event Information', {
            'fields': ('event_id', 'event_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MetricsRange)
class MetricsRangeAdmin(admin.ModelAdmin):
    list_display = ('metricType', 'Min', 'Max', 'Avg', 'playerAge')
    list_filter = ('metricType', 'playerAge')
    search_fields = ('metricType',)
    ordering = ('metricType', 'playerAge')
    
    fieldsets = (
        ('Metric Information', {
            'fields': ('metricType', 'playerAge')
        }),
        ('Range Values', {
            'fields': ('Min', 'Max', 'Avg')
        }),
    )

@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_positions_display', 'team', 'graduation_year')
    search_fields = ('user__username', 'team', 'positions')
    list_filter = ('graduation_year',)
    
    def get_positions_display(self, obj):
        return obj.get_positions_display()
    get_positions_display.short_description = 'Positions'
