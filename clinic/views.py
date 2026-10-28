from datetime import date
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from .forms import AppointmentForm, DoctorForm
from .models import Appointment, Doctor, Specialty

def is_htmx(request): return request.headers.get('HX-Request') == 'true'
def doctor_list(request):
    qs = Doctor.objects.select_related('specialty').all()
    query = request.GET.get('q','').strip(); specialty = request.GET.get('specialty',''); specialties = [x for x in request.GET.get('specialties','').split(',') if x]; sort = request.GET.get('sort','name')
    if query: qs = qs.filter(Q(full_name__icontains=query)|Q(bio__icontains=query))
    if specialties: qs = qs.filter(specialty__slug__in=specialties)
    elif specialty: qs = qs.filter(specialty__slug=specialty)
    qs = qs.order_by({'fee_low':'consultation_fee','fee_high':'-consultation_fee','name':'full_name'}.get(sort,'full_name'))
    from django.core.paginator import Paginator
    page_obj = Paginator(qs, 6).get_page(request.GET.get('page'))
    ctx = {'page_obj':page_obj,'doctors':page_obj.object_list,'specialties':Specialty.objects.all(),'query':query,'selected_specialty':specialty,'selected_specialties':specialties,'sort':sort,'result_count':qs.count()}
    return render(request, 'clinic/partials/doctor_grid.html' if is_htmx(request) else 'clinic/doctor_list.html', ctx)
def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor.objects.select_related('specialty'), pk=pk)
    upcoming = doctor.appointments.filter(appointment_date__gte=date.today()).exclude(status='cancelled').order_by('appointment_date','time_slot')[:10]
    return render(request,'clinic/doctor_detail.html',{'doctor':doctor,'upcoming':upcoming})
def available_slots(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    raw = request.GET.get('appointment_date','')
    try: chosen = date.fromisoformat(raw)
    except ValueError: chosen = None
    booked = set(doctor.appointments.filter(appointment_date=chosen).exclude(status='cancelled').values_list('time_slot',flat=True)) if chosen else set()
    slots = [{'value':v,'label':l,'booked':v in booked} for v,l in Appointment.TIME_SLOTS]
    return render(request,'clinic/partials/slot_options.html',{'slots':slots,'chosen_date':chosen,'closed_sunday':bool(chosen and chosen.weekday()==6)})
def book_appointment(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if not doctor.is_accepting:
        messages.error(request,'This doctor is not accepting new appointments.')
        return redirect('doctor_detail',pk=doctor.pk)
    if request.method == 'POST':
        form = AppointmentForm(request.POST, doctor=doctor)
        if form.is_valid():
            appointment = form.save(commit=False); appointment.doctor = doctor
            try: appointment.save()
            except Exception:
                form.add_error('time_slot','This time slot is no longer available. Please select another.')
            else:
                if is_htmx(request):
                    response = HttpResponse('')
                    response['HX-Redirect'] = reverse('appointment_confirmation',args=[appointment.pk])
                    response['HX-Trigger'] = 'appointment-booked'
                    return response
                return redirect('appointment_confirmation',pk=appointment.pk)
        if is_htmx(request): return render(request,'clinic/partials/appointment_form_fields.html',{'form':form,'doctor':doctor},status=422)
    else: form = AppointmentForm(doctor=doctor, initial={'appointment_date':date.today().isoformat()})
    return render(request,'clinic/appointment_form.html',{'form':form,'doctor':doctor})
def appointment_confirmation(request, pk):
    appointment = get_object_or_404(Appointment.objects.select_related('doctor','doctor__specialty'),pk=pk)
    return render(request,'clinic/appointment_success.html',{'appointment':appointment})
def manage_doctors(request):
    qs = Doctor.objects.select_related('specialty').all(); q=request.GET.get('q','').strip()
    if q: qs=qs.filter(Q(full_name__icontains=q)|Q(specialty__name__icontains=q))
    return render(request,'clinic/doctor_manage.html',{'doctors':qs,'query':q})
def doctor_create(request):
    form=DoctorForm(request.POST or None,request.FILES or None)
    if request.method=='POST' and form.is_valid():
        form.save(); messages.success(request,'Doctor saved successfully.'); return redirect('manage_doctors')
    return render(request,'clinic/doctor_form.html',{'form':form,'heading':'Add doctor'})
def doctor_edit(request,pk):
    doctor=get_object_or_404(Doctor,pk=pk); form=DoctorForm(request.POST or None,request.FILES or None,instance=doctor)
    if request.method=='POST' and form.is_valid(): form.save(); messages.success(request,'Doctor updated.'); return redirect('manage_doctors')
    return render(request,'clinic/doctor_form.html',{'form':form,'heading':'Edit doctor','doctor':doctor})
def doctor_delete(request,pk):
    doctor=get_object_or_404(Doctor,pk=pk)
    if request.method!='POST': return HttpResponseBadRequest('POST required')
    try: doctor.delete()
    except Exception: return HttpResponse('Cannot delete a doctor with existing appointments.',status=409)
    if is_htmx(request): return HttpResponse('')
    messages.success(request,'Doctor deleted.'); return redirect('manage_doctors')
def toggle_accepting(request,pk):
    doctor=get_object_or_404(Doctor,pk=pk)
    if request.method!='POST': return HttpResponseBadRequest('POST required')
    doctor.is_accepting=not doctor.is_accepting; doctor.save(update_fields=['is_accepting'])
    return render(request,'clinic/partials/doctor_row.html',{'doctor':doctor}) if is_htmx(request) else redirect('manage_doctors')
def manage_appointments(request):
    appointments=Appointment.objects.select_related('doctor','doctor__specialty').all()
    status_data=list(appointments.values('id','status'))
    return render(request,'clinic/appointment_manage.html',{'appointments':appointments,'appointment_status_data':status_data})
def appointment_status(request,pk,status):
    appointment=get_object_or_404(Appointment.objects.select_related('doctor'),pk=pk)
    if request.method!='POST' or status not in ('confirmed','cancelled'): return HttpResponseBadRequest('Invalid action')
    appointment.status=status; appointment.save(update_fields=['status'])
    if is_htmx(request):
        response=render(request,'clinic/partials/appointment_row.html',{'appointment':appointment})
        response['HX-Trigger']='appointment-updated'
        return response
    messages.success(request,f'Appointment {appointment.reference} marked {status}.'); return redirect('manage_appointments')
def custom_404(request, exception):
    if is_htmx(request): return HttpResponse('<div class="inline-error" role="alert">The requested record was not found. Refresh and try again.</div>',status=404)
    return render(request,'clinic/404.html',status=404)
