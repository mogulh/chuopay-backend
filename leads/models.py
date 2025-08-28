from django.db import models

class Lead(models.Model):
    USER_TYPE_CHOICES = [
        ('parent', 'Parent'),
        ('administrator', 'School Administrator'),
        ('teacher', 'Teacher'),
    ]
    
    name = models.CharField(max_length=255)
    email = models.EmailField()
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    source = models.CharField(max_length=50, default='demo_signup')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'leads'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.email}) - {self.user_type}" 