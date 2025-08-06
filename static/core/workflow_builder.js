// let allConfigs = {};
const stepCounters = {form: 0, email: 0, timer: 0, approval: 0, condition: 0, webhook: 0};

// Show Notification ()
function showNotification(message, type = 'success', duration = 5000) {
    const notif = document.getElementById("notification");
    notif.className = type;
    notif.textContent = message;
    notif.style.display = 'block';
    notif.classList.add("show");
    setTimeout(() => notif.classList.remove("show"), duration - 500);

    setTimeout(() => {
        notif.style.display = 'none';
        notif.className = '';
        notif.textContent = '';
    }, duration);

}

function renumberStepsByType() {
    const dropzone = document.getElementById('workflow-canvas');
    const steps = dropzone.querySelectorAll('li');

    const counters = {};  // { form: 1, timer: 2, ... }

    steps.forEach(li => {
        const type = li.dataset.type;
        if (!counters[type]) counters[type] = 1;
        else counters[type]++;

        const label = li.querySelector('.step-label');
        if (label) {
            label.textContent = `${type.charAt(0).toUpperCase() + type.slice(1)} Step ${counters[type]}`;
        }
    });
}


document.addEventListener("DOMContentLoaded", function () {
    // Restore config from backend


    // 🟢 Make toolbox draggable
    document.querySelectorAll('.draggable').forEach(item => {
        item.addEventListener('dragstart', e => {
            e.dataTransfer.setData('type', item.dataset.type);
            e.dataTransfer.setData('origin', 'sidebar');
        });
    });

    const dropzone = document.getElementById('workflow-canvas');

    // 🟢 Drop logic
    dropzone.addEventListener('dragover', e => e.preventDefault());

    dropzone.addEventListener('drop', e => {
        e.preventDefault();
        const type = e.dataTransfer.getData('type');
        const origin = e.dataTransfer.getData('origin');
        if (origin !== 'sidebar') return;

        stepCounters[type] += 1;
        const stepId = `temp-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

        const li = document.createElement('li');
        li.dataset.type = type;
        li.dataset.stepId = stepId;
        li.innerHTML = `
      <span class="step-label">${type.charAt(0).toUpperCase() + type.slice(1)} Step ${stepCounters[type]}</span>
      <button class="delete-step" title="Remove this step">✖</button>
    `;

        li.setAttribute('draggable', 'true');
        li.addEventListener('dragstart', function (e) {
            e.dataTransfer.setData('type', type);
            e.dataTransfer.setData('origin', 'canvas');
        });

        dropzone.appendChild(li);
        renumberStepsByType();

    });

    // 🟢 Delete step
    dropzone.addEventListener('click', function (e) {
        if (e.target.classList.contains('delete-step')) {
            e.preventDefault();
            e.stopPropagation();  // ✅ prevent modal from opening
            e.target.closest('li').remove();
            renumberStepsByType();  // 🔁 Recalculate step numbers
            return;
        }

        const li = e.target.closest('li');
        if (li) {
            openStepModal(li.dataset.type, li.dataset.stepId);
        }
    });

    // 🟢 Make sortable
    new Sortable(dropzone, {
        animation: 150,
        onEnd: () => {
            document.querySelectorAll('#workflow-canvas li').forEach((li, i) => {
                li.dataset.index = i;
            });
            renumberStepsByType();  // 🔁 Live renumber after reorder
        }
    });

    // * 🟢 Modal open
    /*dropzone.addEventListener('click', function (e) {
        const li = e.target.closest('li');
        if (!li) return;
        openStepModal(li.dataset.type, li.dataset.stepId);
    }); */

    // 🟢 Modal form save
    document.getElementById('modal-form').addEventListener('submit', function (e) {
        e.preventDefault();
        const modal = document.getElementById('step-config-modal');
        const stepId = modal.dataset.stepId;
        const config = {};
        const stepType = modal.dataset.type;
        if (stepType === 'form') {
            const fields = [];
            document.querySelectorAll('.field-row').forEach((row, i) => {
                fields.push({
                    label: row.querySelector(`[name=field_label_${i}]`)?.value || '',
                    field_type: row.querySelector(`[name=field_type_${i}]`)?.value || 'text',
                    required: row.querySelector(`[name=field_required_${i}]`)?.checked || false,
                    choices: row.querySelector(`[name=field_choices_${i}]`)?.value || '',
                });
            });
            config.fields = fields;
        }
        const formData = new FormData(e.target);

        formData.forEach((val, key) => config[key] = val);
        allConfigs[stepId] = config;
        closeStepModal();

        // 🔁 Highlight saved step temporarily
        const savedLi = document.querySelector(`#workflow-canvas li[data-step-id="${stepId}"]`);
        if (savedLi) {
            savedLi.classList.add("step-saved");
            setTimeout(() => savedLi.classList.remove("step-saved"), 1500);
        }
    });

    // 🟢 Save to backend via fetch
    document.getElementById("save-workflow").addEventListener("click", function () {
        const steps = [];
        document.querySelectorAll("#workflow-canvas li").forEach((li, index) => {
            steps.push({
                id: li.dataset.stepId,
                order: index + 1,
                type: li.dataset.type,
                name: li.querySelector(".step-label")?.innerText || `Step ${index + 1}`
            });
        });

        fetch(window.location.href, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken(),
            },
            body: JSON.stringify({steps: steps, configs: allConfigs})
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showNotification("✅ Workflow saved!", "success");
                } else {
                    showNotification("❌ Failed to save workflow.", "error");
                }
            })
            .catch(err => {
                alert("❌ Save failed.");
                console.error(err);
            });
    });

});

