function toggleCandidateFields() {
    var candidatoCheckbox = document.getElementById('candidato');
    var candidateFields = document.getElementById('candidate-fields');
    if (candidatoCheckbox.checked) {
        candidateFields.classList.remove('hidden');
    } else {
        candidateFields.classList.add('hidden');
    }
}