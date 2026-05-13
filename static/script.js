async function loadPCs() {
    const response = await fetch("/pcs");
    const pcs = await response.json();

    const container = document.getElementById("pcs");

    container.innerHTML = "";

    pcs.forEach(pc => {

        const card = document.createElement("div");
        card.className = "pc-card";

        const statusText = pc.is_busy ? "Занят" : "Свободен";
        const statusClass = pc.is_busy ? "busy" : "free";

        card.innerHTML = `
            <div class="pc-title">ПК #${pc.id}</div>

            <div class="status ${statusClass}">
                ${statusText}
            </div>

            ${
                pc.is_busy
                ?
                `<button class="end-btn" onclick="endSession(${pc.id})">
                    Завершить
                </button>`
                :
                `<button class="book-btn" onclick="bookPC(${pc.id})">
                    Забронировать
                </button>`
            }
        `;

        container.appendChild(card);
    });
}

async function bookPC(id) {

    const hours = prompt("Введите количество часов:");

    if (!hours) return;

    await fetch(`/book/${id}?hours=${hours}`, {
        method: "POST"
    });

    loadPCs();
}

async function endSession(id) {

    await fetch(`/end/${id}`, {
        method: "POST"
    });

    loadPCs();
}

loadPCs();

setInterval(loadPCs, 5000);
