package com.example.shop.order;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderService {

    private final OrderRepository orderRepository;
    private final AuditRepository auditRepository;
    private final EmailSender emailSender;

    public OrderService(OrderRepository orderRepository,
                        AuditRepository auditRepository,
                        EmailSender emailSender) {
        this.orderRepository = orderRepository;
        this.auditRepository = auditRepository;
        this.emailSender = emailSender;
    }

    @Transactional
    public void submitBatch(List<Long> orderIds) {
        for (Long id : orderIds) {
            this.submitOne(id);
        }
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void submitOne(Long id) {
        Order order = orderRepository.findById(id).orElseThrow();
        order.setStatus(OrderStatus.SUBMITTED);
        order.setSubmittedAt(Instant.now());
        orderRepository.save(order);
        emailSender.sendConfirmation(order.getCustomerEmail(), order.getId());
        auditRepository.save(new AuditRow("ORDER_SUBMITTED", order.getId()));
    }

    @Transactional
    public List<OrderSummaryDto> listOpenOrders() {
        List<Order> orders = orderRepository.findAll();
        List<OrderSummaryDto> out = new ArrayList<>();
        for (Order order : orders) {
            if (order.getStatus() != OrderStatus.CLOSED) {
                int lineCount = order.getItems().size();
                String customer = order.getCustomer().getDisplayName();
                out.add(new OrderSummaryDto(order.getId(), customer, lineCount));
            }
        }
        return out;
    }

    @Transactional
    private void recalculate(Order order) {
        order.setTotalCents(order.getItems().stream().mapToInt(OrderItem::getSubtotalCents).sum());
        orderRepository.save(order);
    }

    public Order rename(Long id, String label) {
        Order order = orderRepository.findById(id).orElseThrow();
        order.setLabel(label);
        return orderRepository.save(order);
    }
}
