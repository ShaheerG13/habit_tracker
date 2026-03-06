// create-habit modal
var createModal = document.getElementById("myModal");
var createBtn = document.getElementById("modalBtn");
var createClose = document.querySelector(".create-close");

if (createBtn && createModal) {
  createBtn.onclick = function (e) {
    e.preventDefault();
    createModal.style.display = "block";
  };
}

if (createClose && createModal) {
  createClose.onclick = function () {
    createModal.style.display = "none";
  };
}

// delete-habit modal
var deleteModal = document.getElementById("deleteModal");
var deleteClose = document.querySelector(".delete-close");
var deleteHabitForm = document.getElementById("delete-habit-form");
var deleteHabitIdInput = document.getElementById("delete-habit-id-input");
var deleteHabitNameDisplay = document.getElementById("delete-habit-name-display");
var deleteHabitNameInput = document.getElementById("delete-habit-name-input");
var deleteHabitSubmitBtn = deleteHabitForm
  ? deleteHabitForm.querySelector(".modal-delete-btn")
  : null;

if (deleteClose && deleteModal) {
  deleteClose.onclick = function () {
    deleteModal.style.display = "none";
  };
}

// open delete modal when clicking the red X
document.querySelectorAll(".habit-delete").forEach(function (button) {
  button.addEventListener("click", function (event) {
    event.preventDefault();
    event.stopPropagation();

    if (!deleteModal || !deleteHabitIdInput || !deleteHabitNameDisplay || !deleteHabitNameInput || !deleteHabitSubmitBtn) {
      return;
    }

    var habitId = this.getAttribute("data-habit-id");
    var habitName = this.getAttribute("data-habit-name") || "";

    deleteHabitIdInput.value = habitId;
    deleteHabitNameDisplay.textContent = habitName;
    deleteHabitNameInput.value = "";
    deleteHabitSubmitBtn.disabled = true;

    deleteModal.style.display = "block";
    deleteHabitNameInput.focus();
  });
});

// enable delete button only when typed name matches
if (deleteHabitNameInput && deleteHabitSubmitBtn && deleteHabitNameDisplay) {
  deleteHabitNameInput.addEventListener("input", function () {
    var typed = deleteHabitNameInput.value || "";
    var target = deleteHabitNameDisplay.textContent || "";
    deleteHabitSubmitBtn.disabled = typed !== target;
  });
}

// close modals when clicking outside
window.onclick = function (event) {
  if (createModal && event.target === createModal) {
    createModal.style.display = "none";
  }
  if (deleteModal && event.target === deleteModal) {
    deleteModal.style.display = "none";
  }
};