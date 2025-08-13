function toggleFormSections() {
    const selected = document.getElementById('request_form').value.toLowerCase();
    const sections = document.querySelectorAll('.form-section');
    sections.forEach(sec => sec.classList.add('d-none'));

    if (selected === 'leave') {
        document.getElementById('leave-form').classList.remove('d-none');
    } else if (selected === 'clearance') {
        document.getElementById('clearance-form').classList.remove('d-none');
    } else if (selected === 'salary advance') {
        document.getElementById('salary-form').classList.remove('d-none');
    } else if (selected === 'certificate') {
        document.getElementById('certificate-form').classList.remove('d-none');
    }
}


