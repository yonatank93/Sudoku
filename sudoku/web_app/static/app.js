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

function isSamePeer(r1, c1, r2, c2, blockDim) {
    if (r1 === r2 || c1 === c2) return true;
    const [bRows, bCols] = blockDim;
    return (
        Math.floor(r1 / bRows) === Math.floor(r2 / bRows) &&
        Math.floor(c1 / bCols) === Math.floor(c2 / bCols)
    );
}

function findConflicts(board, blockDim) {
    const conflicts = new Set();
    const n = board.length;
    const [bRows, bCols] = blockDim;

    const markGroup = coords => {
        const seen = new Map();
        for (const [r, c] of coords) {
            const val = board[r][c];
            if (!val) continue;
            if (!seen.has(val)) {
                seen.set(val, [[r, c]]);
            } else {
                seen.get(val).push([r, c]);
            }
        }
        for (const positions of seen.values()) {
            if (positions.length > 1) {
                for (const [r, c] of positions) {
                    conflicts.add(`${r},${c}`);
                }
            }
        }
    };

    for (let r = 0; r < n; r++) {
        markGroup(Array.from({ length: n }, (_, c) => [r, c]));
    }
    for (let c = 0; c < n; c++) {
        markGroup(Array.from({ length: n }, (_, r) => [r, c]));
    }
    for (let br = 0; br < n; br += bRows) {
        for (let bc = 0; bc < n; bc += bCols) {
            const coords = [];
            for (let dr = 0; dr < bRows; dr++) {
                for (let dc = 0; dc < bCols; dc++) {
                    coords.push([br + dr, bc + dc]);
                }
            }
            markGroup(coords);
        }
    }
    return conflicts;
}

function countRemainingSymbols(board, allowedValues) {
    const n = allowedValues.length;
    const counts = {};
    for (const sym of allowedValues) {
        counts[sym] = n;
    }
    for (let r = 0; r < board.length; r++) {
        for (let c = 0; c < board[r].length; c++) {
            const val = board[r][c];
            if (val && Object.prototype.hasOwnProperty.call(counts, val)) {
                counts[val] -= 1;
            }
        }
    }
    return counts;
}

