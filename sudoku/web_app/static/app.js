const BOARD_PRESETS = {
    "4x4": { blockDim: [2, 2], allowedValues: ["1", "2", "3", "4"] },
    "6x6": { blockDim: [2, 3], allowedValues: ["1", "2", "3", "4", "5", "6"] },
    "8x8": { blockDim: [2, 4], allowedValues: ["1", "2", "3", "4", "5", "6", "7", "8"] },
    "9x9": { blockDim: [3, 3], allowedValues: ["1", "2", "3", "4", "5", "6", "7", "8", "9"] },
    "16x16": {
        blockDim: [4, 4],
        allowedValues: "123456789abcdefg".split(""),
    },
};

const DIFFICULTY_LABELS = {
    1: "1 — Very Easy",
    2: "2 — Easy",
    3: "3 — Medium",
    4: "4 — Hard",
    5: "5 — Expert",
};

function parseCustomSymbols(raw) {
    const trimmed = String(raw || "").trim();
    if (!trimmed) return [];
    if (trimmed.includes(",")) {
        return trimmed
            .split(",")
            .map(s => s.trim())
            .filter(Boolean);
    }
    return Array.from(trimmed);
}

function normalizeCellSymbol(raw, allowedValues) {
    if (raw === null || raw === undefined) return "";
    const str = String(raw).trim();
    if (!str) return "";
    if (allowedValues.includes(str)) return str;
    // Allow case-insensitive match when unambiguous (e.g. 'A' -> 'a' in 16x16)
    const lower = str.toLowerCase();
    const ciMatches = allowedValues.filter(v => v.toLowerCase() === lower);
    if (ciMatches.length === 1) return ciMatches[0];
    return "";
}

function createEmptyGrid(n) {
    return Array.from({ length: n }, () => Array(n).fill(""));
}

const state = {
    sizeKey: "9x9",
    allowedValues: [...BOARD_PRESETS["9x9"].allowedValues],
    blockDim: [...BOARD_PRESETS["9x9"].blockDim],
    board: createEmptyGrid(9),
    prefilled: Array.from({ length: 9 }, () => Array(9).fill(false)),
    solverFilled: Array.from({ length: 9 }, () => Array(9).fill(false)),
    selected: null,
    isSolved: false,
    isBusy: false,
};

function setStatus(message, kind = "") {
    const el = document.getElementById("solutionMessage");
    if (!el) return;
    el.textContent = message;
    el.className = "status-message";
    if (kind === "success") el.classList.add("status-success");
    if (kind === "error") el.classList.add("status-error");
}

function clearStatus() {
    setStatus("", "");
}

function updateDifficultyLabel() {
    const slider = document.getElementById("difficulty");
    const label = document.getElementById("difficultyLabel");
    if (!slider || !label) return;
    const val = parseInt(slider.value, 10);
    label.textContent = DIFFICULTY_LABELS[val] || String(val);
    localStorage.setItem("difficulty", String(val));
}

function updateButtonStates() {
    const checkBtn = document.getElementById("checkSolution");
    const clearBtn = document.getElementById("clearInput");
    const solveBtn = document.getElementById("solveBtn");
    const genBtn = document.getElementById("generateProblem");
    const resetBtn = document.getElementById("resetAll");

    if (checkBtn) checkBtn.disabled = state.isBusy || state.isSolved;
    if (clearBtn) clearBtn.disabled = state.isBusy || state.isSolved;
    if (solveBtn) solveBtn.disabled = state.isBusy || state.isSolved;
    if (genBtn) genBtn.disabled = state.isBusy;
    if (resetBtn) resetBtn.disabled = state.isBusy;
}

function setBusy(busy) {
    state.isBusy = busy;
    updateButtonStates();
}

function renderBoard() {
    const boardEl = document.getElementById("sudokuBoard");
    if (!boardEl) return;

    const n = state.allowedValues.length;
    const [bRows, bCols] = state.blockDim;
    const maxLen = Math.max(...state.allowedValues.map(v => v.length));

    boardEl.innerHTML = "";
    boardEl.style.setProperty("--grid-size", String(n));
    boardEl.classList.toggle("size-16", n >= 12);

    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            const cell = document.createElement("div");
            cell.className = "cell";
            cell.dataset.row = String(r);
            cell.dataset.col = String(c);
            cell.setAttribute("role", "gridcell");

            if (c === n - 1) cell.classList.add("last-col");
            if (r === n - 1) cell.classList.add("last-row");
            if ((c + 1) % bCols === 0 && c !== n - 1) cell.classList.add("block-right");
            if ((r + 1) % bRows === 0 && r !== n - 1) cell.classList.add("block-bottom");

            if (state.prefilled[r][c]) cell.classList.add("prefilled");
            if (state.solverFilled[r][c]) cell.classList.add("solver-filled");
            if (state.selected && state.selected.row === r && state.selected.col === c) {
                cell.classList.add("selected");
            }

            const input = document.createElement("input");
            input.type = "text";
            input.className = "cell-input";
            input.name = `cell${r}${c}`;
            input.maxLength = maxLen;
            input.autocomplete = "off";
            input.value = state.board[r][c];
            input.readOnly = state.prefilled[r][c] || state.isSolved;
            input.setAttribute("aria-label", `Row ${r + 1} Column ${c + 1}`);

            input.addEventListener("focus", () => {
                selectCell(r, c);
            });

            input.addEventListener("input", () => {
                if (state.prefilled[r][c] || state.isSolved) {
                    input.value = state.board[r][c];
                    return;
                }
                const norm = normalizeCellSymbol(input.value, state.allowedValues);
                input.value = norm;
                state.board[r][c] = norm;
                state.solverFilled[r][c] = false;
                cell.classList.remove("solver-filled");
                clearStatus();
            });

            cell.addEventListener("click", () => {
                input.focus();
            });

            cell.appendChild(input);
            boardEl.appendChild(cell);
        }
    }
    updateButtonStates();
}

