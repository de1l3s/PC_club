let countdownIntervals = {};

// === Валидация ===
function isValidEmail(email) {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return regex.test(email);
}

function isValidPhone(phone) {
    const cleanPhone = phone.replace(/[\s\-\(\)]/g, "");
    const regex = /^\+?\d{5,15}$/;
    return regex.test(cleanPhone);
}

// === Цикличный prompt ===
function promptUntilValid(message, validator, errorMessage) {
    while (true) {
        const input = prompt(message);
        if (input === null) return null;
        const trimmed = input.trim();
        if (trimmed === "") {
            alert("⚠ Поле не может быть пустым!");
            continue;
        }
        if (!validator(trimmed)) {
            alert(errorMessage);
            continue;
        }
        return trimmed;
    }
}

// === Email prompt (исправлено: Отмена ≠ пропустить) ===
function promptEmail() {
    while (true) {
        const input = prompt(
            "📧 Введите email (необязательно):\nПример: user@mail.ru\n\n" +
            "• Нажмите ОК с пустым полем, чтобы пропустить\n" +
            "• Нажмите Отмена, чтобы отменить бронирование"
        );

        // Пользователь нажал "Отмена" — отменяем всё
        if (input === null) return null;

        const trimmed = input.trim();

        // Пустое поле — пользователь хочет пропустить email
        if (trimmed === "") return "";

        // Проверяем корректность
        if (!isValidEmail(trimmed)) {
            alert("❌ Некорректный email!\n\n📧 Пример: user@mail.ru\n\nПопробуйте ещё раз или оставьте поле пустым для пропуска.");
            continue;
        }

        return trimmed;
    }
}

function promptPositiveNumber(message) {
    while (true) {
        const input = prompt(message);
        if (input === null) return null;
        const trimmed = input.trim();
        if (trimmed === "") {
            alert("⚠ Введите количество часов!");
            continue;
        }
        const num = parseFloat(trimmed);
        if (isNaN(num) || num <= 0) {
            alert("❌ Введите положительное число!\nПример: 1.5, 2, 3");
            continue;
        }
        return num;
    }
}

// === Загрузка ПК ===
async function loadPCs() {
    try {
        const response = await fetch("/pcs");
        const pcs = await response.json();

        const container = document.getElementById("pcs");
        container.innerHTML = "";

        let freeCount = 0;
        pcs.forEach(pc => { if (!pc.is_busy) freeCount++; });
        document.getElementById("free-count").textContent = freeCount;
        document.getElementById("total-count").textContent = pcs.length;

        pcs.forEach(pc => {
            const card = document.createElement("div");
            card.className = "pc-card";
            if (pc.is_busy) card.classList.add("busy-card");

            const statusText = pc.is_busy ? "Занят" : "Свободен";
            const statusClass = pc.is_busy ? "busy" : "free";

            let cardHTML = `
                <div class="pc-title">🖥 ПК #${pc.id}</div>
                <div class="status ${statusClass}">${statusText}</div>
            `;

            if (pc.is_busy) {
                if (pc.user) {
                    cardHTML += `
                        <div class="user-info">
                            <div class="user-name">👤 ${escapeHTML(pc.user.name)}</div>
                            <div class="user-phone">📱 ${escapeHTML(pc.user.phone)}</div>
                            ${pc.user.email ? `<div class="user-email">📧 ${escapeHTML(pc.user.email)}</div>` : ""}
                        </div>
                    `;
                }

                if (pc.session_end) {
                    cardHTML += `<div class="timer" id="timer-${pc.id}"></div>`;
                }

                cardHTML += `
                    <button class="end-btn" onclick="endSession(${pc.id})">
                        ✖ Завершить
                    </button>
                `;
            } else {
                cardHTML += `
                    <button class="book-btn" onclick="bookPC(${pc.id})">
                        ▶ Забронировать
                    </button>
                `;
            }

            card.innerHTML = cardHTML;
            container.appendChild(card);

            if (pc.is_busy && pc.session_end) {
                startCountdown(pc.id, pc.session_end);
            }
        });
    } catch (e) {
        console.error("Ошибка загрузки ПК:", e);
    }
}

