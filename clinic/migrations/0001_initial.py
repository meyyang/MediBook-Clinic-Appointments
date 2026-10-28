# Generated for the MediBook practical project.
import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='Specialty', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('name',models.CharField(max_length=80,unique=True)),('slug',models.SlugField(max_length=90,unique=True))], options={'ordering':['name']}),
        migrations.CreateModel(name='Doctor', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('full_name',models.CharField(max_length=120)),('bio',models.TextField(max_length=1500)),('consultation_fee',models.DecimalField(decimal_places=2,max_digits=8)),('photo',models.ImageField(blank=True,null=True,upload_to='doctors/')),('is_accepting',models.BooleanField(default=True)),('date_created',models.DateTimeField(auto_now_add=True)),('specialty',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='doctors',to='clinic.specialty'))], options={'ordering':['full_name']}),
        migrations.CreateModel(name='Appointment', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('patient_name',models.CharField(max_length=120)),('email',models.EmailField(blank=True,max_length=254)),('phone',models.CharField(max_length=16)),('appointment_date',models.DateField()),('time_slot',models.CharField(choices=[('09:00','09:00'),('10:00','10:00'),('11:00','11:00'),('13:00','13:00'),('14:00','14:00'),('15:00','15:00')],max_length=5)),('visit_type',models.CharField(choices=[('clinic','In-Clinic'),('teleconsultation','Teleconsultation')],default='clinic',max_length=20)),('reason',models.CharField(max_length=300)),('status',models.CharField(choices=[('pending','Pending'),('confirmed','Confirmed'),('cancelled','Cancelled')],default='pending',max_length=12)),('date_created',models.DateTimeField(auto_now_add=True)),('doctor',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='appointments',to='clinic.doctor'))], options={'ordering':['-appointment_date','time_slot']}),
        migrations.AddConstraint(model_name='appointment',constraint=models.UniqueConstraint(condition=~models.Q(('status','cancelled')),fields=('doctor','appointment_date','time_slot'),name='unique_active_doctor_slot')),
    ]
