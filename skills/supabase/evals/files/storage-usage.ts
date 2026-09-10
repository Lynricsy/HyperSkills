// src/receipts.ts — runs in the browser with the publishable key.
import { supabase } from './supabase-browser'

export async function saveReceipt(userId: string, file: File) {
  // Re-uploading the same month's receipt is expected to replace the old one.
  const { error } = await supabase.storage
    .from('receipts')
    .upload(`${userId}/${file.name}`, file, { upsert: true })

  if (error) throw error

  // The URL this returns 400s for every signed-in user.
  const { data } = supabase.storage
    .from('receipts')
    .getPublicUrl(`${userId}/${file.name}`)

  return data.publicUrl
}

export async function listReceipts(userId: string) {
  // Always resolves to an empty array.
  const { data } = await supabase.storage.from('receipts').list(userId)
  return data
}
