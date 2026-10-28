import re
from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from .models import Doctor, Appointment

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['full_name','specialty','bio','consultation_fee','photo','is_accepting']
        labels = {'full_name':'Doctor name','specialty':'Specialty','bio':'Professional biography','consultation_fee':'Consultation fee (₱)','photo':'Profile photo','is_accepting':'Accepting new patients'}
        help_texts = {'full_name':'Enter the doctor’s full name.','bio':'Briefly describe experience and focus (up to 1,500 characters).','consultation_fee':'Must be greater than ₱0.00.','photo':'Optional JPG/PNG profile image.','is_accepting':'Uncheck to prevent new bookings.'}
        widgets = {'full_name':forms.TextInput(attrs={'class':'field','placeholder':'Dr. Alex Santos'}),'specialty':forms.Select(attrs={'class':'field'}),'bio':forms.Textarea(attrs={'class':'field','rows':4}),'consultation_fee':forms.NumberInput(attrs={'class':'field','min':'0.01','step':'0.01'}),'photo':forms.ClearableFileInput(attrs={'class':'field','accept':'image/*'}),'is_accepting':forms.CheckboxInput(attrs={'class':'checkbox'})}
    def clean_consultation_fee(self):
        fee = self.cleaned_data['consultation_fee']
        if fee <= 0: raise ValidationError('Consultation fee must be greater than 0.')
        return fee

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient_name','email','phone','appointment_date','time_slot','visit_type','reason']
        labels = {'patient_name':'Patient name','email':'Email address','phone':'Mobile number','appointment_date':'Appointment date','time_slot':'Available time','visit_type':'Visit type','reason':'Reason for visit'}
        help_texts = {'phone':'Use 09XXXXXXXXX or +639XXXXXXXXX.','appointment_date':'Clinic is closed on Sundays.','time_slot':'Slots already booked for this doctor/date are disabled.','reason':'At least 10 characters; maximum 300.'}
        widgets = {'patient_name':forms.TextInput(attrs={'class':'field','autocomplete':'name'}),'email':forms.EmailInput(attrs={'class':'field','autocomplete':'email'}),'phone':forms.TextInput(attrs={'class':'field','placeholder':'09XXXXXXXXX','autocomplete':'tel'}),'appointment_date':forms.DateInput(attrs={'class':'field','type':'date'},format='%Y-%m-%d'),'time_slot':forms.Select(attrs={'class':'field'}),'visit_type':forms.Select(attrs={'class':'field'}),'reason':forms.Textarea(attrs={'class':'field','rows':4,'maxlength':'300','x-model':'reason'})}
    def __init__(self, *args, doctor=None, **kwargs):
        self.doctor = doctor
        super().__init__(*args, **kwargs)
        self.fields['appointment_date'].input_formats = ['%Y-%m-%d']
        if doctor and self.data.get('appointment_date'):
            try:
                chosen = date.fromisoformat(self.data.get('appointment_date'))
                booked = doctor.appointments.filter(appointment_date=chosen).exclude(status='cancelled').values_list('time_slot',flat=True)
                self.fields['time_slot'].choices = [('', 'Choose a time')] + [(v,l) for v,l in Appointment.TIME_SLOTS if v not in booked]
            except (ValueError, TypeError): pass
        else:
            self.fields['time_slot'].choices = [('', 'Choose a time')] + list(Appointment.TIME_SLOTS)
    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not (re.fullmatch(r'09\d{9}', phone) or re.fullmatch(r'\+639\d{9}', phone)):
            raise ValidationError('Enter a valid number: 09XXXXXXXXX or +639XXXXXXXXX.')
        return phone
    def clean_appointment_date(self):
        value = self.cleaned_data['appointment_date']
        if value < date.today(): raise ValidationError('Appointment date cannot be in the past.')
        if value.weekday() == 6: raise ValidationError('The clinic is closed on Sundays.')
        return value
    def clean_reason(self):
        reason = self.cleaned_data['reason'].strip()
        if len(reason) < 10: raise ValidationError('Reason must contain at least 10 characters.')
        return reason
    def clean(self):
        cleaned = super().clean()
        if cleaned.get('visit_type') == 'teleconsultation' and not cleaned.get('email'):
            self.add_error('email', 'Email is required for a teleconsultation.')
        if self.doctor and cleaned.get('appointment_date') and cleaned.get('time_slot'):
            qs = Appointment.objects.filter(doctor=self.doctor, appointment_date=cleaned['appointment_date'], time_slot=cleaned['time_slot']).exclude(status='cancelled')
            if self.instance.pk: qs = qs.exclude(pk=self.instance.pk)
            if qs.exists(): self.add_error('time_slot', 'This time slot has already been booked. Please choose another.')
        return cleaned
