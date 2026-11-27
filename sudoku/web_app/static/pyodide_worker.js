/* Web Worker that runs the Python `sudoku` package in-browser via Pyodide. */

const PYODIDE_INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.4/full/";

let pyodideInstance = null;
let dispatchFn = null;
let initPromise = null;

async function ensureInitialized(pkgUrl = "./sudoku_pkg.zip") {
    if (dispatchFn) return;
    if (initPromise) {
        await initPromise;
        return;
    }

    initPromise = (async () => {
        importScripts(`${PYODIDE_INDEX_URL}pyodide.js`);
        pyodideInstance = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });
        await pyodideInstance.loadPackage("numpy");

        const resp = await fetch(pkgUrl);
        if (!resp.ok) {
            throw new Error(
                `Failed to download Sudoku Python bundle (${resp.status}).`
            );
        }
        const buffer = await resp.arrayBuffer();
        pyodideInstance.unpackArchive(buffer, "zip");

        await pyodideInstance.runPythonAsync(`
import json
import sys

if "." not in sys.path:
    sys.path.insert(0, ".")

from sudoku.web_app import engine as _sudoku_engine


def _sudoku_dispatch(action: str, payload_json: str) -> str:
    try:
        data = json.loads(payload_json) if payload_json else {}
        if action == "generate":
            result = _sudoku_engine.generate_payload(
                level=data.get("level", 3),
                size=data.get("size"),
                allowed_values=data.get("allowed_values"),
                block_dim=data.get("block_dim"),
            )
        elif action == "solve":
            result = _sudoku_engine.solve_payload(data)
        elif action == "solve_steps":
            result = _sudoku_engine.solve_steps_payload(data)
        elif action == "check_solution":
            result = _sudoku_engine.check_solution_payload(data)
        else:
            raise ValueError(f"Unknown action: {action}")
        return json.dumps({"ok": True, "data": result})
    except (AssertionError, ValueError, TypeError) as err:
        return json.dumps({"ok": False, "error": str(err)})
`);

        dispatchFn = pyodideInstance.globals.get("_sudoku_dispatch");
    })();

    try {
        await initPromise;
    } catch (err) {
        initPromise = null;
        throw err;
    }
}

self.onmessage = async event => {
    const { id, type, action, payload, pkgUrl } = event.data || {};
    try {
        if (type === "init") {
            await ensureInitialized(pkgUrl);
            self.postMessage({ id, ok: true, data: { ready: true } });
            return;
        }

        if (type === "call") {
            await ensureInitialized(pkgUrl);
            const rawResult = dispatchFn(action, JSON.stringify(payload || {}));
            const parsed = JSON.parse(rawResult);
            if (parsed.ok) {
                self.postMessage({ id, ok: true, data: parsed.data });
            } else {
                self.postMessage({ id, ok: false, error: parsed.error });
            }
            return;
        }

        self.postMessage({ id, ok: false, error: `Unknown message type: ${type}` });
    } catch (err) {
        self.postMessage({
            id,
            ok: false,
            error: err && err.message ? err.message : String(err),
        });
    }
};
