const selectedImages = [];
const maxSelections = 4;

function updateBadges() {
    document.querySelectorAll(".tile").forEach(tile => {
        const badge = tile.querySelector(".order-badge");
        const imgId = tile.querySelector("img").dataset.id;
        const index = selectedImages.indexOf(imgId);

        if (index === -1) {
            tile.classList.remove("selected");
            badge.textContent = "";
        } else {
            tile.classList.add("selected");
            badge.textContent = index + 1;
        }
    });

    const submitBtn = document.getElementById("submitBtn");
    if (submitBtn) {

    // Only enforce selection count on login page
         if (!window.isRecallPage) {
             submitBtn.disabled = selectedImages.length !== maxSelections;
         } else {
             submitBtn.disabled = false;
         }
     }
}

document.addEventListener("click", function (event) {
    const tile = event.target.closest(".tile");
    if (!tile) return;

    const img = tile.querySelector("img");
    const imgId = img.dataset.id;

    const index = selectedImages.indexOf(imgId);

    // If already selected → deselect
    if (index !== -1) {
        selectedImages.splice(index, 1);
        updateBadges();
        return;
    }

    // If not selected and limit reached → do nothing
    if (selectedImages.length >= maxSelections) return;

    // Select new image
    selectedImages.push(imgId);
    updateBadges();
});

document.addEventListener("submit", async function (event) {
    const form = event.target;
    if (!form.matches("form")) return;

    event.preventDefault();

    const sequenceInput = document.getElementById("sequenceInput");
    sequenceInput.value = selectedImages.join("|");

    const formData = new FormData(form);

    const response = await fetch(form.action, {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        const message = await response.text();
        showError(message || "Authentication failed");
        return;
    }

 // On success, follow the redirect from Flask
window.location.href = response.url;

});


function showError(message) {
    const modal = document.getElementById("errorModal");
    const messageEl = document.getElementById("modalMessage");
    const closeBtn = document.getElementById("closeModal");

    if (!modal) {
        alert(message);
        return;
    }

    messageEl.textContent = message;
    modal.classList.remove("hidden");

    closeBtn.onclick = () => {
        modal.classList.add("hidden");
    };
}

