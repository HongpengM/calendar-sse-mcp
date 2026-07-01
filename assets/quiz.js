// Reusable multiple-choice quiz widget.
// Usage: include this script and add a div with class "quiz" and data-answer="0..N".
// Each label/input is an option; the first matching label text is treated as the option.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.quiz').forEach((quiz) => {
    const radios = quiz.querySelectorAll('input[type="radio"]');
    const feedback = quiz.querySelector('.feedback');
    const correctIndex = parseInt(quiz.dataset.answer, 10);

    radios.forEach((radio, index) => {
      radio.addEventListener('change', () => {
        if (index === correctIndex) {
          feedback.className = 'feedback correct';
          feedback.textContent = feedback.dataset.correct || '正确。';
        } else {
          feedback.className = 'feedback incorrect';
          feedback.textContent = feedback.dataset.incorrect || '再想想。';
        }
      });
    });
  });
});
