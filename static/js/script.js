// MediCare - Healthcare Management System
// Client-side helper scripts

document.addEventListener('DOMContentLoaded', function () {
  // Demo login credentials quick-fill helper
  window.fillDemo = function (role) {
    const userField = document.getElementById('username');
    const passField = document.getElementById('password');
    const roleSelect = document.getElementById('role');

    if (!userField || !passField) return;

    if (role === 'admin') {
      userField.value = 'admin';
      passField.value = 'admin123';
      if (roleSelect) roleSelect.value = 'ADMIN';
    } else if (role === 'doctor') {
      userField.value = 'doctor1';
      passField.value = 'doctor123';
      if (roleSelect) roleSelect.value = 'DOCTOR';
    } else if (role === 'patient') {
      userField.value = 'patient1';
      passField.value = 'patient123';
      if (roleSelect) roleSelect.value = 'PATIENT';
    }
  };

  // Dynamic Medicine Row Adder for Doctor Consultation page
  const addMedBtn = document.getElementById('add-medicine-btn');
  const medContainer = document.getElementById('medicine-rows-container');

  if (addMedBtn && medContainer) {
    addMedBtn.addEventListener('click', function () {
      const rowCount = medContainer.querySelectorAll('.medicine-row').length + 1;
      const row = document.createElement('div');
      row.className = 'medicine-row form-row';
      row.style.marginBottom = '12px';
      row.style.padding = '10px';
      row.style.background = '#f8fafc';
      row.style.border = '1px solid #e2e8f0';
      row.style.borderRadius = '6px';

      row.innerHTML = `
        <div class="form-group" style="margin-bottom: 0;">
          <label style="font-size: 11px;">Medicine Name *</label>
          <input type="text" name="med_name[]" class="form-control" placeholder="e.g. Amoxicillin" required>
        </div>
        <div class="form-group" style="margin-bottom: 0;">
          <label style="font-size: 11px;">Dosage *</label>
          <input type="text" name="med_dosage[]" class="form-control" placeholder="e.g. 250 mg" required>
        </div>
        <div class="form-group" style="margin-bottom: 0;">
          <label style="font-size: 11px;">Frequency *</label>
          <input type="text" name="med_frequency[]" class="form-control" placeholder="e.g. Twice daily" required>
        </div>
        <div class="form-group" style="margin-bottom: 0;">
          <label style="font-size: 11px;">Duration *</label>
          <input type="text" name="med_duration[]" class="form-control" placeholder="e.g. 5 days" required>
        </div>
        <div class="form-group" style="margin-bottom: 0;">
          <label style="font-size: 11px;">Instructions</label>
          <input type="text" name="med_instructions[]" class="form-control" placeholder="e.g. After food">
        </div>
        <div style="display: flex; align-items: flex-end;">
          <button type="button" class="btn btn-danger btn-sm" onclick="this.closest('.medicine-row').remove()">Remove</button>
        </div>
      `;
      medContainer.appendChild(row);
    });
  }

  // Print Prescription
  window.printPrescription = function () {
    window.print();
  };
});