function selectCell(row, col) {
    state.selected = { row, col };
    document.querySelectorAll("#sudokuBoard .cell").forEach(cell => {
        const r = parseInt(cell.dataset.row, 10);
        const c = parseInt(cell.dataset.col, 10);
        cell.classList.toggle("selected", r === row && c === col);
    });
}

function applyBoardConfig(sizeKey, allowedValues, blockDim) {
    const n = allowedValues.length;
    state.sizeKey = sizeKey;
    state.allowedValues = [...allowedValues];
    state.blockDim = [...blockDim];
    state.board = createEmptyGrid(n);
    state.prefilled = Array.from({ length: n }, () => Array(n).fill(false));
    state.solverFilled = Array.from({ length: n }, () => Array(n).fill(false));
    state.selected = null;
    state.isSolved = false;
    clearStatus();
    renderBoard();
}

function loadBoardData(problem, { markPrefilled = true, markSolved = false } = {}) {
    const n = state.allowedValues.length;
    state.board = createEmptyGrid(n);
    state.prefilled = Array.from({ length: n }, () => Array(n).fill(false));
    state.solverFilled = Array.from({ length: n }, () => Array(n).fill(false));
    state.isSolved = markSolved;

    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            const val = normalizeCellSymbol(problem[r][c], state.allowedValues);
            state.board[r][c] = val;
            if (markPrefilled && val !== "") {
                state.prefilled[r][c] = true;
            }
        }
    }
    renderBoard();
}

function getPayload() {
    return {
        problem: state.board.map(row => row.map(v => (v === "" ? 0 : v))),
        allowed_values: state.allowedValues,
        block_dim: state.blockDim,
    };
}

async function handleGenerate() {
    const level = parseInt(document.getElementById("difficulty").value, 10);
    const params = new URLSearchParams({ level: String(level) });

    if (state.sizeKey !== "custom") {
        params.set("size", state.sizeKey);
    } else {
        params.set("allowed_values", state.allowedValues.join(","));
        params.set("block_rows", String(state.blockDim[0]));
        params.set("block_cols", String(state.blockDim[1]));
    }

    setBusy(true);
    setStatus("Generating puzzle…");
    try {
        const response = await fetch(`/generate?${params.toString()}`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Failed to generate Sudoku problem.");
        }
        state.allowedValues = data.allowed_values.map(String);
        state.blockDim = data.block_dim;
        loadBoardData(data.problem, { markPrefilled: true, markSolved: false });
        clearStatus();
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
}

async function handleSolve() {
    setBusy(true);
    setStatus("Solving…");
    try {
        const response = await fetch("/solve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(getPayload()),
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Could not solve this board.");
        }

        const n = state.allowedValues.length;
        for (let r = 0; r < n; r++) {
            for (let c = 0; c < n; c++) {
                const wasEmpty = state.board[r][c] === "";
                const solvedVal = normalizeCellSymbol(
                    data.solution[r][c],
                    state.allowedValues
                );
                state.board[r][c] = solvedVal;
                if (wasEmpty) {
                    state.solverFilled[r][c] = true;
                }
            }
        }
        state.isSolved = true;
        renderBoard();
        setStatus(
            `Solved in ${data.steps} step${data.steps === 1 ? "" : "s"} (${data.elapsed_ms} ms).`,
            "success"
        );
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
}

async function handleCheckSolution() {
    setBusy(true);
    try {
        const response = await fetch("/check_solution", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(getPayload()),
        });
        const data = await response.json();
        if (data.solved) {
            setStatus("Congratulations! The Sudoku is solved!", "success");
        } else {
            setStatus("Oops! The Sudoku is not solved yet.", "error");
        }
    } catch (error) {
        setStatus("Could not check the solution. Please try again.", "error");
    } finally {
        setBusy(false);
    }
}

function handleClearUserInputs() {
    const n = state.allowedValues.length;
    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            if (!state.prefilled[r][c]) {
                state.board[r][c] = "";
                state.solverFilled[r][c] = false;
            }
        }
    }
    state.isSolved = false;
    clearStatus();
    renderBoard();
}

