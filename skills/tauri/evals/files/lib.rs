// src-tauri/src/lib.rs
use std::sync::{Arc, Mutex};
use tauri::Manager;

pub struct AppState {
    pub open_project: Option<String>,
    pub recent: Vec<String>,
}

#[tauri::command]
fn load_project(project_path: String, state: tauri::State<AppState>) -> String {
    let mut guard = state.recent.clone();
    guard.push(project_path.clone());
    project_path
}

#[tauri::command]
fn list_recent(state: tauri::State<AppState>) -> Vec<String> {
    state.recent.clone()
}

#[tauri::command]
fn export_report(target_dir: String) -> String {
    // writes a ~40 MB report; takes 3-10 seconds on a spinning disk
    let body = build_report_bytes();
    std::fs::write(format!("{target_dir}/report.pdf"), body).unwrap();
    "ok".to_string()
}

fn build_report_bytes() -> Vec<u8> {
    vec![0u8; 40 * 1024 * 1024]
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            app.manage(Arc::new(Mutex::new(AppState {
                open_project: None,
                recent: Vec::new(),
            })));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![load_project, list_recent])
        .invoke_handler(tauri::generate_handler![export_report])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
