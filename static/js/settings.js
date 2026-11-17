function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

function togglePass(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('ph-eye'); icon.classList.add('ph-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('ph-eye-slash'); icon.classList.add('ph-eye');
    }
}

function generatePassword(inputId) {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789';
    let pass = '';
    for (let i = 0; i < 10; i++) pass += chars[Math.floor(Math.random() * chars.length)];
    const input = document.getElementById(inputId);
    input.value = pass;
    input.type = 'text';
    const btn = input.closest('.password-wrapper').querySelector('.toggle-pass i');
    if (btn) { btn.classList.remove('ph-eye'); btn.classList.add('ph-eye-slash'); }
}

function openEditModal(id, username, nama, email, role) {
    document.getElementById('edit_user_id').value = id;
    document.getElementById('edit_username').value = username;
    document.getElementById('edit_nama').value = nama;
    document.getElementById('edit_email').value = email;
    document.getElementById('edit_role').value = role;
    openModal('editUserModal');
}

function openResetModal(id, username) {
    document.getElementById('targetUserId').value = id;
    document.getElementById('targetUsername').innerText = username;
    openModal('resetModal');
}

function deleteUser(id, username) {
    if(confirm("Hapus user " + username + "?")) {
        const fd = new FormData(); fd.append('user_id', id);
        fetch('/settings/delete_user', { method: 'POST', body: fd })
        .then(res => res.json()).then(d => { if(d.status=='success') location.reload(); else alert(d.msg); });
    }
}

htmxReady(() => {

    // UPDATE PROFILE
    const formProfile = document.getElementById('formUpdateProfile');
    if(formProfile) {
        formProfile.addEventListener('submit', (e) => {
            e.preventDefault();
            fetch('/settings/update_profile', { method: 'POST', body: new FormData(formProfile) })
            .then(res => res.json()).then(d => { if(d.status=='success') location.reload(); else alert("Error: " + d.msg); });
        });
    }

    // CHANGE PASS
    const formPass = document.getElementById('formChangePass');
    if(formPass) {
        formPass.addEventListener('submit', (e) => {
            e.preventDefault();
            fetch('/settings/change_password', { method: 'POST', body: new FormData(formPass) })
            .then(res => res.json()).then(d => { if(d.status=='success') { alert("Password Updated"); formPass.reset(); } else alert(d.msg); });
        });
    }

    // ADMIN: ADD USER
    const formAdd = document.getElementById('formAddUser');
    if(formAdd) {
        formAdd.addEventListener('submit', (e) => {
            e.preventDefault();
            fetch('/settings/create_user', { method: 'POST', body: new FormData(formAdd) })
            .then(res => res.json()).then(d => { if(d.status=='success') location.reload(); else alert(d.msg); });
        });
    }

    // ADMIN: EDIT USER
    const formEdit = document.getElementById('formEditUser');
    if(formEdit) {
        formEdit.addEventListener('submit', (e) => {
            e.preventDefault();
            fetch('/settings/update_user_data', { method: 'POST', body: new FormData(formEdit) })
            .then(res => res.json()).then(d => { if(d.status=='success') location.reload(); else alert(d.msg); });
        });
    }

    // ADMIN: RESET PASS
    const formReset = document.getElementById('formResetUser');
    if(formReset) {
        formReset.addEventListener('submit', (e) => {
            e.preventDefault();
            fetch('/settings/reset_user_pass', { method: 'POST', body: new FormData(formReset) })
            .then(res => res.json()).then(d => { if(d.status=='success') { alert("Password Reset!"); closeModal('resetModal'); } else alert(d.msg); });
        });
    }
});