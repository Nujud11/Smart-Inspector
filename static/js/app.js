document.addEventListener("DOMContentLoaded", () => {
    initializeTheme();
    initializeUploadPage();
    initializeReportTabs();
});

function initializeTheme() {
    const root = document.documentElement;
    const toggle = document.getElementById("themeToggle");

    if (!toggle) {
        return;
    }

    function applyTheme(theme) {
        root.dataset.theme = theme;

        toggle.setAttribute(
            "aria-pressed",
            theme === "dark" ? "true" : "false"
        );

        toggle.setAttribute(
            "aria-label",
            theme === "dark"
                ? "تفعيل الوضع الفاتح"
                : "تفعيل الوضع الداكن"
        );

        localStorage.setItem(
            "smart-inspector-theme",
            theme
        );
    }

    applyTheme(root.dataset.theme || "light");

    toggle.addEventListener("click", () => {
        const nextTheme =
            root.dataset.theme === "dark"
                ? "light"
                : "dark";

        applyTheme(nextTheme);
    });
}

function initializeUploadPage() {
    const input = document.getElementById("accidentImages");
    const dropZone = document.getElementById("dropZone");
    const previewSection = document.getElementById(
        "previewSection"
    );
    const previewGrid = document.getElementById("previewGrid");
    const fileCount = document.getElementById("fileCount");
    const clearButton = document.getElementById("clearImages");
    const form = document.getElementById("accidentForm");
    const overlay = document.getElementById(
        "processingOverlay"
    );

    /*
     * إذا لم نكن في صفحة رفع الصور، نخرج من هذه الدالة فقط.
     * لا نوقف ملف JavaScript كاملًا، حتى تعمل تبويبات التقرير.
     */
    if (!input) {
        return;
    }

    function renderPreviews() {
        const files = Array.from(input.files);

        previewGrid.innerHTML = "";

        if (files.length === 0) {
            previewSection.classList.add("hidden");
            return;
        }

        previewSection.classList.remove("hidden");
        fileCount.textContent = `${files.length} صور`;

        files.forEach((file, index) => {
            const reader = new FileReader();

            reader.onload = (event) => {
                const card = document.createElement("div");
                card.className = "preview-card";

                card.innerHTML = `
                    <img
                        src="${event.target.result}"
                        alt="صورة الحادث ${index + 1}"
                    >

                    <div class="preview-overlay">
                        <span>الصورة ${index + 1}</span>
                    </div>
                `;

                previewGrid.appendChild(card);
            };

            reader.readAsDataURL(file);
        });
    }

    input.addEventListener("change", () => {
        if (input.files.length > 4) {
            alert("يمكن رفع أربع صور كحد أقصى.");
            input.value = "";
            renderPreviews();
            return;
        }

        renderPreviews();
    });

    if (dropZone) {
        ["dragenter", "dragover"].forEach((eventName) => {
            dropZone.addEventListener(eventName, (event) => {
                event.preventDefault();
                dropZone.classList.add("dragging");
            });
        });

        ["dragleave", "drop"].forEach((eventName) => {
            dropZone.addEventListener(eventName, (event) => {
                event.preventDefault();
                dropZone.classList.remove("dragging");
            });
        });
    }

    if (clearButton) {
        clearButton.addEventListener("click", () => {
            input.value = "";
            renderPreviews();
        });
    }

    if (form) {
        form.addEventListener("submit", () => {
            if (overlay) {
                overlay.classList.remove("hidden");
            }

            const steps = document.querySelectorAll(
                ".processing-step"
            );

            let activeIndex = 0;

            const intervalId = window.setInterval(() => {
                if (activeIndex < steps.length - 1) {
                    steps[activeIndex].classList.remove(
                        "active"
                    );

                    steps[activeIndex].classList.add(
                        "complete"
                    );

                    activeIndex += 1;

                    steps[activeIndex].classList.add(
                        "active"
                    );
                } else {
                    window.clearInterval(intervalId);
                }
            }, 3500);
        });
    }
}


function initializeReportTabs() {
    const reportTabs = document.querySelectorAll(
        ".report-tab"
    );

    const tabPanels = document.querySelectorAll(
        ".tab-panel"
    );

    if (reportTabs.length === 0) {
        return;
    }

    reportTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const targetName = tab.dataset.tab;

            reportTabs.forEach((item) => {
                item.classList.remove("active");
            });

            tabPanels.forEach((panel) => {
                panel.classList.remove("active");
            });

            tab.classList.add("active");

            const targetPanel = document.getElementById(
                `tab-${targetName}`
            );

            if (targetPanel) {
                targetPanel.classList.add("active");
            }
        });
    });
}