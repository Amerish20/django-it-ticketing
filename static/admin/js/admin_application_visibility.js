document.addEventListener('DOMContentLoaded', function () {

    const saveContinueBtn = document.querySelector('.default.save-continuete'); // Save and continue editing
    const saveAddAnotherBtn = document.querySelector('.default.save-addanother'); // Save and add another
    const saveContinueBtn2 = document.querySelector('input[name="_continue"]'); // alternative selector
    const saveAddAnotherBtn2 = document.querySelector('input[name="_addanother"]'); // alternative selector

    if (saveContinueBtn) saveContinueBtn.style.display = 'none';
    if (saveAddAnotherBtn) saveAddAnotherBtn.style.display = 'none';
    if (saveContinueBtn2) saveContinueBtn2.style.display = 'none';
    if (saveAddAnotherBtn2) saveAddAnotherBtn2.style.display = 'none';

    const deleteLink = document.querySelector('.deletelink');
    if (deleteLink) {
        deleteLink.textContent = 'Permanently Delete';
        deleteLink.style.color = 'white';
        deleteLink.style.fontWeight = 'bold';
    }

    const requestForm = document.getElementById("id_request_form");
    const fromInput = document.getElementById("id_from_date");
    const toInput = document.getElementById("id_to_date");
    const rejoinInput = document.getElementById("id_rejoin_date");
    const delayedDaysInput = document.getElementById("id_delayed_days");
    const totalDaysAfterRejoinInput = document.getElementById("id_total_days_after_rejoin");
    const totalDaysInput = document.getElementById("id_total_days");

    // Auto-calc for Leave total days
    if (fromInput && toInput && totalDaysInput) {
        fromInput.addEventListener("change", calculateDays);
        toInput.addEventListener("change", calculateDays);
    }

    // Auto-calc for Rejoining delay days
    if (rejoinInput) {
        rejoinInput.addEventListener("change", calculateRejoinDays);
    }

    function getSelectedRequestFormId() {
        return requestForm ? parseInt(requestForm.value) : null;
    }

    function calculateDays() {
        const fromDate = new Date(fromInput.value);
        const toDate = new Date(toInput.value);
        if (!isNaN(fromDate) && !isNaN(toDate)) {
            const timeDiff = toDate - fromDate;
            const days = Math.floor(timeDiff / (1000 * 3600 * 24)) + 1;
            totalDaysInput.value = days > 0 ? days : "";
        } else {
            totalDaysInput.value = "";
        }
    }

    function calculateRejoinDays() {
        const formId = getSelectedRequestFormId();

        // Only for "Rejoining" form (request_form_id == 2)
        if (formId !== 2) return;

        const fromDate = new Date(fromInput.value);
        const toDate = new Date(toInput.value);
        const rejoinDate = new Date(rejoinInput.value);

        if (!isNaN(fromDate) && !isNaN(toDate) && !isNaN(rejoinDate)) {
            let delayedDays = 0;

            if (rejoinDate > toDate) {
                delayedDays = Math.floor((rejoinDate - toDate) / (1000 * 3600 * 24)) - 1;
                if (delayedDays < 0) delayedDays = 0;
            }

            const totalAfter = Math.floor((rejoinDate - fromDate) / (1000 * 3600 * 24));

            delayedDaysInput.value = delayedDays >= 0 ? delayedDays : "";
            totalDaysAfterRejoinInput.value = totalAfter >= 0 ? totalAfter : "";
        } else {
            delayedDaysInput.value = "";
            totalDaysAfterRejoinInput.value = "";
        }
    }
    
    const fields = {
        leave: [
            'id_rejoin_date', 'id_delayed_days', 'id_total_days_after_rejoin',
            'id_rejoin_status', 'id_rejoin_remarks', 'id_application_id_rejoin',
            'id_salary_ad_month', 'id_salary_ad_year'
        ],
        salary: [
            'id_total_days', 'id_leave_type', 'id_from_date', 'id_to_date',
            'id_rejoin_date', 'id_delayed_days', 'id_total_days_after_rejoin',
            'id_rejoin_status', 'id_rejoin_remarks', 'id_application_id_rejoin'
        ],
        rejoining: [
            'id_rejoin_status', 'id_leave_type', 'id_salary_ad_month', 'id_salary_ad_year', 'id_remarks', 
            'id_remarks_dep_head', 'id_remarks_hr', 'id_remarks_gm','id_rejoin_remarks'
        ]
    };

    function toggleFields() {
        const selected = requestForm?.value || '';

        // show all fields first
        document.querySelectorAll('.form-row, .form-group').forEach(row => row.style.display = '');

        // make sure from/to date are editable again
        setReadOnly('#id_from_date', false);
        setReadOnly('#id_to_date', false);

        if (selected == '1') { 
            // Leave
            hide(fields.leave);
            setReadOnlyOrDisable('#id_request_form', true);
            setReadOnlyOrDisable('#id_user', true);

        } else if (selected == '2') { 
            // Rejoining
            hide(fields.rejoining);

            // make from/to date read-only in Rejoining mode
            setReadOnlyOrDisable('#id_request_form', true);
            setReadOnlyOrDisable('#id_user', true);
            setReadOnlyOrDisable('#id_from_date', true);
            setReadOnlyOrDisable('#id_to_date', true);

        } else if (selected == '3') { 
            // Salary Advance
            hide(fields.salary);
            setReadOnlyOrDisable('#id_request_form', true);
            setReadOnlyOrDisable('#id_user', true);
        }
    }

    function hide(fieldIds) {
        fieldIds.forEach(id => {
            const el = document.querySelector(`#${id}`);
            if (el) {
                const row = el.closest('.form-row, .form-group');
                if (row) row.style.display = 'none';
            }
        });
    }

    // Helper to toggle readonly + styling
    function setReadOnly(selector, state) {
        const field = document.querySelector(selector);
        if (field) {
            field.readOnly = state;
            field.style.backgroundColor = state ? '#eee' : '';
        }
    }

    function setReadOnlyOrDisable(selector, readonly = true) {
        const field = document.querySelector(selector);
        if (!field) return;

        if (field.tagName === 'SELECT') {
            // For dropdowns
            field.style.pointerEvents = readonly ? 'none' : 'auto';
            field.style.backgroundColor = readonly ? '#eee' : '';
        } else {
            // For text or date inputs
            field.readOnly = readonly;
            field.style.backgroundColor = readonly ? '#eee' : '';
        }
    }

    if (requestForm) {
        toggleFields(); // run on load
        requestForm.addEventListener('change', toggleFields);
    }
    
});
