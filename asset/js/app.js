function toggleModule(element) {
  element.classList.toggle('expanded');
  const sublist = element.nextElementSibling;
  if (sublist) {
    sublist.classList.toggle('expanded');
  }
}
 
function toggleMobileMenu() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('mobile-active');
}
 
document.addEventListener('click', function(e) {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.querySelector('.mobile-menu-toggle');
  if (window.innerWidth <= 768) {
    if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
      sidebar.classList.remove('mobile-active');
    }
  }
});
 
