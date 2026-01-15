export function setupToggles(callbacks) {
    const { onMainToggle, onSubToggle } = callbacks;

    // --- MAIN TOGGLE ---
    const mBtns = document.querySelectorAll('.main-toggle .br-toggle-btn');
    const mCont = document.querySelector('.main-toggle');
    const pFriends = document.getElementById('br-panel-friends');
    const pNotifs = document.getElementById('br-panel-notifications');
    const pAdmin = document.getElementById('br-panel-admin');

    mBtns.forEach(b => b.addEventListener('click', () => {
        const target = b.dataset.target;
        
        mBtns.forEach(btn => btn.classList.toggle('active', btn === b));
        
        // Clases de estado para el Glider
        mCont.classList.remove('state-friends', 'state-notifications', 'state-admin');
        mCont.classList.add(`state-${target}`);

        // Gestión de Paneles
        if (pFriends) pFriends.style.display = 'none';
        if (pNotifs) pNotifs.style.display = 'none';
        if (pAdmin) pAdmin.style.display = 'none';

        if (target === 'notifications') {
            if (pNotifs) pNotifs.style.display = 'flex';
        } else if (target === 'admin') {
            if (pAdmin) pAdmin.style.display = 'flex';
        } else {
            if (pFriends) pFriends.style.display = 'flex';
        }

        if(onMainToggle) onMainToggle(target);
    }));

    // --- SUB TOGGLES ---
    const subGroups = document.querySelectorAll('.br-subtoggle-container');
    subGroups.forEach(group => {
        const sBtns = group.querySelectorAll('.br-subtoggle-btn');
        sBtns.forEach((b, i) => b.addEventListener('click', () => {
            group.classList.remove('pos-0','pos-1','pos-2');
            group.classList.add(`pos-${i}`);
            
            sBtns.forEach(btn => btn.classList.toggle('active', btn === b));
            
            const targetId = b.dataset.subtarget;
            const targetPage = document.getElementById(targetId);
            if (targetPage) {
                const parentWrapper = targetPage.parentElement;
                parentWrapper.querySelectorAll('.br-subpage').forEach(p => {
                    if (p.id === targetId) {
                        p.classList.add('active');
                        if(onSubToggle) onSubToggle(p);
                    } else {
                        p.classList.remove('active');
                    }
                });
            }
        }));
    });
}