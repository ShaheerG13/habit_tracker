// create-habit modal
let createModal = document.getElementById("myModal");
let createBtn = document.getElementById("modalBtn");
let createClose = document.querySelector(".create-close");

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
let deleteModal = document.getElementById("deleteModal");
let deleteClose = document.querySelector(".delete-close");
let deleteHabitForm = document.getElementById("delete-habit-form");
let deleteHabitIdInput = document.getElementById("delete-habit-id-input");
let deleteHabitNameDisplay = document.getElementById("delete-habit-name-display");
let deleteHabitNameInput = document.getElementById("delete-habit-name-input");
let deleteHabitSubmitBtn = deleteHabitForm
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

    let habitId = this.getAttribute("data-habit-id");
    let habitName = this.getAttribute("data-habit-name") || "";

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
    let typed = deleteHabitNameInput.value || "";
    let target = deleteHabitNameDisplay.textContent || "";
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