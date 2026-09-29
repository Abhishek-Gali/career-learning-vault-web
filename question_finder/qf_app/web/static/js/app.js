// app.js — Interactive Client Logic

document.addEventListener("DOMContentLoaded", () => {
    console.log("CLF-C02 Researcher Web UI initialized.");
});

function handleOptionSelect(element, isMultiple) {
    const parent = element.closest(".options-list");
    if (!isMultiple) {
        parent.querySelectorAll(".option-item").forEach(el => el.classList.remove("selected"));
        element.classList.add("selected");
    } else {
        element.classList.toggle("selected");
    }
}
