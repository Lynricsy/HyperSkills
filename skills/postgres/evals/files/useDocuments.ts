// apps/web/src/hooks/useDocuments.ts
import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
);

export async function listDocuments() {
  // Returns [] in the browser. The identical select in the Supabase
  // SQL editor returns all 240 rows.
  const { data, error } = await supabase
    .from("documents")
    .select("id, title, updated_at")
    .order("updated_at", { ascending: false });

  if (error) throw error;
  return data;
}

export async function whoAmI() {
  const { data } = await supabase.auth.getSession();
  return data.session?.user?.id ?? null;
}
