package com.example.shop;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.example.shop.order.Order;
import com.example.shop.order.OrderRepository;
import com.example.shop.order.OrderService;
import com.example.shop.pricing.PricingClient;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ShopApplicationTests {

    @Autowired
    MockMvc mockMvc;

    @Autowired
    TestRestTemplate restTemplate;

    @Autowired
    OrderRepository orderRepository;

    @Autowired
    OrderService orderService;

    @MockBean
    PricingClient pricingClient;

    @Test
    void listOrdersReturnsOk() throws Exception {
        mockMvc.perform(get("/api/v1/orders")).andExpect(status().isOk());
    }

    @Test
    void createOrderRequiresAuthentication() throws Exception {
        mockMvc.perform(post("/api/v1/orders").content("{}")).andExpect(status().isUnauthorized());
    }

    @Test
    void findByStatusFiltersRows() {
        orderRepository.save(new Order());
        List<Order> found = orderRepository.findByStatus(null);
        assertEquals(1, found.size());
    }

    @Test
    void pricingIsStubbed() {
        when(pricingClient.quote(any())).thenReturn(1000);
        assertEquals(1000, orderService.rename(1L, "x").getTotalCents());
    }
}
