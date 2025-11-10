function toggleFormSections() {
  const selected = document.getElementById('request_form').value;
  const sections = document.querySelectorAll('.form-section');
  sections.forEach(sec => {
    // remove required from inputs in hidden sections
    sec.classList.add('d-none');
    sec.querySelectorAll('[required]').forEach(el => el.removeAttribute('required'));
  });

  let activeSection = null;

  if (selected === '1') { // leave
    activeSection = document.getElementById('leave-form');
    // fetch leave types for this request_form
    fetch(`/get-leave-types/${selected}/`)
      .then(response => response.json())
      .then(data => {
        const leaveTypeSelect = document.getElementById('leave_type');
        leaveTypeSelect.innerHTML = '<option value="">Select Leave Type</option>';
        data.forEach(item => {
          leaveTypeSelect.innerHTML += `<option value="${item.id}">${item.name}</option>`;
        });
      });
  } else if (selected === '2') { //rejoining
    activeSection = document.getElementById('rejoin-form');
  } else if (selected === '3') { // salary advance
    activeSection = document.getElementById('salary-form');
  } else if (selected === '4') { // clearance
    activeSection = document.getElementById('clearance-form');
    // fetch clearance types for this request_form
    fetch(`/get-leave-types/${selected}/`)
      .then(response => response.json())
      .then(data => {
        const clearanceTypeSelect = document.getElementById('clearance_type');
        clearanceTypeSelect.innerHTML = '<option value="">Select Clearance Type</option>';
        data.forEach(item => {
          clearanceTypeSelect.innerHTML += `<option value="${item.id}">${item.name}</option>`;
        });
      });
  }

  if (activeSection) {
    activeSection.classList.remove('d-none');
    // reapply required only for active section
    activeSection.querySelectorAll('select,input,textarea').forEach(el => {
      if (el.dataset.mustRequired === "1") {
        el.setAttribute('required', 'required');
      }
    });
  }
}
