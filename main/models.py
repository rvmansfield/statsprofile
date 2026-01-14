from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

# Create your models here.

class PlayerMetric(models.Model):
    METRIC_TYPE_CHOICES = [
        ('60', '60 Yard Dash (seconds)'),
        ('fbvelo', 'Fastball Velocity (mph)'),
        ('exitvelo', 'Exit Velocity (mph)'),
        ('ofvelo', 'Outfield Velocity (mph)'),
        ('ifvelo', 'Infield Velocity (mph)'),
      
    ]
    
    CAPTURED_BY_CHOICES = [
        ('Perfect Game', 'Perfect Game'),
        ('Player Metrix', 'Player Metrix'),
        ('Self Captured', 'Self Captured'),
    ]
    
    metricType = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES, verbose_name='Metric Type')
    metric = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Metric')
    
      # Restrict ages to 12-20 via choices; stored as integer
    AGE_CHOICES = [(i, str(i)) for i in range(12, 21)]
    playerAge = models.IntegerField(
        choices=AGE_CHOICES,
        verbose_name='Player Age',
        validators=[MinValueValidator(12), MaxValueValidator(20)]
    )
    
    
    
    # Restrict grad classes via choices; stored as integer
    CLASS_CHOICES = [(i, str(i)) for i in range(2018, 2032)]
    gradClass = models.IntegerField(
        choices=CLASS_CHOICES,
        verbose_name='Graduation Class',
        validators=[MinValueValidator(2018), MaxValueValidator(2032)],
        default=2026
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User', null=True, blank=True)
    dateCaptured = models.DateField(verbose_name='Date Captured', null=True, blank=True)
    notes = models.TextField(verbose_name='Notes', blank=True, null=True, max_length=500)
    capturedBy = models.CharField(
        max_length=20,
        choices=CAPTURED_BY_CHOICES,
        verbose_name='Captured By',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{self.metricType} - {self.metric} (GradClass {self.gradClass}) - {username}"
    
    class Meta:
        verbose_name = 'Player Metric'
        verbose_name_plural = 'Player Metrics'


class MetricsHistory(models.Model):
    # Basic player information
    height = models.IntegerField(null=True, blank=True, verbose_name='Height (inches)')
    weight = models.IntegerField(null=True, blank=True, verbose_name='Weight (lbs)')
    
    # Velocity metrics
    ifVelo = models.IntegerField(null=True, blank=True, verbose_name='Infield Velocity (mph)')
    ofVelo = models.IntegerField(null=True, blank=True, verbose_name='Outfield Velocity (mph)')
    cVelo = models.IntegerField(null=True, blank=True, verbose_name='Catcher Velocity (mph)')
    exitVelo = models.IntegerField(null=True, blank=True, verbose_name='Exit Velocity (mph)')
    maxFB = models.IntegerField(null=True, blank=True, verbose_name='Max Fastball Velocity (mph)')
    
    # Time metrics
    popTime = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name='Pop Time (seconds)')
    sixtyyard = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name='60 Yard Dash (seconds)')
    
    # Pitch velocities
    changeUp = models.IntegerField(null=True, blank=True, verbose_name='Changeup Velocity (mph)')
    curve = models.IntegerField(null=True, blank=True, verbose_name='Curveball Velocity (mph)')
    slider = models.IntegerField(null=True, blank=True, verbose_name='Slider Velocity (mph)')
    
    # Event and player tracking
    event_id = models.IntegerField(verbose_name='Event ID')
    player_id = models.IntegerField(verbose_name='Player ID')
    gradYear = models.IntegerField(null=True, blank=True, verbose_name='Graduation Year')
    event_date = models.DateTimeField(verbose_name='Event Date')

    # Players Age
    playerage = models.IntegerField(verbose_name='Player Age', default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Player {self.player_id} - Event {self.event_id} ({self.event_date.strftime('%Y-%m-%d')})"
    
    class Meta:
        verbose_name = 'Metrics History'
        verbose_name_plural = 'Metrics History'
        ordering = ['-event_date', 'player_id']
        indexes = [
            models.Index(fields=['player_id']),
            models.Index(fields=['event_date']),
            models.Index(fields=['event_id']),
        ]


class MetricsRange(models.Model):
    METRIC_TYPE_CHOICES = [
        ('60', '60 Yard Dash (seconds)'),
        ('fbvelo', 'Fastball Velocity (mph)'),
        ('exitvelo', 'Exit Velocity (mph)'),
        ('ofvelo', 'Outfield Velocity (mph)'),
        ('ifvelo', 'Infield Velocity (mph)'),
    ]
    AGE_CHOICES = [(i, str(i)) for i in range(12, 21)]
    
    metricType = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES, verbose_name='Metric Type')
    Min = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Minimum Value')
    Max = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Maximum Value')
    Avg = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Average Value')
    playerAge = models.IntegerField(verbose_name='Player Age', default=0)
    
    def __str__(self):
        return f"{self.get_metricType_display()} - Min: {self.Min}, Max: {self.Max}, Avg: {self.Avg}"
    
    class Meta:
        verbose_name = 'Metrics Range'
        verbose_name_plural = 'Metrics Ranges'
        unique_together = (('metricType', 'playerAge'),)


