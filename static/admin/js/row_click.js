document.addEventListener('DOMContentLoaded', function () {
  const table = document.querySelector('#result_list');
  if (!table) return;

  table.querySelectorAll('tbody tr').forEach(function (tr) {
    // First column usually holds the edit link
    const link = tr.querySelector('th a, td:first-child a');
    if (!link) return;

    tr.style.cursor = 'pointer';
    tr.addEventListener('click', function (e) {
      // Don’t hijack clicks on real controls/links
      if (e.target.closest('a, input, button, label, select, .action-select')) return;

      if (e.ctrlKey || e.metaKey) {
        window.open(link.href, '_blank');
      } else {
        window.location.href = link.href;
      }
    });
  });
});