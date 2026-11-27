function disableButtons() {
    const checkSolutionBtn = document.getElementById("checkSolution");
    const clearInputBtn = document.getElementById("clearInput");

    checkSolutionBtn.disabled = true;
    clearInputBtn.disabled = true;

    checkSolutionBtn.style.backgroundColor = "gray";
    checkSolutionBtn.style.cursor = "not-allowed";
    clearInputBtn.style.backgroundColor = "gray";
    clearInputBtn.style.cursor = "not-allowed";
}

function enableButtons() {
    const checkSolutionBtn = document.getElementById("checkSolution");
    const clearInputBtn = document.getElementById("clearInput");

    checkSolutionBtn.disabled = false;
    clearInputBtn.disabled = false;

    checkSolutionBtn.style.backgroundColor = "";
    checkSolutionBtn.style.cursor = "pointer";
    clearInputBtn.style.backgroundColor = "";
    clearInputBtn.style.cursor = "pointer";
}

function clearSolutionMessage() {
    const messageElement = document.getElementById("solutionMessage");
    messageElement.textContent = "";
    messageElement.style.color = "";
}

function displayErrorMessage(message) {
    const messageElement = document.getElementById("solutionMessage");
    messageElement.textContent = message;
    messageElement.style.color = "red";
}

function storeDifficulty() {
    localStorage.setItem("difficulty", document.getElementById("difficulty").value);
}

function clearUserInputs() {
    document.querySelectorAll('input[type="text"]').forEach(cell => {
        if (!cell.classList.contains("prefilled")) {
            cell.value = "";
        }
    });
    clearSolutionMessage();
}

function resetAll(resetDifficulty = true) {
    document.querySelectorAll('input[type="text"]').forEach(cell => {
        cell.value = "";
        cell.removeAttribute("readonly");
        cell.classList.remove("prefilled");
    });
    enableButtons();
    clearSolutionMessage();

    if (resetDifficulty) {
        document.getElementById("difficulty").value = 3;
    }
}

function gatherSudokuInput() {
    const sudokuInput = [];
    for (let i = 0; i < 9; i++) {
        const row = [];
        for (let j = 0; j < 9; j++) {
            const cell = document.querySelector(`input[name="cell${i}${j}"]`);
            row.push(cell.value ? parseInt(cell.value, 10) : 0);
        }
        sudokuInput.push(row);
    }
    return sudokuInput;
}

function displaySolutionMessage(solved) {
    const messageElement = document.getElementById("solutionMessage");
    if (solved) {
        messageElement.textContent = "Congratulations! The Sudoku is solved!";
        messageElement.style.color = "green";
    } else {
        messageElement.textContent = "Oops! The Sudoku is not solved yet.";
        messageElement.style.color = "red";
    }
}

function fillSudokuBoard(problem) {
    for (let i = 0; i < 9; i++) {
        for (let j = 0; j < 9; j++) {
            const cell = document.querySelector(`input[name="cell${i}${j}"]`);
            if (problem[i][j] > 0) {
                cell.value = problem[i][j];
                cell.setAttribute("readonly", true);
                cell.classList.add("prefilled");
            } else {
                cell.value = "";
                cell.removeAttribute("readonly");
                cell.classList.remove("prefilled");
            }
        }
    }
    clearSolutionMessage();
}

document.addEventListener("DOMContentLoaded", function () {
    const initialSolved = document.body.dataset.initialSolved === "true";

    // Clean up any legacy disabled flag from older sessions
    localStorage.removeItem("buttonsDisabled");

    // Difficulty restoration
    const difficultySlider = document.getElementById("difficulty");
    const savedDifficulty = localStorage.getItem("difficulty");
    if (savedDifficulty) {
        difficultySlider.value = savedDifficulty;
    }

    // Disable play buttons only when showing a solved board from the server
    if (initialSolved) {
        disableButtons();
    } else {
        enableButtons();
    }

    // Check solution handler
    document.getElementById("checkSolution").addEventListener("click", function () {
        const sudokuInput = gatherSudokuInput();
        fetch("/check_solution", {
            method: "POST",
            body: JSON.stringify({ problem: sudokuInput }),
            headers: { "Content-Type": "application/json" },
        })
            .then(response => response.json())
            .then(data => displaySolutionMessage(data.solved))
            .catch(error => {
                console.error("Error checking solution:", error);
                displayErrorMessage("Could not check the solution. Please try again.");
            });
    });

    // Fetch Sudoku problem when "Generate Problem" is clicked
    document.getElementById("generateProblem").addEventListener("click", function () {
        const level = document.getElementById("difficulty").value;
        fetch(`/generate?level=${level}`)
            .then(async response => {
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || "Failed to generate Sudoku problem.");
                }
                return data;
            })
            .then(data => {
                fillSudokuBoard(data.problem);
                enableButtons();
            })
            .catch(error => {
                console.error("Error fetching Sudoku problem:", error);
                displayErrorMessage(error.message);
            });
    });

    // Input validation (1-9 only)
    document.querySelectorAll('input[type="text"]').forEach(input => {
        input.addEventListener("input", function () {
            if (!/^[1-9]$/.test(this.value)) {
                this.value = "";
            }
        });
    });
});
