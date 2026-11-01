package com.example.accounts;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Bean;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.assertj.MockMvcTester;
import org.testcontainers.containers.PostgreSQLContainer;

@WebMvcTest(AccountController.class)
class AccountControllerTest {
    @Autowired MockMvcTester mvc;
    @MockitoBean AccountService accountService;

    @Test
    @WithMockUser(roles = "admin")
    void rejectsAccountWithoutOwner() {
        // fails: expected 400 but was 403
        assertThat(mvc.post().uri("/api/accounts")
                .contentType(MediaType.APPLICATION_JSON).content("{\"currency\":\"EUR\"}"))
            .hasStatus(HttpStatus.BAD_REQUEST);
    }
}

// shared by the @SpringBootTest suites
@TestConfiguration(proxyBeanMethods = false)
class TestcontainersConfig {
    @Bean @ServiceConnection
    PostgreSQLContainer<?> postgres() {
        return new PostgreSQLContainer<>("postgres:17-alpine");
    }
}
