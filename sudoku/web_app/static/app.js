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

function createEmptyNotes(n) {
    return Array.from({ length: n }, () =>
        Array.from({ length: n }, () => new Set())
    );
}

function cloneGrid(grid) {
    return grid.map(row => [...row]);
}

function cloneNotes(notes) {
    return notes.map(row => row.map(set => new Set(set)));
}

function clearPeerNotes(notes, row, col, symbol, blockDim) {
    const n = notes.length;
    notes[row][col].clear();
    if (!symbol) return;
    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            if (isSamePeer(row, col, r, c, blockDim)) {
                notes[r][c].delete(symbol);
            }
        }
    }
}

function formatTime(totalSeconds) {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function serializeBoardToText(board, allowedValues) {
    const emptyChar = allowedValues.includes("0") ? "_" : "0";
    const multiChar = allowedValues.some(v => v.length > 1);
    const sep = multiChar ? " " : "";
    return board
        .map(row => row.map(v => (v === "" ? emptyChar : v)).join(sep))
        .join("\n");
}

function parseBoardFromText(text, allowedValues) {
    const n = allowedValues.length;
    const lines = String(text || "")
        .split(/\r?\n/)
        .map(l => l.trim())
        .filter(Boolean);

    if (lines.length !== n) {
        throw new Error(`Expected ${n} non-empty rows, got ${lines.length}.`);
    }

    const emptyTokens = new Set(["_", "-", "."]);
    if (!allowedValues.includes("0")) {
        emptyTokens.add("0");
    }
    const multiChar = allowedValues.some(v => v.length > 1);
    const board = [];

    for (let r = 0; r < n; r++) {
        const line = lines[r];
        let tokens;
        if (multiChar || line.includes(" ") || line.includes(",")) {
            tokens = line.split(/[\s,]+/).filter(Boolean);
        } else {
            tokens = Array.from(line);
        }

        if (tokens.length !== n) {
            throw new Error(
                `Row ${r + 1} must have ${n} entries, got ${tokens.length}.`
            );
        }

        const row = [];
        for (let c = 0; c < n; c++) {
            const tok = tokens[c];
            if (emptyTokens.has(tok)) {
                row.push("");
            } else {
                const norm = normalizeCellSymbol(tok, allowedValues);
                if (!norm) {
                    throw new Error(
                        `Invalid symbol '${tok}' at row ${r + 1}, column ${c + 1}.`
                    );
                }
                row.push(norm);
            }
        }
        board.push(row);
    }
    return board;
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
    notes: createEmptyNotes(9),
    prefilled: Array.from({ length: 9 }, () => Array(9).fill(false)),
    solverFilled: Array.from({ length: 9 }, () => Array(9).fill(false)),
    stepChanged: new Set(),
    stepTrace: null,
    stepIndex: 0,
    animTimerId: null,
    undoStack: [],
    redoStack: [],
    selected: null,
    highlightConflicts: true,
    notesMode: false,
    elapsedSeconds: 0,
    timerId: null,
    timerPaused: false,
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

function updateTimerDisplay() {
    const el = document.getElementById("timerDisplay");
    if (el) el.textContent = formatTime(state.elapsedSeconds);
}

function startTimer() {
    if (state.timerId !== null || state.isSolved || state.timerPaused) return;
    state.timerId = setInterval(() => {
        state.elapsedSeconds += 1;
        updateTimerDisplay();
    }, 1000);
}

function stopTimer() {
    if (state.timerId !== null) {
        clearInterval(state.timerId);
        state.timerId = null;
    }
}

function resetTimer({ autoStart = false } = {}) {
    stopTimer();
    state.elapsedSeconds = 0;
    state.timerPaused = false;
    updatePauseUI();
    updateTimerDisplay();
    if (autoStart) startTimer();
}

function updatePauseUI() {
    const boardEl = document.getElementById("sudokuBoard");
    const overlay = document.getElementById("pauseOverlay");
    const pauseBtn = document.getElementById("pauseBtn");
    if (boardEl) boardEl.classList.toggle("paused", state.timerPaused);
    if (overlay) overlay.classList.toggle("hidden", !state.timerPaused);
    if (pauseBtn) pauseBtn.textContent = state.timerPaused ? "Resume" : "Pause";
}

function togglePause() {
    if (state.isSolved || state.isBusy) return;
    if (state.timerPaused) {
        state.timerPaused = false;
        updatePauseUI();
        startTimer();
    } else {
        state.timerPaused = true;
        stopTimer();
        updatePauseUI();
    }
    updateButtonStates();
}

function updateNotesButton() {
    const btn = document.getElementById("notesBtn");
    if (!btn) return;
    btn.textContent = state.notesMode ? "Notes: ON" : "Notes: OFF";
    btn.setAttribute("aria-pressed", String(state.notesMode));
    btn.classList.toggle("btn-active", state.notesMode);
}

function snapshotState() {
    return {
        board: cloneGrid(state.board),
        notes: cloneNotes(state.notes),
        solverFilled: cloneGrid(state.solverFilled),
    };
}

function pushHistory() {
    state.undoStack.push(snapshotState());
    if (state.undoStack.length > 200) {
        state.undoStack.shift();
    }
    state.redoStack = [];
}

function clearHistory() {
    state.undoStack = [];
    state.redoStack = [];
}

function handleUndo() {
    if (!state.undoStack.length || state.isBusy || state.isSolved || state.timerPaused) return;
    invalidateStepTrace();
    state.redoStack.push(snapshotState());
    const prev = state.undoStack.pop();
    state.board = prev.board;
    state.notes = prev.notes;
    state.solverFilled = prev.solverFilled;
    clearStatus();
    renderBoard();
}

function handleRedo() {
    if (!state.redoStack.length || state.isBusy || state.isSolved || state.timerPaused) return;
    invalidateStepTrace();
    state.undoStack.push(snapshotState());
    const next = state.redoStack.pop();
    state.board = next.board;
    state.notes = next.notes;
    state.solverFilled = next.solverFilled;
    clearStatus();
    renderBoard();
}

function stopAnimation() {
    if (state.animTimerId !== null) {
        clearInterval(state.animTimerId);
        state.animTimerId = null;
    }
    const animBtn = document.getElementById("animateBtn");
    if (animBtn) animBtn.textContent = "Watch Solve";
}

function invalidateStepTrace() {
    stopAnimation();
    state.stepTrace = null;
    state.stepIndex = 0;
    state.stepChanged = new Set();
}

function updateButtonStates() {
    const checkBtn = document.getElementById("checkSolution");
    const clearBtn = document.getElementById("clearInput");
    const solveBtn = document.getElementById("solveBtn");
    const genBtn = document.getElementById("generateProblem");
    const resetBtn = document.getElementById("resetAll");
    const undoBtn = document.getElementById("undoBtn");
    const redoBtn = document.getElementById("redoBtn");
    const notesBtn = document.getElementById("notesBtn");
    const pauseBtn = document.getElementById("pauseBtn");
    const stepBtn = document.getElementById("stepBtn");
    const animBtn = document.getElementById("animateBtn");

    const animating = state.animTimerId !== null;
    const locked = state.isBusy || state.isSolved || state.timerPaused || animating;
    if (checkBtn) checkBtn.disabled = locked;
    if (clearBtn) clearBtn.disabled = locked;
    if (solveBtn) solveBtn.disabled = locked;
    if (stepBtn) stepBtn.disabled = locked;
    if (animBtn) animBtn.disabled = state.isBusy || state.isSolved || state.timerPaused;
    if (genBtn) genBtn.disabled = state.isBusy;
    if (resetBtn) resetBtn.disabled = state.isBusy;
    if (undoBtn) undoBtn.disabled = locked || state.undoStack.length === 0;
    if (redoBtn) redoBtn.disabled = locked || state.redoStack.length === 0;
    if (notesBtn) notesBtn.disabled = locked;
    if (pauseBtn) pauseBtn.disabled = state.isBusy || state.isSolved || animating;
    updateNotesButton();
}

function setBusy(busy) {
    state.isBusy = busy;
    updateButtonStates();
}

function renderCellNotes(cell, row, col) {
    const existing = cell.querySelector(".notes-grid");
    if (existing) existing.remove();

    if (state.board[row][col] !== "") return;
    const cellNotes = state.notes[row][col];
    if (!cellNotes || cellNotes.size === 0) return;

    const n = state.allowedValues.length;
    const cols = Math.ceil(Math.sqrt(n));
    const grid = document.createElement("div");
    grid.className = "notes-grid";
    grid.style.setProperty("--notes-cols", String(cols));

    for (const sym of state.allowedValues) {
        const span = document.createElement("span");
        span.className = "note-item";
        if (cellNotes.has(sym)) {
            span.classList.add("active");
            span.textContent = sym;
        }
        grid.appendChild(span);
    }
    cell.appendChild(grid);
}

function setCellValue(row, col, rawVal, { forceValue = false } = {}) {
    if (state.prefilled[row][col] || state.isSolved || state.isBusy || state.timerPaused) {
        return;
    }
    const norm = normalizeCellSymbol(rawVal, state.allowedValues);

    if (state.notesMode && !forceValue) {
        if (state.board[row][col] !== "") {
            // In notes mode, erasing clears the value; otherwise ignore on filled cell
            if (norm === "") {
                pushHistory();
                state.board[row][col] = "";
                state.solverFilled[row][col] = false;
                startTimer();
                clearStatus();
                renderBoard();
            }
            return;
        }
        pushHistory();
        if (norm === "") {
            state.notes[row][col].clear();
        } else if (state.notes[row][col].has(norm)) {
            state.notes[row][col].delete(norm);
        } else {
            state.notes[row][col].add(norm);
        }
        startTimer();
        clearStatus();
        const cell = document.querySelector(
            `#sudokuBoard .cell[data-row="${row}"][data-col="${col}"]`
        );
        if (cell) renderCellNotes(cell, row, col);
        updateButtonStates();
        return;
    }

    if (state.board[row][col] === norm && (norm !== "" || state.notes[row][col].size === 0)) {
        const input = document.querySelector(`#sudokuBoard input[name="cell${row}${col}"]`);
        if (input) input.value = norm;
        return;
    }

    pushHistory();
    invalidateStepTrace();
    state.board[row][col] = norm;
    state.solverFilled[row][col] = false;
    if (norm !== "") {
        clearPeerNotes(state.notes, row, col, norm, state.blockDim);
    } else {
        state.notes[row][col].clear();
    }

    startTimer();
    clearStatus();
    renderBoard();
    focusCell(row, col);
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
        btn.disabled = state.isBusy || state.isSolved || state.timerPaused;

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
    eraseBtn.disabled = state.isBusy || state.isSolved || state.timerPaused;
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
            if (state.stepChanged.has(`${r},${c}`)) cell.classList.add("step-changed");

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
            renderCellNotes(cell, r, c);
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
    invalidateStepTrace();
    const n = allowedValues.length;
    state.sizeKey = sizeKey;
    state.allowedValues = [...allowedValues];
    state.blockDim = [...blockDim];
    state.board = createEmptyGrid(n);
    state.notes = createEmptyNotes(n);
    state.prefilled = Array.from({ length: n }, () => Array(n).fill(false));
    state.solverFilled = Array.from({ length: n }, () => Array(n).fill(false));
    clearHistory();
    state.selected = null;
    state.isSolved = false;
    resetTimer({ autoStart: false });
    clearStatus();
    renderBoard();
}

function loadBoardData(problem, { markPrefilled = true, markSolved = false } = {}) {
    invalidateStepTrace();
    const n = state.allowedValues.length;
    state.board = createEmptyGrid(n);
    state.notes = createEmptyNotes(n);
    state.prefilled = Array.from({ length: n }, () => Array(n).fill(false));
    state.solverFilled = Array.from({ length: n }, () => Array(n).fill(false));
    clearHistory();
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
    resetTimer({ autoStart: markPrefilled && !markSolved });
    renderBoard();
}

function getPayload() {
    return {
        problem: state.board.map(row => row.map(v => (v === "" ? 0 : v))),
        allowed_values: state.allowedValues,
        block_dim: state.blockDim,
    };
}

let pyodideWorker = null;
let pyodideNextId = 1;
const pyodidePending = new Map();

function isPyodideMode() {
    return (
        typeof document !== "undefined" &&
        document.body &&
        document.body.dataset.mode === "pyodide"
    );
}

function getPyodideWorker() {
    if (!pyodideWorker) {
        const workerUrl =
            (document.body && document.body.dataset.workerUrl) ||
            "./pyodide_worker.js";
        pyodideWorker = new Worker(workerUrl);
        pyodideWorker.onmessage = event => {
            const { id, ok, data, error } = event.data || {};
            const entry = pyodidePending.get(id);
            if (!entry) return;
            pyodidePending.delete(id);
            if (ok) {
                entry.resolve(data);
            } else {
                entry.reject(new Error(error || "Python engine error."));
            }
        };
        pyodideWorker.onerror = err => {
            const msg = (err && err.message) || "Pyodide worker failed.";
            for (const entry of pyodidePending.values()) {
                entry.reject(new Error(msg));
            }
            pyodidePending.clear();
        };
    }
    return pyodideWorker;
}

function sendWorkerMessage(message) {
    return new Promise((resolve, reject) => {
        const id = pyodideNextId++;
        pyodidePending.set(id, { resolve, reject });
        getPyodideWorker().postMessage({ ...message, id });
    });
}

async function initPyodideBackend() {
    const pkgUrl =
        (document.body && document.body.dataset.pkgUrl) || "./sudoku_pkg.zip";
    setBusy(true);
    setStatus("Loading Python Sudoku engine (first visit may take a few seconds)…");
    try {
        await sendWorkerMessage({ type: "init", pkgUrl });
        setStatus("Python engine ready! Click Generate Puzzle or enter a board.", "success");
    } catch (error) {
        setStatus(`Failed to load Python engine: ${error.message}`, "error");
    } finally {
        setBusy(false);
    }
}

async function apiRequest(action, payload) {
    if (isPyodideMode()) {
        return sendWorkerMessage({ type: "call", action, payload });
    }

    if (action === "generate") {
        const params = new URLSearchParams({ level: String(payload.level) });
        if (payload.size) {
            params.set("size", payload.size);
        } else {
            params.set("allowed_values", payload.allowed_values.join(","));
            params.set("block_rows", String(payload.block_dim[0]));
            params.set("block_cols", String(payload.block_dim[1]));
        }
        const response = await fetch(`/generate?${params.toString()}`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Failed to generate Sudoku problem.");
        }
        return data;
    }

    const endpointMap = {
        solve: "/solve",
        solve_steps: "/solve_steps",
        check_solution: "/check_solution",
    };
    const response = await fetch(endpointMap[action], {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Request failed.");
    }
    return data;
}

async function handleGenerate() {
    const level = parseInt(document.getElementById("difficulty").value, 10);
    const reqPayload =
        state.sizeKey !== "custom"
            ? { level, size: state.sizeKey }
            : {
                  level,
                  allowed_values: state.allowedValues,
                  block_dim: state.blockDim,
              };

    setBusy(true);
    setStatus("Generating puzzle…");
    try {
        const data = await apiRequest("generate", reqPayload);
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
    invalidateStepTrace();
    setBusy(true);
    setStatus("Solving…");
    try {
        const data = await apiRequest("solve", getPayload());

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
        state.notes = createEmptyNotes(n);
        state.isSolved = true;
        stopTimer();
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
        const data = await apiRequest("check_solution", getPayload());
        if (data.solved) {
            stopTimer();
            setStatus(
                `Congratulations! Solved in ${formatTime(state.elapsedSeconds)}!`,
                "success"
            );
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
    pushHistory();
    invalidateStepTrace();
    const n = state.allowedValues.length;
    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            if (!state.prefilled[r][c]) {
                state.board[r][c] = "";
                state.solverFilled[r][c] = false;
            }
            state.notes[r][c].clear();
        }
    }
    state.isSolved = false;
    clearStatus();
    renderBoard();
}

async function ensureStepTrace() {
    if (state.stepTrace && state.stepIndex < state.stepTrace.length) {
        return true;
    }
    setBusy(true);
    setStatus("Computing solver steps…");
    try {
        const data = await apiRequest("solve_steps", getPayload());
        state.stepTrace = data.steps;
        state.stepIndex = 0;
        if (data.total_steps === 0) {
            state.isSolved = true;
            stopTimer();
            renderBoard();
            setStatus("Board is already solved!", "success");
            return false;
        }
        return true;
    } catch (error) {
        setStatus(error.message, "error");
        return false;
    } finally {
        setBusy(false);
    }
}

function applyNextStep() {
    if (!state.stepTrace || state.stepIndex >= state.stepTrace.length) {
        stopAnimation();
        updateButtonStates();
        return false;
    }

    const stepData = state.stepTrace[state.stepIndex];
    state.stepIndex += 1;

    const n = state.allowedValues.length;
    state.notes = createEmptyNotes(n);
    state.stepChanged = new Set(stepData.changed.map(([r, c]) => `${r},${c}`));

    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            const val = normalizeCellSymbol(
                stepData.board[r][c],
                state.allowedValues
            );
            state.board[r][c] = val;
            if (!state.prefilled[r][c] && val !== "") {
                state.solverFilled[r][c] = true;
            } else if (val === "") {
                state.solverFilled[r][c] = false;
            }
        }
    }

    const total = state.stepTrace.length;
    if (stepData.empty_count === 0) {
        state.isSolved = true;
        stopTimer();
        stopAnimation();
        renderBoard();
        setStatus(`Solved in ${total} step${total === 1 ? "" : "s"}!`, "success");
        return false;
    }

    renderBoard();
    const note = stepData.reverted ? " (backtracking)" : "";
    setStatus(
        `Step ${stepData.step} / ${total}${note} — ${stepData.empty_count} empty cell${stepData.empty_count === 1 ? "" : "s"} left.`
    );
    return true;
}

async function handleStep() {
    const ready = await ensureStepTrace();
    if (!ready) return;
    applyNextStep();
}

async function handleToggleAnimate() {
    if (state.animTimerId !== null) {
        stopAnimation();
        updateButtonStates();
        return;
    }
    const ready = await ensureStepTrace();
    if (!ready) return;

    const speedMs = parseInt(document.getElementById("animSpeed").value, 10) || 450;
    const animBtn = document.getElementById("animateBtn");
    if (animBtn) animBtn.textContent = "Stop";

    if (!applyNextStep()) return;
    state.animTimerId = setInterval(() => {
        applyNextStep();
    }, speedMs);
    updateButtonStates();
}

function handleLoadPastedPuzzle() {
    const textarea = document.getElementById("puzzleText");
    if (!textarea) return;
    try {
        const parsed = parseBoardFromText(textarea.value, state.allowedValues);
        loadBoardData(parsed, { markPrefilled: true, markSolved: false });
        setStatus("Puzzle loaded.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function handleCopyBoard() {
    const text = serializeBoardToText(state.board, state.allowedValues);
    const textarea = document.getElementById("puzzleText");
    if (textarea) textarea.value = text;
    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
            setStatus("Board copied to clipboard!", "success");
            return;
        }
    } catch (_) {
        // Fallback below
    }
    setStatus("Board text placed in the box above for copying.");
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

        document.getElementById("notesBtn").addEventListener("click", () => {
            state.notesMode = !state.notesMode;
            updateNotesButton();
        });
        document.getElementById("undoBtn").addEventListener("click", handleUndo);
        document.getElementById("redoBtn").addEventListener("click", handleRedo);
        document.getElementById("pauseBtn").addEventListener("click", togglePause);
        document.getElementById("resumeOverlayBtn").addEventListener("click", togglePause);

        document.addEventListener("keydown", evt => {
            const mod = evt.ctrlKey || evt.metaKey;
            if (mod && evt.key.toLowerCase() === "z") {
                evt.preventDefault();
                if (evt.shiftKey) {
                    handleRedo();
                } else {
                    handleUndo();
                }
            } else if (mod && evt.key.toLowerCase() === "y") {
                evt.preventDefault();
                handleRedo();
            }
        });

        document.getElementById("generateProblem").addEventListener("click", handleGenerate);
        document.getElementById("solveBtn").addEventListener("click", handleSolve);
        document.getElementById("checkSolution").addEventListener("click", handleCheckSolution);
        document.getElementById("clearInput").addEventListener("click", handleClearUserInputs);
        document.getElementById("resetAll").addEventListener("click", handleResetAll);
        document.getElementById("stepBtn").addEventListener("click", handleStep);
        document.getElementById("animateBtn").addEventListener("click", handleToggleAnimate);

        const ioPanel = document.getElementById("ioPanel");
        document.getElementById("ioToggleBtn").addEventListener("click", () => {
            ioPanel.classList.toggle("hidden");
            if (!ioPanel.classList.contains("hidden")) {
                const ta = document.getElementById("puzzleText");
                if (ta && !ta.value.trim()) {
                    ta.value = serializeBoardToText(state.board, state.allowedValues);
                }
            }
        });
        document.getElementById("closeIoBtn").addEventListener("click", () => {
            ioPanel.classList.add("hidden");
        });
        document.getElementById("loadPuzzleBtn").addEventListener("click", handleLoadPastedPuzzle);
        document.getElementById("copyBoardBtn").addEventListener("click", handleCopyBoard);

        hydrateInitialServerState();
        if (isPyodideMode()) {
            initPyodideBackend();
        }
    });
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        BOARD_PRESETS,
        DIFFICULTY_LABELS,
        parseCustomSymbols,
        normalizeCellSymbol,
        createEmptyGrid,
        createEmptyNotes,
        cloneGrid,
        cloneNotes,
        clearPeerNotes,
        formatTime,
        serializeBoardToText,
        parseBoardFromText,
        isSamePeer,
        findConflicts,
        countRemainingSymbols,
    };
}
