// app.js — Interactive Client Logic & Mobile Drawer Navigation

document.addEventListener("DOMContentLoaded", () => {
    // Close sidebar on Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeMobileSidebar();
        }
    });

    // Close sidebar when clicking any nav link on mobile
    document.querySelectorAll(".nav-links a").forEach((link) => {
        link.addEventListener("click", () => {
            if (window.innerWidth < 768) {
                closeMobileSidebar();
            }
        });
    });
});

function toggleMobileSidebar() {
    const sidebar = document.querySelector(".sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    const menuBtn = document.getElementById("mobile-menu-btn");
    
    if (!sidebar) return;
    
    const isOpen = sidebar.classList.toggle("sidebar-open");
    if (overlay) {
        overlay.classList.toggle("sidebar-open", isOpen);
    }
    if (menuBtn) {
        menuBtn.innerHTML = isOpen ? "✕" : "☰";
        menuBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
    }
}

function closeMobileSidebar() {
    const sidebar = document.querySelector(".sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    const menuBtn = document.getElementById("mobile-menu-btn");
    
    if (sidebar) sidebar.classList.remove("sidebar-open");
    if (overlay) overlay.classList.remove("sidebar-open");
    if (menuBtn) {
        menuBtn.innerHTML = "☰";
        menuBtn.setAttribute("aria-expanded", "false");
    }
}

function handleOptionSelect(element, isMultiple) {
    const parent = element.closest(".options-list");
    if (!parent) return;
    if (!isMultiple) {
        parent.querySelectorAll(".option-item").forEach(el => el.classList.remove("selected"));
        element.classList.add("selected");
    } else {
        element.classList.toggle("selected");
    }
}