const state = {
    sizeKey: "9x9",
    allowedValues: [...BOARD_PRESETS["9x9"].allowedValues],
    blockDim: [...BOARD_PRESETS["9x9"].blockDim],
    board: createEmptyGrid(9),
    prefilled: Array.from({ length: 9 }, () => Array(9).fill(false)),
    solverFilled: Array.from({ length: 9 }, () => Array(9).fill(false)),
    selected: null,
    highlightConflicts: true,
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

function setCellValue(row, col, rawVal) {
    if (state.prefilled[row][col] || state.isSolved || state.isBusy) return;
    const norm = normalizeCellSymbol(rawVal, state.allowedValues);
    state.board[row][col] = norm;
    state.solverFilled[row][col] = false;

    const input = document.querySelector(`#sudokuBoard input[name="cell${row}${col}"]`);
    if (input) input.value = norm;
    const cell = input ? input.parentElement : null;
    if (cell) cell.classList.remove("solver-filled");

    clearStatus();
    refreshHighlights();
    renderSymbolPad();
}

function focusCell(row, col) {
    const n = state.allowedValues.length;
    const nr = Math.max(0, Math.min(n - 1, row));
    const nc = Math.max(0, Math.min(n - 1, col));
    const input = document.querySelector(`#sudokuBoard input[name="cell${nr}${nc}"]`);
    if (input) {
        input.focus();
    } else {
        selectCell(nr, nc);
    }
}

function refreshHighlights() {
    const conflicts = state.highlightConflicts
        ? findConflicts(state.board, state.blockDim)
        : new Set();
    const sel = state.selected;
    const selVal = sel ? state.board[sel.row][sel.col] : "";

    document.querySelectorAll("#sudokuBoard .cell").forEach(cell => {
        const r = parseInt(cell.dataset.row, 10);
        const c = parseInt(cell.dataset.col, 10);
        const isSel = Boolean(sel && sel.row === r && sel.col === c);
        const isPeer = Boolean(
            sel && !isSel && isSamePeer(sel.row, sel.col, r, c, state.blockDim)
        );
        const isSameVal = Boolean(selVal && !isSel && state.board[r][c] === selVal);
        const isConflict = conflicts.has(`${r},${c}`);

        cell.classList.toggle("selected", isSel);
        cell.classList.toggle("peer", isPeer);
        cell.classList.toggle("same-value", isSameVal);
        cell.classList.toggle("conflict", isConflict);
    });
}

function renderSymbolPad() {
    const padEl = document.getElementById("symbolPad");
    if (!padEl) return;

    const remaining = countRemainingSymbols(state.board, state.allowedValues);
    padEl.innerHTML = "";

    for (const sym of state.allowedValues) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "pad-btn";
        const rem = remaining[sym];
        if (rem <= 0) btn.classList.add("completed");
        btn.disabled = state.isBusy || state.isSolved;

        const symSpan = document.createElement("span");
        symSpan.textContent = sym;
        const countSpan = document.createElement("span");
        countSpan.className = "pad-count";
        countSpan.textContent = String(Math.max(0, rem));

        btn.appendChild(symSpan);
        btn.appendChild(countSpan);
        btn.addEventListener("click", () => {
            if (!state.selected) return;
            setCellValue(state.selected.row, state.selected.col, sym);
        });
        padEl.appendChild(btn);
    }

    const eraseBtn = document.createElement("button");
    eraseBtn.type = "button";
    eraseBtn.className = "pad-btn erase-btn";
    eraseBtn.textContent = "Erase";
    eraseBtn.disabled = state.isBusy || state.isSolved;
    eraseBtn.addEventListener("click", () => {
        if (!state.selected) return;
        setCellValue(state.selected.row, state.selected.col, "");
    });
    padEl.appendChild(eraseBtn);
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

            input.addEventListener("keydown", evt => {
                if (evt.key === "ArrowUp") {
                    evt.preventDefault();
                    focusCell(r - 1, c);
                } else if (evt.key === "ArrowDown") {
                    evt.preventDefault();
                    focusCell(r + 1, c);
                } else if (evt.key === "ArrowLeft") {
                    evt.preventDefault();
                    focusCell(r, c - 1);
                } else if (evt.key === "ArrowRight") {
                    evt.preventDefault();
                    focusCell(r, c + 1);
                } else if (evt.key === "Backspace" || evt.key === "Delete") {
                    evt.preventDefault();
                    setCellValue(r, c, "");
                } else if (
                    maxLen === 1 &&
                    evt.key.length === 1 &&
                    !evt.ctrlKey &&
                    !evt.metaKey &&
                    !evt.altKey
                ) {
                    const norm = normalizeCellSymbol(evt.key, state.allowedValues);
                    evt.preventDefault();
                    if (norm) {
                        setCellValue(r, c, norm);
                    }
                }
            });

            input.addEventListener("input", () => {
                if (state.prefilled[r][c] || state.isSolved) {
                    input.value = state.board[r][c];
                    return;
                }
                setCellValue(r, c, input.value);
            });

            cell.addEventListener("click", () => {
                input.focus();
            });

            cell.appendChild(input);
            boardEl.appendChild(cell);
        }
    }
    refreshHighlights();
    renderSymbolPad();
    updateButtonStates();
}

function selectCell(row, col) {
    state.selected = { row, col };
    refreshHighlights();
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

        const conflictToggle = document.getElementById("conflictToggle");
        const savedConflict = localStorage.getItem("sudokuConflicts");
        if (savedConflict !== null) {
            state.highlightConflicts = savedConflict === "true";
            conflictToggle.checked = state.highlightConflicts;
        }
        conflictToggle.addEventListener("change", () => {
            state.highlightConflicts = conflictToggle.checked;
            localStorage.setItem("sudokuConflicts", String(state.highlightConflicts));
            refreshHighlights();
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
        isSamePeer,
        findConflicts,
        countRemainingSymbols,
    };
}
