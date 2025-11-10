document.addEventListener("DOMContentLoaded", function () {
    const fromInput = document.getElementById("from_date");
    const toInput = document.getElementById("to_date");
    const rejoinInput = document.getElementById("rejoin_date");
    const lastworkingdateInput = document.getElementById("last_working_date");
    const departuredateInput = document.getElementById("departure_date");

    let today = new Date();

    // Get first day of previous month
    let prevMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    let year = prevMonth.getFullYear();
    let month = String(prevMonth.getMonth() + 1).padStart(2, '0');
    let day = "01";
    let minDate = `${year}-${month}-${day}`;

    // Allow previous month onwards
    if (fromInput) {
        fromInput.setAttribute("min", minDate);
    }
    if (toInput) {
        toInput.setAttribute("min", minDate);
    }
    if (rejoinInput) {
        rejoinInput.setAttribute("min", minDate);
    }
    if (lastworkingdateInput) {
        lastworkingdateInput.setAttribute("min", minDate);
    }
    if (departuredateInput) {
        departuredateInput.setAttribute("min", minDate);
    }

    // Hook into calculate function
    if (fromInput) fromInput.addEventListener("change", calculateTotalDays);
    if (toInput) toInput.addEventListener("change", calculateTotalDays);
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

