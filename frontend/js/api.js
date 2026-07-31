const TOKEN_KEY = "cmr_token";
const USER_KEY = "cmr_user";

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getUser() {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
}

function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

function authHeaders() {
    const token = getToken();
    return token ? { "Authorization": "Bearer " + token } : {};
}

async function handleResponse(res) {
    if (!res.ok) {
        if (res.status === 401) clearSession();
        const body = await res.json().catch(() => null);
        let detail = body && body.detail ? body.detail : `Errore HTTP ${res.status}`;
        if (Array.isArray(detail)) detail = detail.map((d) => d.msg).join(", ");
        throw new Error(detail);
    }
    return res.status === 204 ? null : res.json();
}

async function apiGet(path) {
    return handleResponse(await fetch(path, { headers: authHeaders() }));
}

async function apiSend(method, path, data) {
    const headers = Object.assign({ "Content-Type": "application/json" }, authHeaders());
    return handleResponse(await fetch(path, {
        method: method,
        headers: headers,
        body: data !== undefined ? JSON.stringify(data) : undefined,
    }));
}

async function apiLogin(email, password) {
    const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password: password }),
    });
    const data = await handleResponse(res);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    const user = await apiGet("/api/auth/me");
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    return user;
}

function logout() {
    clearSession();
    window.location.href = "/";
}

function setupNav() {
    const nav = document.querySelector(".navbar nav");
    if (!nav) return;
    const user = getUser();
    if (!user) {
        nav.insertAdjacentHTML("beforeend", '<a href="/login.html">Accedi</a>');
    } else if (user.role === "admin") {
        nav.insertAdjacentHTML("beforeend",
            '<a href="/admin.html">Amministrazione</a><a href="#" id="nav-logout">Esci</a>');
    } else {
        nav.insertAdjacentHTML("beforeend",
            '<a href="/area-personale.html">Le mie visite</a><a href="#" id="nav-logout">Esci</a>');
    }
    const out = document.getElementById("nav-logout");
    if (out) {
        out.addEventListener("click", (e) => {
            e.preventDefault();
            logout();
        });
    }
}

document.addEventListener("DOMContentLoaded", setupNav);
