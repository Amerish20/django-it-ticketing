function calculateDays() {
    const fromInput = document.getElementById("id_from_date");
    const toInput = document.getElementById("id_to_date");
    const totalDaysInput = document.getElementById("id_total_days");

    if (!fromInput || !toInput || !totalDaysInput) return;

    const fromDate = new Date(fromInput.value);
    const toDate = new Date(toInput.value);

    if (!isNaN(fromDate) && !isNaN(toDate)) {
        const timeDiff = toDate.getTime() - fromDate.getTime();
        const days = Math.floor(timeDiff / (1000 * 3600 * 24)) + 1;
        totalDaysInput.value = days > 0 ? days : '';
    } else {
        totalDaysInput.value = '';
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const fromInput = document.getElementById("id_from_date");
    const toInput = document.getElementById("id_to_date");

    if (fromInput) fromInput.addEventListener("change", calculateDays);
    if (toInput) toInput.addEventListener("change", calculateDays);
});


//Frontend code for popup
function calculateTotalDays() {
    const fromDateInput = document.getElementById('from_date');
    const toDateInput = document.getElementById('to_date');
    const totalDaysInput = document.getElementById('total_days');
    const totalDaysContainer = document.getElementById('total-days-container');

    const from = new Date(fromDateInput.value);
    const to = new Date(toDateInput.value);

    if (fromDateInput.value && toDateInput.value && !isNaN(from) && !isNaN(to)) {
        const diffTime = Math.abs(to - from);
        const days = Math.ceil(diffTime / (1000 * 60 * 60 * 24))+1;
        totalDaysInput.value = days;

        // Show total_days only if both dates are selected
        totalDaysContainer.classList.remove('d-none');
    } else {
        totalDaysInput.value = '';
        totalDaysContainer.classList.add('d-none');
    }
}

