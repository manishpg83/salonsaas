// SalonOS — tiny vanilla-JS polish, no framework, no build step.
// Disables the submit button and swaps its label while a form is submitting,
// so a slow request doesn't look like a dead click.
document.addEventListener("submit", function (event) {
  var form = event.target;
  var button = form.querySelector('button[type="submit"]');
  if (!button || button.disabled) return;

  button.dataset.originalText = button.textContent;
  button.disabled = true;
  button.textContent = "Please wait…";
});

// Mobile off-canvas sidebar: toggle button opens it, backdrop or a nav link
// click closes it again (so navigating doesn't leave it stuck open).
(function () {
  var shell = document.querySelector(".app-shell");
  var toggle = document.querySelector(".nav-toggle");
  var backdrop = document.querySelector(".sidebar-backdrop");
  if (!shell || !toggle) return;

  function close() {
    shell.classList.remove("sidebar-open");
  }

  toggle.addEventListener("click", function () {
    shell.classList.toggle("sidebar-open");
  });
  if (backdrop) backdrop.addEventListener("click", close);
  shell.querySelectorAll(".sidebar .nav-link").forEach(function (link) {
    link.addEventListener("click", close);
  });
})();
