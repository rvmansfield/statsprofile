from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from .forms import PlayerMetricForm, CaptureForm, PlayerProfileForm
from .models import PlayerMetric, MetricsHistory, MetricsRange
import json

# Create your views here.

def index(request):
    
    return render(request, 'main/index.html')


def calculate_percentile(min_val, max_val, current_val):
    if max_val == min_val:
        raise ValueError("max and min cannot be the same")
    
    # Clamp current_val between min and max to avoid weird % outside 0–100
    current_val = max(min_val, min(current_val, max_val))
    
    percentile = (current_val - min_val) / (max_val - min_val) * 100
    return int(percentile)



def results(request, metric_id):
    try:
        player_metric = PlayerMetric.objects.get(id=metric_id)
        
        # Get comparison data from MetricsRange for the same metric type and age
        comparison_data = []
        
        # Get the player's age for comparison
        player_age = int(player_metric.ageCaptured)
        
        # Try to get the metrics range for this metric type and age
        try:
            metrics_range = MetricsRange.objects.get(
                metricType=player_metric.metricType,
                playerAge=player_age
            )
            
            comparison_data = {
                'min_value': metrics_range.Min,
                'max_value': metrics_range.Max,
                'average': metrics_range.Avg,
                'current_value': player_metric.metric,
                'metric_type_display': player_metric.get_metricType_display(),
                'player_age': player_age,
                'has_data': True,
                'percentile': calculate_percentile(metrics_range.Min, metrics_range.Max, player_metric.metric),
                
            }

            print(comparison_data)
            
        except MetricsRange.DoesNotExist:
            # No range data for this metric type and age
            comparison_data = {
                'no_data': True,
                'player_age': player_age,
                'metric_type_display': player_metric.get_metricType_display()
            }
        
        return render(request, 'main/results.html', {
            'player_metric': player_metric,
            'comparison_data': comparison_data
        })
    except PlayerMetric.DoesNotExist:
        return redirect('evaluate')

def metrics_history(request):
    # Get search parameters
    search_query = request.GET.get('search', '')
    player_id = request.GET.get('player_id', '')
    event_id = request.GET.get('event_id', '')
    
    # Start with all records
    metrics_list = MetricsHistory.objects.all()
    
    # Apply filters
    if search_query:
        metrics_list = metrics_list.filter(
            Q(player_id__icontains=search_query) |
            Q(event_id__icontains=search_query) |
            Q(gradYear__icontains=search_query)
        )
    
    if player_id:
        metrics_list = metrics_list.filter(player_id=player_id)
    
    if event_id:
        metrics_list = metrics_list.filter(event_id=event_id)
    
    # Pagination
    paginator = Paginator(metrics_list, 25)  # Show 25 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'player_id': player_id,
        'event_id': event_id,
        'total_records': metrics_list.count(),
    }
    
    return render(request, 'main/metrics_history.html', context)


@login_required
def capture(request):
    """View for capturing multiple metrics at once - requires login"""
    if request.method == 'POST':
        form = CaptureForm(request.POST)
        if form.is_valid():
            # Get common data
            age_captured = form.cleaned_data['ageCaptured']
            user = request.user  # Always use the logged-in user (capture requires login)
            date_captured = form.cleaned_data.get('dateCaptured')
            captured_by = form.cleaned_data.get('capturedBy')
            notes = form.cleaned_data.get('notes')
            
            # Save metrics for each filled field
            saved_count = 0
            for field_name, value in form.cleaned_data.items():
                if field_name.startswith('metric_') and value is not None:
                    metric_type = field_name.replace('metric_', '')
                    try:
                        PlayerMetric.objects.create(
                            metricType=metric_type,
                            metric=value,
                            ageCaptured=age_captured,
                            user=user,
                            dateCaptured=date_captured,
                            capturedBy=captured_by,
                            notes=notes
                        )
                        saved_count += 1
                    except Exception as e:
                        messages.error(request, f'Error saving {metric_type}: {str(e)}')
            
            if saved_count > 0:
                messages.success(request, f'Successfully saved {saved_count} metric(s)!')
                return redirect('capture')
            else:
                messages.warning(request, 'No metrics were saved. Please fill in at least one metric.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CaptureForm()
    
    return render(request, 'main/capture.html', {'form': form})


@login_required
def profile(request):
    """View for displaying user profile with individual metric charts"""
    user = request.user
    player_profile = user.player_profile
    
    # Get all metrics for the current user
    user_metrics = PlayerMetric.objects.filter(user=user).order_by('dateCaptured')
    
    # Initialize metric data containers
    metrics_data = {
        '60': {'dates': [], 'values': [], 'labels': [], 'display': '60 Yard Dash', 'unit': 'seconds', 'reverse': True},
        'fbvelo': {'dates': [], 'values': [], 'labels': [], 'display': 'Fastball Velocity', 'unit': 'mph', 'reverse': False},
        'exitvelo': {'dates': [], 'values': [], 'labels': [], 'display': 'Exit Velocity', 'unit': 'mph', 'reverse': False},
        'ofvelo': {'dates': [], 'values': [], 'labels': [], 'display': 'Outfield Velocity', 'unit': 'mph', 'reverse': False},
        'ifvelo': {'dates': [], 'values': [], 'labels': [], 'display': 'Infield Velocity', 'unit': 'mph', 'reverse': False},
    }
    
    # Organize metrics by type
    for metric in user_metrics:
        if metric.metricType in metrics_data:
            date_str = metric.dateCaptured.strftime('%Y-%m-%d') if metric.dateCaptured else 'N/A'
            # Get capturedBy display value
            captured_by_display = metric.get_capturedBy_display() if metric.capturedBy else 'N/A'
            # Create label as array for multi-line display in Chart.js
            label = [date_str, captured_by_display]
            metrics_data[metric.metricType]['dates'].append(date_str)
            metrics_data[metric.metricType]['values'].append(float(metric.metric))
            metrics_data[metric.metricType]['labels'].append(label)
    
    # Prepare context with JSON data for each metric
    context = {
        'user': user,
        'profile': player_profile,
        'total_metrics': user_metrics.count(),
        'metrics_data': {
            metric_type: {
                'dates': json.dumps(data['dates']),
                'values': json.dumps(data['values']),
                'labels': json.dumps(data['labels']),
                'display': data['display'],
                'unit': data['unit'],
                'reverse': data['reverse'],
                'has_data': len(data['dates']) > 0
            }
            for metric_type, data in metrics_data.items()
        }
    }
    
    return render(request, 'main/profile.html', context)

def evaluate(request):
    if request.method == 'POST':
        form = PlayerMetricForm(request.POST)
        if form.is_valid():
            # Set user based on authentication status
            if request.user.is_authenticated:
                form.instance.user = request.user
            else:
                form.instance.user = None  # Anonymous user
            player_metric = form.save()
            return redirect('results', metric_id=player_metric.id)
    else:
        form = PlayerMetricForm()
    
    return render(request, 'main/evaluate.html', {'form': form})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = PlayerProfileForm(request.POST, request.FILES, instance=request.user.player_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = PlayerProfileForm(instance=request.user.player_profile)
    
    return render(request, 'main/edit_profile.html', {'form': form})