function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// === Таймер ===
function startCountdown(pcId, sessionEnd) {
    if (countdownIntervals[pcId]) {
        clearInterval(countdownIntervals[pcId]);
    }

    function updateTimer() {
        const now = new Date().getTime();
        const end = new Date(sessionEnd).getTime();
        const diff = end - now;

        const timerElement = document.getElementById(`timer-${pcId}`);
        if (!timerElement) {
            clearInterval(countdownIntervals[pcId]);
            return;
        }

        if (diff <= 0) {
            timerElement.textContent = "⚡ Время истекло";
            timerElement.style.color = "#ff3d71";
            clearInterval(countdownIntervals[pcId]);
            return;
        }

        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);

        timerElement.textContent = `⏳ ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        if (diff < 5 * 60 * 1000) {
            timerElement.classList.add("warning");
        }
    }

    updateTimer();
    countdownIntervals[pcId] = setInterval(updateTimer, 1000);
}

// === Бронирование ===
async function bookPC(id) {
    const name = promptUntilValid(
        "👤 Введите ваше имя:",
        (v) => v.length >= 1,
        "⚠ Имя не может быть пустым!"
    );
    if (name === null) return;

    const phone = promptUntilValid(
        "📱 Введите номер телефона:\n(минимум 5 цифр)\nПример: +7 900 1234567",
        isValidPhone,
        "❌ Некорректный номер!\n\nРазрешены: цифры, +, -, пробелы, ()\nМинимум 5 цифр."
    );
    if (phone === null) return;

    // ИСПРАВЛЕНО: теперь Отмена отменяет, а пустое поле пропускает
    const email = promptEmail();
    if (email === null) return; // Только явная Отмена прерывает

    const hours = promptPositiveNumber(
        "⏰ На сколько часов?\nПример: 1.5, 2, 3"
    );
    if (hours === null) return;

    let url = `/book/${id}?hours=${hours}&name=${encodeURIComponent(name)}&phone=${encodeURIComponent(phone)}`;
    if (email !== "") {
        url += `&email=${encodeURIComponent(email)}`;
    }

    try {
        const response = await fetch(url, { method: "POST" });
        const text = await response.text();

        if (!response.ok) {
            let errorMessage = "Неизвестная ошибка";
            try {
                const errorData = JSON.parse(text);
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                errorMessage = text || "Ошибка сервера";
            }
            alert("❌ " + errorMessage);
            return;
        }

        loadPCs();
    } catch (e) {
        console.error("Ошибка:", e);
        alert("❌ Ошибка соединения с сервером. Проверьте, запущен ли сервер.");
    }
}

// === Завершение сессии ===
async function endSession(id) {
    try {
        await fetch(`/end/${id}`, { method: "POST" });
        loadPCs();
    } catch (e) {
        console.error("Ошибка завершения:", e);
    }
}

// === История ===
async function showHistory() {
    const phone = promptUntilValid(
        "📱 Введите номер телефона для просмотра истории:",
        isValidPhone,
        "❌ Некорректный номер!"
    );
    if (phone === null) return;

    try {
        const response = await fetch(`/history?phone=${encodeURIComponent(phone)}`);

        if (!response.ok) {
            alert("❌ Пользователь не найден");
            return;
        }

        const data = await response.json();
        const user = data.user;
        const sessions = data.sessions;

        let sessionsHTML = "";
        if (sessions.length === 0) {
            sessionsHTML = "<p style='text-align:center; color: var(--text-muted); padding: 20px;'>Нет бронирований</p>";
        } else {
            sessions.forEach(s => {
                const statusClass = s.is_active ? "session-active" : "session-ended";
                const statusText = s.is_active ? "🟢 Активна" : "⚫ Завершена";
                const start = new Date(s.start_time).toLocaleString("ru-RU");
                const end = new Date(s.end_time).toLocaleString("ru-RU");
                sessionsHTML += `
                    <div class="session-item ${statusClass}">
                        <strong>ПК #${s.pc_id}</strong> — ${s.hours} ч<br>
                        <small>${start}</small><br>
                        <small>${end}</small><br>
                        <span style="font-size: 12px; color: var(--text-muted);">${statusText}</span>
                    </div>
                `;
            });
        }

        const modal = document.createElement("div");
        modal.className = "modal";
        modal.onclick = function(e) {
            if (e.target === modal) modal.remove();
        };
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close" onclick="this.parentElement.parentElement.remove()">✖</span>
                <h2>👤 ${escapeHTML(user.name)}</h2>
                <p>📱 ${escapeHTML(user.phone)}</p>
                ${user.email ? `<p>📧 ${escapeHTML(user.email)}</p>` : ""}
                <h3>📋 История бронирований (${sessions.length})</h3>
                ${sessionsHTML}
            </div>
        `;

        document.body.appendChild(modal);
    } catch (e) {
        console.error("Ошибка истории:", e);
    }
}

// === Запуск ===
loadPCs();
setInterval(loadPCs, 5000);
