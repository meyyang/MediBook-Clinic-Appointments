from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from .models import Specialty, Doctor, Appointment
from .forms import AppointmentForm, DoctorForm

class MediBookTests(TestCase):
    def setUp(self):
        self.specialty=Specialty.objects.create(name='Family Medicine',slug='family-medicine')
        self.doctor=Doctor.objects.create(full_name='Dr. Demo Santos',specialty=self.specialty,bio='Experienced primary care doctor supporting families and wellness.',consultation_fee=Decimal('650.00'))
        self.client=Client()
    def valid_payload(self, **overrides):
        future=date.today()+timedelta(days=2)
        while future.weekday()==6: future+=timedelta(days=1)
        data={'patient_name':'Sample Patient','email':'sample@example.com','phone':'09171234567','appointment_date':future.isoformat(),'time_slot':'09:00','visit_type':'clinic','reason':'Regular wellness consultation'}
        data.update(overrides); return data
    def test_directory_renders(self):
        response=self.client.get(reverse('doctor_list'))
        self.assertEqual(response.status_code,200); self.assertContains(response,'Dr. Demo Santos')
    def test_valid_booking_saves_and_confirmation_has_reference(self):
        response=self.client.post(reverse('book_appointment',args=[self.doctor.pk]),self.valid_payload())
        self.assertEqual(response.status_code,302)
        appointment=Appointment.objects.get(); self.assertEqual(appointment.status,'pending')
        confirmation=self.client.get(response.url); self.assertContains(confirmation,appointment.reference)
    def test_phone_validation(self):
        form=AppointmentForm(self.valid_payload(phone='12345'),doctor=self.doctor)
        self.assertFalse(form.is_valid()); self.assertIn('phone',form.errors)
    def test_fee_must_be_positive(self):
        form=DoctorForm({'full_name':'Dr. Fee','specialty':self.specialty.pk,'bio':'Bio','consultation_fee':'0','is_accepting':'on'})
        self.assertFalse(form.is_valid()); self.assertIn('consultation_fee',form.errors)
    def test_sunday_rejected(self):
        sunday=date.today()+timedelta(days=(6-date.today().weekday())%7 or 7)
        form=AppointmentForm(self.valid_payload(appointment_date=sunday.isoformat()),doctor=self.doctor)
        self.assertFalse(form.is_valid()); self.assertIn('appointment_date',form.errors)
    def test_teleconsultation_requires_email(self):
        form=AppointmentForm(self.valid_payload(email='',visit_type='teleconsultation'),doctor=self.doctor)
        self.assertFalse(form.is_valid()); self.assertIn('email',form.errors)
    def test_reason_minimum(self):
        form=AppointmentForm(self.valid_payload(reason='short'),doctor=self.doctor)
        self.assertFalse(form.is_valid()); self.assertIn('reason',form.errors)
    def test_double_booking_rejected(self):
        payload=self.valid_payload(); form=AppointmentForm(payload,doctor=self.doctor); self.assertTrue(form.is_valid(),form.errors)
        appointment=form.save(commit=False); appointment.doctor=self.doctor; appointment.save()
        second=AppointmentForm(payload,doctor=self.doctor); self.assertFalse(second.is_valid()); self.assertIn('time_slot',second.errors)
    def test_not_accepting_doctor_cannot_be_booked(self):
        self.doctor.is_accepting=False; self.doctor.save()
        response=self.client.post(reverse('book_appointment',args=[self.doctor.pk]),self.valid_payload())
        self.assertEqual(response.status_code,302); self.assertEqual(Appointment.objects.count(),0)
    def test_invalid_doctor_returns_404(self):
        self.assertEqual(self.client.get('/doctors/99999/').status_code,404)
    def test_htmx_search_returns_partial(self):
        response=self.client.get(reverse('doctor_list'),{'q':'Demo'},HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code,200); self.assertContains(response,'doctor-results')
    def test_cancelled_slot_can_be_rebooked(self):
        payload=self.valid_payload(); a=Appointment.objects.create(doctor=self.doctor,**payload,status='cancelled')
        form=AppointmentForm(payload,doctor=self.doctor); self.assertTrue(form.is_valid(),form.errors)