function addFieldRow(field = {}, index = null) {
    if (index === null) {
        index = document.querySelectorAll(".field-row").length;
    }

    const row = document.createElement("div");
    row.className = "field-row";
    row.innerHTML = `
    <label>Label: <input name="field_label_${index}" value="${field.label || ''}"></label>
    <label>Type:
        <select name="field_type_${index}">
          <option value="text" ${field.field_type === 'text' ? 'selected' : ''}>Text</option>
          <option value="textarea" ${field.field_type === 'textarea' ? 'selected' : ''}>Textarea</option>
          <option value="email" ${field.field_type === 'email' ? 'selected' : ''}>Email</option>
          <option value="number" ${field.field_type === 'number' ? 'selected' : ''}>Number</option>
          <option value="phone" ${field.field_type === 'phone' ? 'selected' : ''}>Phone</option>
          <option value="url" ${field.field_type === 'url' ? 'selected' : ''}>URL</option>
        
          <option value="date" ${field.field_type === 'date' ? 'selected' : ''}>Date</option>
          <option value="time" ${field.field_type === 'time' ? 'selected' : ''}>Time</option>
          <option value="datetime" ${field.field_type === 'datetime' ? 'selected' : ''}>DateTime</option>
        
          <option value="range_date" ${field.field_type === 'range_date' ? 'selected' : ''}>Date Range</option>
          <option value="range_time" ${field.field_type === 'range_time' ? 'selected' : ''}>Time Range</option>
          <option value="range_datetime" ${field.field_type === 'range_datetime' ? 'selected' : ''}>DateTime Range</option>
        
          <option value="choice" ${field.field_type === 'choice' ? 'selected' : ''}>Dropdown</option>
          <option value="multi_choice" ${field.field_type === 'multi_choice' ? 'selected' : ''}>Multi-Select</option>
        
          <option value="checkbox" ${field.field_type === 'checkbox' ? 'selected' : ''}>Checkbox</option>
          <option value="file" ${field.field_type === 'file' ? 'selected' : ''}>File Upload</option>
          <option value="password" ${field.field_type === 'password' ? 'selected' : ''}>Password</option>
        
          <option value="section_heading" ${field.field_type === 'section_heading' ? 'selected' : ''}>Section Heading</option>
          <option value="html_note" ${field.field_type === 'html_note' ? 'selected' : ''}>HTML Note</option>
        </select>

    </label>
    <div class="field-inline">
      <label for="field_required_${index}">Required:</label>
      <input type="checkbox" id="field_required_${index}" name="field_required_${index}" ${field.required ? 'checked' : ''}>
    </div>

    <label>Choices (CSV): <input name="field_choices_${index}" value="${field.choices || ''}"></label>
    <br><br>
  `;
    document.getElementById("field-configs").appendChild(row);
}


function openStepModal(type, id) {
    const modal = document.getElementById("step-config-modal");
    modal.dataset.stepId = id;
    modal.dataset.type = type;
    const config = allConfigs[id] || {};
    document.getElementById("modal-title").textContent = `Configure ${type} Step`;

    const fields = {
        form: `
      <label>Title: <input name="title" required value="${config.title || ''}"></label>
      <div id="field-configs"></div>
    `,
        email: `
      <label>Subject: <input name="subject" required value="${config.subject || ''}"></label>
      <label>Body:<br><textarea name="body" rows="4">${config.body || ''}</textarea></label>
    `,
        timer: `<label>Delay (in seconds): <input name="delay" type="number" min="1" required value="${config.delay || ''}"></label>`,
        approval: `<label>Approver Email: <input name="approver" value="${config.approver || ''}"></label>`,
        condition: `<label>Condition logic: <input name="logic" value="${config.logic || ''}" placeholder="e.g. amount > 10000"></label>`,
        webhook: `<label>Webhook URL: <input name="url" type="url" value="${config.url || ''}"></label>`
    };

    const body = document.getElementById("modal-body");
    body.innerHTML = fields[type] || `<p>No config available for this step type.</p>`;

    // Load existing field configs if form step
    if (type === "form") {
        const savedFields = config.fields || [];
        savedFields.forEach((field, i) => addFieldRow(field, i));

        const addFieldBtn = document.createElement("button");
        addFieldBtn.type = "button";
        addFieldBtn.textContent = "➕ Add Field";
        addFieldBtn.onclick = () => addFieldRow();
        document.getElementById("field-configs").after(addFieldBtn);
    }

    modal.style.display = "block";
}


function closeStepModal() {
    document.getElementById("step-config-modal").style.display = 'none';
}

function getCSRFToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]").value;
}