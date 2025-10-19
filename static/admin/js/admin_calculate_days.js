document.addEventListener("DOMContentLoaded", function () {
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
        if (toInput) toInput.addEventListener("change", calculateRejoinDays);
        if (fromInput) fromInput.addEventListener("change", calculateRejoinDays);
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
});
