// src/lib/projects.ts — every backend call the renderer makes
import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';
import { readTextFile } from '@tauri-apps/plugin-fs';

export async function pickAndLoadProject(): Promise<string> {
  const picked = await open({ directory: true, multiple: false });
  if (typeof picked !== 'string') throw new Error('cancelled');

  const manifest = await readTextFile(`${picked}/project.json`);
  console.log('manifest bytes', manifest.length);

  return invoke<string>('load_project', { project_path: picked });
}

export async function recentProjects(): Promise<string[]> {
  return invoke<string[]>('list_recent');
}

export async function exportReport(targetDir: string): Promise<string> {
  return invoke<string>('export_report', { targetDir });
}
