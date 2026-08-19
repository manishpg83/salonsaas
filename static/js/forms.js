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
