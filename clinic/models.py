from django.db import models
from django.urls import reverse

class Specialty(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Doctor(models.Model):
    full_name = models.CharField(max_length=120)
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, related_name='doctors')
    bio = models.TextField(max_length=1500)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2)
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True)
    is_accepting = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['full_name']
    def __str__(self): return self.full_name
    def get_absolute_url(self): return reverse('doctor_detail', args=[self.pk])

class Appointment(models.Model):
    VISIT_CHOICES = [('clinic','In-Clinic'), ('teleconsultation','Teleconsultation')]
    STATUS_CHOICES = [('pending','Pending'), ('confirmed','Confirmed'), ('cancelled','Cancelled')]
    TIME_SLOTS = [('09:00','09:00'), ('10:00','10:00'), ('11:00','11:00'), ('13:00','13:00'), ('14:00','14:00'), ('15:00','15:00')]
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name='appointments')
    patient_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=16)
    appointment_date = models.DateField()
    time_slot = models.CharField(max_length=5, choices=TIME_SLOTS)
    visit_type = models.CharField(max_length=20, choices=VISIT_CHOICES, default='clinic')
    reason = models.CharField(max_length=300)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    date_created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-appointment_date', 'time_slot']
        constraints = [models.UniqueConstraint(fields=['doctor','appointment_date','time_slot'], condition=~models.Q(status='cancelled'), name='unique_active_doctor_slot')]
    @property
    def reference(self): return f'MB-{self.pk:06d}'
    def __str__(self): return f'{self.reference} — {self.patient_name}'
