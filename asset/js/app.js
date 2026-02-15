/* ===============================
   SIDEBAR MODULE TOGGLE
================================ */
document.querySelectorAll(".tree-toggle").forEach(toggle => {
    toggle.addEventListener("click", function () {
        const next = this.nextElementSibling;
        if (next) {
            next.style.display =
                next.style.display === "block" ? "none" : "block";
        }
    });
});
 
 
/* ===============================
   MOBILE SIDEBAR TOGGLE
================================ */
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebar.classList.toggle("active");
}
 
 
/* ===============================
   CLOSE SIDEBAR WHEN CLICKING OUTSIDE (MOBILE)
================================ */
document.addEventListener("click", function (e) {
    const sidebar = document.getElementById("sidebar");
    const menuBtn = document.querySelector(".menu-btn");
 
    if (window.innerWidth <= 900) {
        if (
            sidebar &&
            !sidebar.contains(e.target) &&
            !menuBtn.contains(e.target)
        ) {
            sidebar.classList.remove("active");
        }
    }
});
 
 
/* ===============================
   AUTO ACTIVE LINK DETECTION
================================ */
const currentPage = window.location.pathname.split("/").pop();
 
document.querySelectorAll(".sidebar a").forEach(link => {
    const linkHref = link.getAttribute("href");
 
    if (linkHref === currentPage) {
        link.classList.add("active");
 
        // If inside sublist, auto expand parent
        const parentSublist = link.closest(".tree-children");
        if (parentSublist) {
            parentSublist.style.display = "block";
        }
    }
});
 
