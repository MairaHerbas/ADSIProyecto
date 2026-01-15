import { setupScrollLogic } from '../logic.js';
import { IOSDatePicker } from './date-picker.js';

const ulNotifs = document.getElementById('list-notifs-ul');
const btnRefresh = document.getElementById('btn-refresh-notifs');
let cachedNotifications = [];
let pickerStart, pickerEnd;

const activeFilters = { users: new Set(), types: new Set() };

export function setupNotificationLogic() {
    btnRefresh.addEventListener('click', loadNotifications);
    document.addEventListener('click', (e) => {
        if (IOSDatePicker.isGlobalDragging) return;
        if(!e.target.closest('.filter-btn')) document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    });

    const ddDate = document.getElementById('dd-date');
    if (ddDate) {
        ddDate.innerHTML = `
            <div class="dd-item selected" data-val="all">CUALQUIERA</div>
            <div class="picker-range-wrapper">
                <div class="picker-group"><div class="picker-label">DESDE</div><div id="ios-picker-start" class="ios-picker"></div></div>
                <div class="picker-group"><div class="picker-label">HASTA</div><div id="ios-picker-end" class="ios-picker"></div></div>
            </div>
            <button id="btn-today-action" class="btn-today">HASTA HOY</button>
        `;

        const today = new Date();
        const lastMonth = new Date(); lastMonth.setMonth(today.getMonth() - 1);

        // Pasamos 'today' como tercer argumento (maxDate)
        pickerStart = new IOSDatePicker('ios-picker-start', lastMonth, today, () => applyFilters());
        pickerEnd = new IOSDatePicker('ios-picker-end', today, today, () => applyFilters());

        pickerStart.linkedPicker = pickerEnd; pickerStart.isStartPicker = true;
        pickerEnd.linkedPicker = pickerStart; pickerEnd.isStartPicker = false;

        document.getElementById('btn-today-action').addEventListener('click', () => {
            pickerEnd.scrollToDate({ day: today.getDate(), month: today.getMonth(), year: today.getFullYear() }, true);
        });

        ddDate.querySelector('[data-val="all"]').addEventListener('click', () => {
             pickerStart.scrollToDate({ day: 1, month: 0, year: 2000 });
             pickerEnd.scrollToDate({ day: today.getDate(), month: today.getMonth(), year: today.getFullYear() });
        });
    }

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if(IOSDatePicker.isGlobalDragging) return;
            if(e.target.closest('.dropdown-menu')) return;
            document.querySelectorAll('.filter-btn').forEach(b => { if(b!==btn) b.classList.remove('active'); });
            btn.classList.toggle('active');
            if(btn.id === 'filter-date-btn' && btn.classList.contains('active')) {
                setTimeout(() => {
                    if(pickerStart) pickerStart.refreshPositionOnVisible();
                    if(pickerEnd) pickerEnd.refreshPositionOnVisible();
                }, 10);
            }
        });
    });
}

// ... (Resto de funciones: loadNotifications, populateFilters, etc. se mantienen IGUALES) ...
export async function loadNotifications() {
    btnRefresh.style.opacity = "0.5";
    try {
        const res = await fetch('/api/notifications');
        cachedNotifications = await res.json();
        
        if (cachedNotifications.length > 0 && pickerStart) {
            const dates = cachedNotifications.map(n => n.date).sort();
            const minStr = dates[0]; const [y, m, d] = minStr.split('-').map(Number);
            pickerStart.scrollToDate({ year: y, month: m - 1, day: d }, false);
        }
        populateFilters(cachedNotifications);
        applyFilters();
    } catch (e) { console.error(e); }
    btnRefresh.style.opacity = "1";
}

function populateFilters(data) {
    const users = [...new Set(data.map(n => n.user))].sort();
    const types = [...new Set(data.map(n => n.type))].sort();
    fillDropdown('dd-user', users, 'users');
    fillDropdown('dd-type', types, 'types');
}

