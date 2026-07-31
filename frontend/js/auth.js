function showError(id, message) {
    const box = document.getElementById(id);
    box.textContent = message;
    box.hidden = false;
}

function redirectAfterLogin(user) {
    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    if (next && next.startsWith("/")) {
        window.location.href = next;
    } else if (user.role === "admin") {
        window.location.href = "/admin.html";
    } else {
        window.location.href = "/area-personale.html";
    }
}

const loginForm = document.getElementById("login-form");
if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const user = await apiLogin(
                document.getElementById("email").value,
                document.getElementById("password").value,
            );
            redirectAfterLogin(user);
        } catch (err) {
            showError("login-error", err.message);
        }
    });
}

const registerForm = document.getElementById("register-form");
if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const data = {
            first_name: document.getElementById("first_name").value,
            last_name: document.getElementById("last_name").value,
            fiscal_code: document.getElementById("fiscal_code").value,
            birth_date: document.getElementById("birth_date").value,
            email: email,
            phone: document.getElementById("phone").value || null,
            password: password,
        };
        try {
            await apiSend("POST", "/api/auth/register", data);
            const user = await apiLogin(email, password);
            redirectAfterLogin(user);
        } catch (err) {
            showError("register-error", err.message);
        }
    });
}
