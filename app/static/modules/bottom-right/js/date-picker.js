const MONTHS = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'];

export class IOSDatePicker {
    static isGlobalDragging = false;

    constructor(containerId, initialDate = new Date(), maxDate = new Date(), onChangeCallback = null) {
        this.container = document.getElementById(containerId);
        this.today = new Date();
        this.today.setHours(0,0,0,0);

        this.state = {
            day: initialDate.getDate(),
            month: initialDate.getMonth(),
            year: initialDate.getFullYear()
        };
        this.maxDate = maxDate;
        this.linkedPicker = null;
        this.isStartPicker = true;
        this.onChange = onChangeCallback;

        this.isDragging = false;
        this.startY = 0;
        this.startScrollTop = 0;
        this.activeCol = null;

        this.render();
        this.attachEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="picker-highlight"></div>
            <div class="picker-col col-day"><div class="picker-spacer"></div><div class="picker-spacer"></div></div>
            <div class="picker-col col-month"><div class="picker-spacer"></div><div class="picker-spacer"></div></div>
            <div class="picker-col col-year"><div class="picker-spacer"></div><div class="picker-spacer"></div></div>
        `;
        this.colDay = this.container.querySelector('.col-day');
        this.colMonth = this.container.querySelector('.col-month');
        this.colYear = this.container.querySelector('.col-year');

        this.refreshAllCols();
        setTimeout(() => this.highlightAll(), 50);
    }

    refreshPositionOnVisible() { this.refreshAllCols(); }

    refreshAllCols() {
        this.populateYears();
        this.populateMonths3Blocks();
        this.populateDays3Blocks();
        
        // Sincronizar scroll visual sin animar (instantáneo para setup)
        this.scrollToVal(this.colYear, this.state.year, false);
        
        const monthH = this.getItemHeight(this.colMonth) || 20;
        this.colMonth.scrollTop = (12 + this.state.month) * monthH;

        const daysInPrevMonth = new Date(this.state.year, this.state.month, 0).getDate();
        const dayH = this.getItemHeight(this.colDay) || 20;
        this.colDay.scrollTop = (daysInPrevMonth + this.state.day - 1) * dayH;

        this.highlightAll();
    }

    populateYears() {
        this.clearItems(this.colYear);
        const startYear = 2000;
        const endYear = this.maxDate.getFullYear(); // Maximo el año de maxDate (Hoy)
        for (let y = startYear; y <= endYear; y++) this.createItem(this.colYear, y, y);
    }

    populateMonths3Blocks() {
        this.clearItems(this.colMonth);
        [0, 1, 2].forEach(block => MONTHS.forEach((m, i) => this.createItem(this.colMonth, m, i, block)));
    }

    populateDays3Blocks() {
        this.clearItems(this.colDay);
        const prevM = new Date(this.state.year, this.state.month, 0);
        for(let d=1; d<=prevM.getDate(); d++) this.createItem(this.colDay, d, d, 0);
        const currM = new Date(this.state.year, this.state.month + 1, 0);
        for(let d=1; d<=currM.getDate(); d++) this.createItem(this.colDay, d, d, 1);
        const nextM = new Date(this.state.year, this.state.month + 2, 0);
        for(let d=1; d<=nextM.getDate(); d++) this.createItem(this.colDay, d, d, 2);
    }

    createItem(parent, text, value, blockIndex = 0) {
        const spacerBottom = parent.lastElementChild;
        const div = document.createElement('div');
        div.className = 'picker-item';
        div.textContent = text;
        div.dataset.val = value;
        div.dataset.block = blockIndex;
        parent.insertBefore(div, spacerBottom);
    }
    clearItems(col) { col.querySelectorAll('.picker-item').forEach(e => e.remove()); }

    // --- SNAP & FLUIDEZ ---

    handleScrollStop(col) {
        // Si estamos arrastrando o usando la rueda activamente, no forzar snap aun
        if (this.isDragging || this.isWheeling) return;

        const itemH = this.getItemHeight(col);
        const center = col.scrollTop + (col.offsetHeight / 2);
        
        const items = Array.from(col.querySelectorAll('.picker-item'));
        let closest = null, minDiff = Infinity;
        
        items.forEach(item => {
            const centerItem = item.offsetTop + (item.offsetHeight / 2);
            const diff = Math.abs(center - centerItem);
            if(diff < minDiff) { minDiff = diff; closest = item; }
        });

        if (closest) {
            // SNAP SUAVE
            const targetScroll = closest.offsetTop - (col.offsetHeight / 2) + (closest.offsetHeight / 2);
            if (Math.abs(col.scrollTop - targetScroll) > 1) {
                col.scrollTo({ top: targetScroll, behavior: 'smooth' });
            }

            const val = parseInt(closest.dataset.val);
            const block = parseInt(closest.dataset.block || 0);

            // LOGICA INFINITA
            let needsRefresh = false;

            if (col === this.colMonth) {
                if (block === 0) { this.state.year--; needsRefresh = true; }
                if (block === 2) { this.state.year++; needsRefresh = true; }
                this.state.month = val;
            } 
            else if (col === this.colDay) {
                if (block === 0) {
                    this.state.month--;
                    if(this.state.month < 0) { this.state.month = 11; this.state.year--; }
                    needsRefresh = true;
                }
                if (block === 2) {
                    this.state.month++;
                    if(this.state.month > 11) { this.state.month = 0; this.state.year++; }
                    needsRefresh = true;
                }
                this.state.day = val;
            }
            else {
                this.state.year = val;
                this.populateDays3Blocks(); 
                this.highlightAll();
            }

            if (needsRefresh) {
                // Refrescar para devolver al bloque central
                this.refreshAllCols(); 
            }

            this.validateDate();
        }
    }

    validateDate() {
        let changed = false;
        const daysInMonth = new Date(this.state.year, this.state.month + 1, 0).getDate();
        if (this.state.day > daysInMonth) {
            this.state.day = daysInMonth;
            changed = true;
        }

        const selDate = new Date(this.state.year, this.state.month, this.state.day);
        
        // Bloquear futuro
        if (selDate > this.maxDate) {
            this.state.day = this.maxDate.getDate();
            this.state.month = this.maxDate.getMonth();
            this.state.year = this.maxDate.getFullYear();
            this.refreshAllCols(); 
            changed = true;
        }

        // Link Pickers
        if (this.linkedPicker && !changed) {
            const myD = this.getDateObject(); const otherD = this.linkedPicker.getDateObject();
            if (this.isStartPicker && myD > otherD) this.linkedPicker.scrollToDate(this.state, true);
            else if (!this.isStartPicker && myD < otherD) this.linkedPicker.scrollToDate(this.state, true);
        }

        if (this.onChange) this.onChange();
    }

    scrollToDate(stateObj, smooth = true) {
        this.state = { ...stateObj };
        this.refreshAllCols();
    }

    scrollToVal(col, val, smooth) {
        const items = Array.from(col.querySelectorAll('.picker-item'));
        let target = items.find(i => parseInt(i.dataset.val) === val && (i.dataset.block === '1' || !i.dataset.block));
        if(!target) target = items.find(i => parseInt(i.dataset.val) === val);

        if (target) {
            const top = target.offsetTop - (col.firstElementChild.offsetHeight); 
            col.scrollTo({ top: top, behavior: smooth ? 'smooth' : 'auto' });
        }
    }

    highlightAll() { [this.colYear, this.colMonth, this.colDay].forEach(col => this.highlightCol(col)); }

    highlightCol(col) {
        const center = col.scrollTop + (col.offsetHeight / 2);
        const items = col.querySelectorAll('.picker-item');
        if (col.offsetHeight === 0) {
            items.forEach(i => {
                let match = false;
                const v = parseInt(i.dataset.val);
                const b = parseInt(i.dataset.block || 1);
                if (col === this.colMonth && v === this.state.month && b === 1) match = true;
                else if (col === this.colDay && v === this.state.day && b === 1) match = true;
                else if (col === this.colYear && v === this.state.year) match = true;
                if(match) i.classList.add('selected'); else i.classList.remove('selected');
            });
            return;
        }
        items.forEach(item => {
            const iCenter = item.offsetTop + (item.offsetHeight / 2);
            if (Math.abs(center - iCenter) < (item.offsetHeight / 1.5)) item.classList.add('selected');
            else item.classList.remove('selected');
        });
    }

    getItemHeight(col) { return col.querySelector('.picker-item')?.offsetHeight || 0; }
    getDateObject() { return new Date(this.state.year, this.state.month, this.state.day); }
    getFormattedDate() {
        const y = this.state.year; const m = String(this.state.month + 1).padStart(2,'0'); const d = String(this.state.day).padStart(2,'0');
        return `${y}-${m}-${d}`;
    }

    attachEvents() {
        [this.colDay, this.colMonth, this.colYear].forEach(col => {
            let t;
            let wheelT;

            col.addEventListener('scroll', () => {
                requestAnimationFrame(() => this.highlightCol(col));
                if(this.isDragging || this.isWheeling) return; 
                clearTimeout(t); 
                t = setTimeout(() => this.handleScrollStop(col), 60);
            });

            // RUEDA SUAVE: 1 CLICK = 1 ITEM
            col.addEventListener('wheel', (e) => {
                e.preventDefault(); 
                this.isWheeling = true;
                
                const h = this.getItemHeight(col);
                const dir = Math.sign(e.deltaY);
                
                const currentSlot = Math.round(col.scrollTop / h);
                const targetSlot = currentSlot + dir;
                
                col.scrollTo({ top: targetSlot * h, behavior: 'smooth' });

                clearTimeout(wheelT);
                wheelT = setTimeout(() => {
                    this.isWheeling = false;
                    this.handleScrollStop(col);
                }, 150);
            }, {passive:false});

            col.addEventListener('mousedown', (e) => {
                this.isDragging = true; IOSDatePicker.isGlobalDragging = true;
                this.activeCol = col; this.startY = e.clientY; this.startScrollTop = col.scrollTop;
                col.style.scrollSnapType = 'none'; document.body.style.cursor = 'grabbing';
            });

            col.addEventListener('click', (e) => {
                if(!this.isDragging && e.target.classList.contains('picker-item')) {
                    const top = e.target.offsetTop - col.firstElementChild.offsetHeight;
                    col.scrollTo({ top: top, behavior: 'smooth' });
                }
            });
        });

        window.addEventListener('mousemove', (e) => {
            if (!this.isDragging || !this.activeCol) return;
            e.preventDefault(); 
            const d = this.startY - e.clientY;
            this.activeCol.scrollTop = this.startScrollTop + d;
        });

        window.addEventListener('mouseup', () => {
            if (!this.isDragging) return;
            this.isDragging = false;
            setTimeout(() => IOSDatePicker.isGlobalDragging = false, 50);
            document.body.style.cursor = 'default';
            if (this.activeCol) {
                this.handleScrollStop(this.activeCol);
                this.activeCol = null;
            }
        });
    }
}