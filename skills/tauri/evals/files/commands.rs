// src-tauri/src/commands.rs
use std::sync::Mutex;
use tauri::State;

pub struct Db {
    pub conn: rusqlite::Connection,
}

pub struct Cache {
    pub entries: Vec<String>,
}

// Called from the settings dialog whenever the user edits the endpoint field.
#[tauri::command]
pub fn validate_endpoint(url: String) -> bool {
    // blocking HTTPS request, 200 ms - 30 s depending on the network
    let resp = ureq::get(&url).call();
    resp.is_ok()
}

// Called on app start to warm the cache; reads ~5000 files.
#[tauri::command]
pub fn warm_cache(root: String, cache: State<Mutex<Cache>>) {
    let mut cache = cache.lock().unwrap();
    for entry in walkdir::WalkDir::new(&root).into_iter().flatten() {
        cache.entries.push(entry.path().display().to_string());
    }
}

#[tauri::command]
pub async fn search_notes(query: &str, db: State<'_, Mutex<Db>>) -> Vec<String> {
    let db = db.lock().unwrap();
    let mut stmt = db
        .conn
        .prepare("SELECT title FROM notes WHERE body LIKE ?1")
        .unwrap();
    let rows = stmt
        .query_map([format!("%{query}%")], |r| r.get::<_, String>(0))
        .unwrap();
    rows.flatten().collect()
}

#[tauri::command]
pub fn read_note(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn export_archive(paths: Vec<String>) -> Result<Vec<u8>, String> {
    // returns a 60-120 MB zip of the selected notes
    let mut out = Vec::new();
    for p in paths {
        out.extend_from_slice(&std::fs::read(&p).map_err(|e| e.to_string())?);
    }
    Ok(out)
}

#[tauri::command]
pub fn current_cache(cache: State<Cache>) -> usize {
    cache.entries.len()
}
