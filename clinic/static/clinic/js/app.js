document.addEventListener('alpine:init', () => {
  Alpine.store('theme', {
    dark: Alpine.$persist(false).as('medibook-dark'),
    toggle() { this.dark = !this.dark; }
  });
  Alpine.store('layout', { view: Alpine.$persist('grid').as('medibook-doctor-view') });
  Alpine.store('toasts', {
    items: [], nextId: 1,
    add(message, kind='success') {
      const id = this.nextId++;
      this.items.push({id, message, kind});
      window.setTimeout(() => this.remove(id), 4000);
    },
    remove(id) { this.items = this.items.filter(item => item.id !== id); }
  });
  Alpine.data('appShell', () => ({
    menuOpen: false,
    init() {
      window.addEventListener('toast', event => this.$store.toasts.add(event.detail?.message || 'Updated', event.detail?.kind || 'success'));
      window.addEventListener('appointment-booked', () => this.$store.toasts.add('Appointment submitted', 'success'));
      window.addEventListener('open-cancel', event => window.dispatchEvent(new CustomEvent('cancel-dialog-open', {detail:event.detail})));
    }
  }));
  Alpine.data('doctorCard', () => ({ expanded: false }));
  Alpine.data('searchBox', () => ({
    query: '', selectedSpecialties: [],
    toggleSpecialty(slug) { this.selectedSpecialties = this.selectedSpecialties.includes(slug) ? this.selectedSpecialties.filter(s => s !== slug) : [...this.selectedSpecialties, slug]; },
    init() { this.query = this.$refs.search?.value || ''; this.$watch('query', value => { if (this.$refs.search) this.$refs.search.value = value; }); }
  }));
  Alpine.data('gridView', () => ({
    get view() { return this.$store.layout.view; },
    set view(value) { this.$store.layout.view = value; }
  }));
  Alpine.data('tabs', names => ({ tabs:names, active:0 }));
  Alpine.data('bookingWizard', () => ({
    step:1, reason:'',
    get stepName() { return ['Patient info','Schedule','Review'][this.step-1] || 'Review'; },
    get canAdvance() {
      if (this.step===1) return !!document.getElementById('id_patient_name')?.value.trim() && !!document.getElementById('id_phone')?.value.trim();
      if (this.step===2) return !!document.getElementById('id_appointment_date')?.value && !!document.getElementById('id_time_slot')?.value && !!document.getElementById('id_visit_type')?.value && (document.getElementById('id_reason')?.value.trim().length >= 10);
      return true;
    },
    get remaining() { return Math.max(0, 300 - (document.getElementById('id_reason')?.value.length || 0)); },
    init() { this.$nextTick(() => { const r=document.getElementById('id_reason'); if(r) {this.reason=r.value; r.addEventListener('input',()=>this.reason=r.value);} }); this.$watch('step', () => this.$nextTick(()=>document.querySelector('.form-panel')?.scrollIntoView({block:'nearest',behavior:'smooth'}))); },
    syncStep() { const r=document.getElementById('id_reason'); if(r) this.reason=r.value; }
  }));
  Alpine.data('appointmentFilters', () => ({
    active:'all', rows:[], serverData:[],
    init() { const source=document.getElementById('appointment-status-data'); if(source) { try { this.serverData=JSON.parse(source.textContent); } catch(e) { this.serverData=[]; } } this.rows = [...this.$el.querySelectorAll('tbody tr[data-status]')]; this.updateCounts(); this.$el.addEventListener('htmx:afterSwap', () => this.updateCounts()); },
    get counts() { const result={all:this.rows.length,pending:0,confirmed:0,cancelled:0}; this.rows.forEach(row=>{ if(row.dataset.status in result) result[row.dataset.status]++; }); return result; },
    updateCounts() { this.rows=[...this.$el.querySelectorAll('tbody tr[data-status]')]; }
  }));
  Alpine.data('cancelDialog', () => ({open:false, url:'', reference:'', init(){window.addEventListener('cancel-dialog-open', e=>{this.url=e.detail.url;this.reference=e.detail.reference;this.open=true;this.$nextTick(()=>this.$refs.cancelButton?.focus());});}, close(){this.open=false;}, submit(){htmx.ajax('POST',this.url,{target:'#appointment-'+this.url.match(/appointments\/(\d+)/)?.[1],swap:'outerHTML',values:{csrfmiddlewaretoken:document.querySelector('[name=csrfmiddlewaretoken]')?.value}});this.open=false;window.dispatchEvent(new CustomEvent('toast',{detail:{message:this.reference+' cancelled',kind:'success'}}));}}));
});
document.addEventListener('htmx:beforeRequest', () => document.documentElement.classList.add('htmx-loading'));
document.addEventListener('htmx:afterRequest', () => document.documentElement.classList.remove('htmx-loading'));
document.addEventListener('htmx:responseError', event => { if(event.detail.xhr.status===404) window.dispatchEvent(new CustomEvent('toast',{detail:{message:'The requested record was not found.',kind:'error'}})); });
