package com.example.payments;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.UUID;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Component
class PaymentExpiryJob {

    private final PaymentRepository payments;
    private final ApplicationEventPublisher events;

    PaymentExpiryJob(PaymentRepository payments, ApplicationEventPublisher events) {
        this.payments = payments;
        this.events = events;
    }

    @Scheduled(cron = "0 30 2 * * *")
    public void expireStale() {
        Instant cutoff = Instant.now().minus(7, ChronoUnit.DAYS);
        List<UUID> ids = payments.findPendingIdsCreatedBefore(cutoff);
        payments.markExpired(ids);
        events.publishEvent(new PaymentsExpired(ids));
    }
}

record PaymentsExpired(List<UUID> paymentIds) {}

@Component
class MerchantNotifier {

    private final MerchantMailer mailer;

    MerchantNotifier(MerchantMailer mailer) {
        this.mailer = mailer;
    }

    // Only mail merchants once the expiry is really committed.
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onExpired(PaymentsExpired event) {
        mailer.sendExpiryDigest(event.paymentIds());
    }
}

interface PaymentRepository extends org.springframework.data.jpa.repository.JpaRepository<Payment, UUID> {

    List<Payment> findTop50ByMerchantIdOrderByCreatedAtDesc(UUID merchantId);

    @Query("select p.id from Payment p where p.status = 'PENDING' and p.createdAt < :cutoff")
    List<UUID> findPendingIdsCreatedBefore(Instant cutoff);

    @Transactional
    @Modifying(clearAutomatically = true)
    @Query("update Payment p set p.status = 'EXPIRED' where p.id in :ids")
    int markExpired(List<UUID> ids);
}
