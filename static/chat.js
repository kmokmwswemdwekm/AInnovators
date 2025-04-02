

document.addEventListener("DOMContentLoaded", function () {
  const welcomeScreen = document.getElementById("welcome-screen");
  const fileInputSection = document.getElementById("file-input-section");
  const questionFormSection = document.getElementById("question-form-section");
  const outputSection = document.getElementById("output-section");
  const fileUpload = document.getElementById("file-upload");
  const questionForm = document.getElementById("question-form");
  const outputContent = document.getElementById("output-content");
  const confirmBtn = document.getElementById("confirm-btn");
  const changeBtn = document.getElementById("change-btn");

  let userResponses = {};

  // Function to hide the welcome screen and show the next section
  function transitionToFileInput() {
      welcomeScreen.style.display = "none"; // Hide welcome screen
      fileInputSection.classList.remove("hidden"); // Show file input section
  }

  // File upload transition logic
  fileUpload.addEventListener("change", function () {
      if (fileUpload.files.length > 0) {
          fileInputSection.style.display = "none";
          questionFormSection.classList.remove("hidden");
      }
  });

  // Handle form submission and move to output
  questionForm.addEventListener("submit", function (event) {
      event.preventDefault();
      userResponses = {
          shortQuestions: document.getElementById("short-questions").value,
          longQuestions: document.getElementById("long-questions").value,
          numericalQuestions: document.getElementById("numerical-questions").value,
          difficulty: document.getElementById("difficulty-level").value,
      };
      questionFormSection.style.display = "none";
      outputSection.classList.remove("hidden");
      outputContent.innerHTML = `
          <p>Short Answer Questions: ${userResponses.shortQuestions}</p>
          <p>Long Answer Questions: ${userResponses.longQuestions}</p>
          <p>Numerical Questions: ${userResponses.numericalQuestions}</p>
          <p>Difficulty Level: ${userResponses.difficulty}</p>
      `;
  });

  // Export PDF logic
  confirmBtn.addEventListener("click", function () {
      const doc = new jsPDF();
      doc.text(20, 20, `Short Answer Questions: ${userResponses.shortQuestions}`);
      doc.text(20, 30, `Long Answer Questions: ${userResponses.longQuestions}`);
      doc.text(20, 40, `Numerical Questions: ${userResponses.numericalQuestions}`);
      doc.text(20, 50, `Difficulty Level: ${userResponses.difficulty}`);
      doc.save("output.pdf");
      alert("PDF Exported Successfully!");
  });

  // Allow the user to make changes
  changeBtn.addEventListener("click", function () {
      outputSection.style.display = "none";
      questionFormSection.classList.remove("hidden");
  });

  // Automatically transition to file input after welcome screen fades out
  setTimeout(transitionToFileInput, 5000);
});
