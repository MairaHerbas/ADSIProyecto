export async function loadProfileContent(contentArea) {
    contentArea.innerHTML = '<div style="color:#aaa; text-align:center; padding:40px; font-family:\'Courier New\'">Cargando datos...</div>';

    try {
        const res = await fetch('/api/profile-details');
        if(!res.ok) throw new Error("Error fetching profile");
        
        const profileData = await res.json();
        renderProfileUI(profileData, contentArea);

    } catch (e) {
        console.error(e);
        contentArea.innerHTML = '<div style="color:#e06c75; text-align:center;">Error de conexión con el Servidor</div>';
    }
}

function renderProfileUI(data, containerEl) {
    const container = document.createElement('div');
    container.className = 'profile-container';

    const title = document.createElement('h2');
    title.className = 'profile-title';
    title.textContent = data.title;
    container.appendChild(title);

    data.fields.forEach(field => {
        const row = document.createElement('div');
        row.className = 'profile-row';
        row.id = `row-${field.id}`;

        const infoGroup = document.createElement('div');
        infoGroup.className = 'data-group';
        
        const label = document.createElement('span');
        label.className = 'data-label';
        label.textContent = field.label;

        const value = document.createElement('span');
        value.className = 'data-value';
        value.textContent = field.value;
        value.id = `val-${field.id}`;

        infoGroup.appendChild(label);
        infoGroup.appendChild(value);
        row.appendChild(infoGroup);

        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'controls-area';

        if (field.editable) {
            const editBtn = document.createElement('button');
            editBtn.className = 'edit-btn';
            const icon = document.createElement('div');
            icon.className = 'edit-icon';
            editBtn.appendChild(icon);
            editBtn.onclick = () => enableEditMode(row, field, value, controlsDiv);
            controlsDiv.appendChild(editBtn);
        }

        row.appendChild(controlsDiv);
        container.appendChild(row);
    });

    containerEl.innerHTML = '';
    containerEl.appendChild(container);
}

function enableEditMode(row, fieldData, valueSpan, controlsDiv) {
    const currentVal = valueSpan.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentVal;
    input.className = 'edit-input';
    
    // Reemplazo en DOM
    valueSpan.replaceWith(input);
    input.focus();
    controlsDiv.innerHTML = ''; 

    // --- NUEVO: SOPORTE TECLADO (ENTER / ESCAPE) ---
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            saveEdit(fieldData.id, input.value, row, input, controlsDiv);
        } else if (e.key === 'Escape') {
            cancelEdit(currentVal, row, input, controlsDiv, fieldData);
        }
    });
    // ------------------------------------------------

    const actionGroup = document.createElement('div');
    actionGroup.className = 'action-group';

    const btnAccept = document.createElement('button');
    btnAccept.className = 'action-btn btn-accept';
    btnAccept.textContent = 'ACEPTAR';
    btnAccept.onclick = () => saveEdit(fieldData.id, input.value, row, input, controlsDiv);

    const btnCancel = document.createElement('button');
    btnCancel.className = 'action-btn btn-cancel';
    btnCancel.textContent = 'CANCELAR';
    btnCancel.onclick = () => cancelEdit(currentVal, row, input, controlsDiv, fieldData);

    actionGroup.appendChild(btnAccept);
    actionGroup.appendChild(btnCancel);
    controlsDiv.appendChild(actionGroup);
}

async function saveEdit(id, newValue, row, inputEl, controlsDiv) {
    const inputs = row.querySelectorAll('button, input');
    inputs.forEach(el => el.disabled = true);

    try {
        const res = await fetch('/api/profile-update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id, value: newValue })
        });
        const result = await res.json();

        if (result.success) {
            restoreViewMode(row, inputEl, result.newValue, controlsDiv, true, id);
        } else {
            alert("Error: " + result.error);
            // Si falla, restauramos el valor que tenía el input actualmente (o el original)
            cancelEdit(inputEl.value, row, inputEl, controlsDiv, {id: id});
        }
    } catch (e) {
        alert("Error de red");
        cancelEdit(inputEl.value, row, inputEl, controlsDiv, {id: id});
    }
}

function cancelEdit(originalValue, row, inputEl, controlsDiv, fieldData) {
    restoreViewMode(row, inputEl, originalValue, controlsDiv, true, fieldData.id);
}

function restoreViewMode(row, inputEl, finalValue, controlsDiv, isEditable, fieldId) {
    const span = document.createElement('span');
    span.className = 'data-value';
    span.textContent = finalValue;
    span.id = `val-${fieldId}`;
    
    inputEl.replaceWith(span);
    controlsDiv.innerHTML = '';
    
    if (isEditable) {
        const editBtn = document.createElement('button');
        editBtn.className = 'edit-btn';
        const icon = document.createElement('div');
        icon.className = 'edit-icon';
        editBtn.appendChild(icon);
        const fieldDataStub = { id: fieldId, editable: true }; 
        editBtn.onclick = () => enableEditMode(row, fieldDataStub, span, controlsDiv);
        controlsDiv.appendChild(editBtn);
    }
}