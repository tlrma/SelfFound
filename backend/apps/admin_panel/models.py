from django.db import models


class Alert(models.Model):
    LEVEL_ERROR   = 'error'
    LEVEL_WARNING = 'warning'
    LEVEL_INFO    = 'info'
    LEVEL_CHOICES = [
        (LEVEL_ERROR,   'Error'),
        (LEVEL_WARNING, 'Warning'),
        (LEVEL_INFO,    'Info'),
    ]

    message    = models.TextField()
    level      = models.CharField(max_length=10, choices=LEVEL_CHOICES, default=LEVEL_ERROR)
    source     = models.CharField(max_length=64, blank=True, default='')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
