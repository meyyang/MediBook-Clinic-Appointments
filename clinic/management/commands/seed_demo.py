from django.core.management.base import BaseCommand
from django.utils.text import slugify
from clinic.models import Specialty, Doctor
class Command(BaseCommand):
    help='Create demo specialties and doctors for MediBook.'
    def handle(self,*args,**options):
        records=[('Family Medicine','Dr. Andrea Santos','Provides primary care for adults and families, preventive checkups, and general health consultations.',650),('Cardiology','Dr. Miguel Reyes','Focuses on heart health, blood pressure, and cardiovascular risk assessment.',950),('Pediatrics','Dr. Clara Mendoza','Provides child wellness visits, routine consultations, and parent guidance.',700),('Dermatology','Dr. Paolo Garcia','Assesses common skin, hair, and nail concerns and recommends treatment options.',850),('Psychiatry','Dr. Nina Cruz','Offers mental health assessment and patient-centered consultation.',1100),('Internal Medicine','Dr. Luis Flores','Supports adult patients with acute and chronic medical concerns.',800),('Ophthalmology','Dr. Bea Lim','Provides eye health consultation and screening.',750)]
        for specialty_name, doctor_name, bio, fee in records:
            specialty,_=Specialty.objects.get_or_create(name=specialty_name,defaults={'slug':slugify(specialty_name)})
            Doctor.objects.get_or_create(full_name=doctor_name,defaults={'specialty':specialty,'bio':bio,'consultation_fee':fee,'is_accepting':True,'photo':'doctors/demo_doctor.png' if doctor_name == 'Dr. Andrea Santos' else None})
        self.stdout.write(self.style.SUCCESS(f'Seeded demo data: {Specialty.objects.count()} specialties, {Doctor.objects.count()} doctors.'))
