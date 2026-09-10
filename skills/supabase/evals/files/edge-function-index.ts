// supabase/functions/send-invoice/index.ts
// Deployed with: supabase functions deploy send-invoice
// The browser call from our React app fails before the function ever runs.
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import Stripe from 'https://esm.sh/stripe@14'

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') ?? '')

const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
)

Deno.serve(async (req) => {
  const { invoiceId } = await req.json()

  const { data: invoice } = await supabase
    .from('invoices')
    .select('*, customer:customers(*)')
    .eq('id', invoiceId)
    .single()

  const event = stripe.webhooks.constructEvent(
    await req.text(),
    req.headers.get('stripe-signature') ?? '',
    Deno.env.get('STRIPE_WEBHOOK_SECRET')!
  )

  await stripe.invoices.sendInvoice(invoice.stripe_invoice_id)

  return new Response(JSON.stringify({ sent: true, event: event.type }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
