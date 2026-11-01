package com.example.accounts;

import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Service
class AccountService {
    private final AccountRepository accounts;

    AccountService(AccountRepository accounts) { this.accounts = accounts; }

    @PreAuthorize("hasRole('admin')")
    @Transactional
    public void close(UUID id) {
        accounts.findById(id).orElseThrow(() -> new AccountNotFoundException(id)).close();
    }
}

@RestControllerAdvice
class ApiErrorAdvice {

    @ExceptionHandler(AccountNotFoundException.class)
    ProblemDetail notFound(AccountNotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "Account not found");
    }

    @ExceptionHandler(Exception.class)
    ProblemDetail unexpected(Exception ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, "Unexpected error");
    }
}