class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile')
    
    # Player Info
    POSITION_CHOICES = [
        ('P', 'Pitcher'),
        ('C', 'Catcher'),
        ('1B', 'First Base'),
        ('2B', 'Second Base'),
        ('3B', 'Third Base'),
        ('SS', 'Shortstop'),
        ('OF', 'Outfield'),
    ]
    positions = models.CharField(max_length=200, blank=True, null=True, help_text='Comma-separated list of positions')
    team = models.CharField(max_length=100, blank=True, null=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    
    # Physical Attributes
    height_inches = models.IntegerField(null=True, blank=True)
    weight_lbs = models.IntegerField(null=True, blank=True)
    
    # Additional Fields
    bio = models.TextField(max_length=500, blank=True)
    # Location and picture
    city = models.CharField(max_length=100, blank=True, null=True)

    # School and handedness
    school = models.CharField(max_length=150, blank=True, null=True)

    HAND_CHOICES = [
        ('R', 'Right'),
        ('L', 'Left'),
        ('S', 'Switch'),
    ]
    throws = models.CharField(max_length=1, choices=HAND_CHOICES, blank=True, null=True)
    hits = models.CharField(max_length=1, choices=HAND_CHOICES, blank=True, null=True)

    # Use a 2-letter US state code choice list
    STATE_CHOICES = [
        ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'), ('CA', 'California'),
        ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'), ('FL', 'Florida'), ('GA', 'Georgia'),
        ('HI', 'Hawaii'), ('ID', 'Idaho'), ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'),
        ('KS', 'Kansas'), ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
        ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'), ('MO', 'Missouri'),
        ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'), ('NH', 'New Hampshire'), ('NJ', 'New Jersey'),
        ('NM', 'New Mexico'), ('NY', 'New York'), ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'),
        ('OK', 'Oklahoma'), ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
        ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'), ('VT', 'Vermont'),
        ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'), ('WI', 'Wisconsin'), ('WY', 'Wyoming'),
        ('DC', 'District of Columbia')
    ]
    state = models.CharField(max_length=2, choices=STATE_CHOICES, blank=True, null=True)
    

    # Picture stored using Django ImageField (uploaded to MEDIA_ROOT/player_pics/...)
    picture = models.ImageField(upload_to='player_pics/', blank=True, null=True,default="player_pics/default.jpg")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_positions_list(self):
        """Return positions as a list of position codes"""
        if self.positions:
            return [pos.strip() for pos in self.positions.split(',') if pos.strip()]
        return []
    
    def get_positions_display(self):
        """Return positions as a formatted string with display names"""
        positions_list = self.get_positions_list()
        if not positions_list:
            return "Not set"
        position_dict = dict(self.POSITION_CHOICES)
        return ", ".join([position_dict.get(pos, pos) for pos in positions_list])
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_or_update_player_profile(sender, instance, created, **kwargs):
    if created:
        PlayerProfile.objects.create(user=instance)
    instance.player_profile.save()

