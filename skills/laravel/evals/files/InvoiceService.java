package com.example.billing;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class InvoiceService {

    private final InvoiceRepository invoices;
    private final LedgerRepository ledger;

    public InvoiceService(InvoiceRepository invoices, LedgerRepository ledger) {
        this.invoices = invoices;
        this.ledger = ledger;
    }

    public void closeMonth(long accountId) {
        for (Invoice invoice : invoices.findOpenByAccount(accountId)) {
            // Expected each invoice to commit or roll back on its own.
            this.settle(invoice);
        }
    }

    @Transactional
    public void settle(Invoice invoice) {
        invoice.setStatus(InvoiceStatus.SETTLED);
        invoices.save(invoice);
        ledger.post(invoice.getAccountId(), invoice.getTotal());
    }
}