function handleResetAll() {
    applyBoardConfig(state.sizeKey, state.allowedValues, state.blockDim);
}

function applyTheme(theme) {
    const isDark = theme === "dark";
    document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
    const toggleBtn = document.getElementById("themeToggle");
    if (toggleBtn) {
        toggleBtn.textContent = isDark ? "Light Mode" : "Dark Mode";
    }
    localStorage.setItem("sudokuTheme", isDark ? "dark" : "light");
}

function initTheme() {
    const saved = localStorage.getItem("sudokuTheme");
    const prefersDark =
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(saved || (prefersDark ? "dark" : "light"));
}

function hydrateInitialServerState() {
    const el = document.getElementById("initialState");
    if (!el) {
        renderBoard();
        return;
    }
    try {
        const init = JSON.parse(el.textContent);
        const hasValues =
            Array.isArray(init.solution) &&
            init.solution.some(row => row.some(v => v && v !== 0));
        if (hasValues) {
            const n = state.allowedValues.length;
            for (let r = 0; r < n; r++) {
                for (let c = 0; c < n; c++) {
                    state.board[r][c] = normalizeCellSymbol(
                        init.solution[r][c],
                        state.allowedValues
                    );
                    const orig =
                        init.original_puzzle && init.original_puzzle[r]
                            ? normalizeCellSymbol(
                                  init.original_puzzle[r][c],
                                  state.allowedValues
                              )
                            : "";
                    if (orig !== "") {
                        state.prefilled[r][c] = true;
                    } else if (init.is_solved && state.board[r][c] !== "") {
                        state.solverFilled[r][c] = true;
                    }
                }
            }
            state.isSolved = Boolean(init.is_solved);
        }
        renderBoard();
        if (init.error_message) {
            setStatus(init.error_message, "error");
        }
    } catch (_) {
        renderBoard();
    }
}

if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", () => {
        localStorage.removeItem("buttonsDisabled");
        initTheme();

        const difficultySlider = document.getElementById("difficulty");
        const savedDifficulty = localStorage.getItem("difficulty");
        if (savedDifficulty && difficultySlider) {
            difficultySlider.value = savedDifficulty;
        }
        updateDifficultyLabel();
        difficultySlider.addEventListener("input", updateDifficultyLabel);

        document.getElementById("themeToggle").addEventListener("click", () => {
            const cur = document.documentElement.getAttribute("data-theme");
            applyTheme(cur === "dark" ? "light" : "dark");
        });

        const sizeSelect = document.getElementById("boardSize");
        const customConfig = document.getElementById("customConfig");
        sizeSelect.addEventListener("change", () => {
            const key = sizeSelect.value;
            if (key === "custom") {
                customConfig.classList.remove("hidden");
            } else {
                customConfig.classList.add("hidden");
                const preset = BOARD_PRESETS[key];
                applyBoardConfig(key, preset.allowedValues, preset.blockDim);
            }
        });

        document.getElementById("applyCustom").addEventListener("click", () => {
            const symbols = parseCustomSymbols(
                document.getElementById("customSymbols").value
            );
            const bRows = parseInt(
                document.getElementById("customBlockRows").value,
                10
            );
            const bCols = parseInt(
                document.getElementById("customBlockCols").value,
                10
            );

            if (symbols.length < 2) {
                setStatus("Please provide at least 2 allowed symbols.", "error");
                return;
            }
            if (new Set(symbols).size !== symbols.length) {
                setStatus("Allowed symbols must not contain duplicates.", "error");
                return;
            }
            if (!Number.isInteger(bRows) || !Number.isInteger(bCols) || bRows <= 0 || bCols <= 0) {
                setStatus("Block dimensions must be positive integers.", "error");
                return;
            }
            if (bRows * bCols !== symbols.length) {
                setStatus(
                    `Block dimensions (${bRows}×${bCols}=${bRows * bCols}) must equal the number of symbols (${symbols.length}).`,
                    "error"
                );
                return;
            }
            applyBoardConfig("custom", symbols, [bRows, bCols]);
        });

        document.getElementById("generateProblem").addEventListener("click", handleGenerate);
        document.getElementById("solveBtn").addEventListener("click", handleSolve);
        document.getElementById("checkSolution").addEventListener("click", handleCheckSolution);
        document.getElementById("clearInput").addEventListener("click", handleClearUserInputs);
        document.getElementById("resetAll").addEventListener("click", handleResetAll);

        hydrateInitialServerState();
    });
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        BOARD_PRESETS,
        DIFFICULTY_LABELS,
        parseCustomSymbols,
        normalizeCellSymbol,
        createEmptyGrid,
    };
}