function fillDropdown(id, items, filterKey) {
    const dd = document.getElementById(id);
    const existingInput = dd.querySelector('input');
    const prevValue = existingInput ? existingInput.value : '';
    dd.innerHTML = '';
    const allDiv = document.createElement('div');
    allDiv.className = 'dd-item'; allDiv.textContent = 'TODOS (Limpiar)';
    allDiv.onclick = () => { activeFilters[filterKey].clear(); refreshDropdownVisuals(dd, activeFilters[filterKey]); updateFilterBtnState(filterKey==='users'?'user':'type'); applyFilters(); };
    dd.appendChild(allDiv);
    if (filterKey === 'types') { const sep = document.createElement('div'); sep.className = 'dd-separator'; dd.appendChild(sep); }
    if(id === 'dd-user') {
        const wrapper = document.createElement('div'); wrapper.className = 'dd-search-wrapper';
        const input = document.createElement('input'); input.type = 'text'; input.placeholder = 'Buscar...'; input.value = prevValue;
        input.oninput = (e) => { const t = e.target.value.toLowerCase(); dd.querySelectorAll('.item-option').forEach(el => el.style.display = el.textContent.toLowerCase().includes(t)?'flex':'none'); };
        wrapper.appendChild(input); dd.appendChild(wrapper);
        if(existingInput && document.activeElement === existingInput) setTimeout(() => input.focus(), 0);
    }
    items.forEach(val => {
        const div = document.createElement('div'); div.className = 'dd-item item-option'; div.textContent = val;
        div.onclick = () => toggleFilter(filterKey, val, div);
        dd.appendChild(div);
    });
}

function toggleFilter(key, val, el) {
    const set = activeFilters[key];
    if(set.has(val)) set.delete(val); else set.add(val);
    if(set.has(val)) el.classList.add('selected'); else el.classList.remove('selected');
    updateFilterBtnState(key === 'users' ? 'user' : 'type');
    applyFilters();
}

function refreshDropdownVisuals(dd, set) { dd.querySelectorAll('.item-option').forEach(el => { if(set.has(el.textContent)) el.classList.add('selected'); else el.classList.remove('selected'); }); }
function updateFilterBtnState(btnName) {
    let active = false;
    if(btnName === 'user') active = activeFilters.users.size > 0;
    if(btnName === 'type') active = activeFilters.types.size > 0;
    if(btnName === 'date' && pickerStart) { const ds = pickerStart.getFormattedDate(); active = ds !== '2000-01-01'; }
    const btn = document.getElementById(`filter-${btnName}-btn`);
    if(active) btn.classList.add('has-filters'); else btn.classList.remove('has-filters');
}

function applyFilters() {
    let filtered = cachedNotifications;
    if(activeFilters.users.size > 0) filtered = filtered.filter(n => activeFilters.users.has(n.user));
    if(activeFilters.types.size > 0) filtered = filtered.filter(n => activeFilters.types.has(n.type));
    if (pickerStart && pickerEnd) {
        const dStart = pickerStart.getFormattedDate(); const dEnd = pickerEnd.getFormattedDate();
        filtered = filtered.filter(n => n.date >= dStart && n.date <= dEnd);
        updateFilterBtnState('date');
    }
    renderNotifications(filtered);
}

function renderNotifications(items) {
    ulNotifs.innerHTML = '';
    if(items.length === 0) { ulNotifs.innerHTML = '<li style="padding:10px; text-align:center; color:#888; font-family:monospace;">Sin resultados</li>'; return; }
    items.forEach(n => {
        const li = document.createElement('li'); li.className = 'notif-item';
        li.innerHTML = `<div class="notif-left"><span class="notif-user">${n.user}</span><span class="notif-desc">${n.desc}</span></div><div class="notif-right"><span class="notif-date">${n.date}<br>${n.time}</span><span class="notif-type badge-${n.type}">${n.type}</span></div>`;
        ulNotifs.appendChild(li);
    });
    setupScrollLogic(ulNotifs);
}