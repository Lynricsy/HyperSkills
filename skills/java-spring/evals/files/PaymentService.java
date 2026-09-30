package com.example.payments;

import java.util.List;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)   // read paths are served by the replica (see payments-application.yml)
public class PaymentService {

    private final PaymentRepository payments;
    private final LedgerService ledger;
    private final AuditTrail audit;

    public PaymentService(PaymentRepository payments, LedgerService ledger, AuditTrail audit) {
        this.payments = payments;
        this.ledger = ledger;
        this.audit = audit;
    }

    public List<Payment> recentFor(UUID merchantId) {
        return payments.findTop50ByMerchantIdOrderByCreatedAtDesc(merchantId);
    }

    @Transactional
    public Payment capture(CaptureCommand command) {
        Payment payment = payments.save(Payment.pending(command));
        payment.markCaptured();
        audit.record("PAYMENT_CAPTURED", payment.getId());
        ledger.post(payment);   // throws InsufficientReserveException (a RuntimeException) for some merchants
        return payment;
    }
}

@Service
class AuditTrail {

    private final AuditEntryRepository entries;

    AuditTrail(AuditEntryRepository entries) {
        this.entries = entries;
    }

    // Own transaction so the audit trail is never lost, whatever happens to the caller.
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void record(String action, UUID paymentId) {
        entries.save(new AuditEntry(action, paymentId));
    }
}
