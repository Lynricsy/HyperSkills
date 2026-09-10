# Spring Security in a Spring Boot application

Verified against: Spring Boot 4.1 / Spring Security 7.

## Contents

- [What Security 7 removed](#what-security-7-removed)
- [The filter chain bean](#the-filter-chain-bean)
- [Resource server: validating someone else's JWT](#resource-server-validating-someone-elses-jwt)
- [First-party tokens](#first-party-tokens)
- [Method security](#method-security)
- [Errors from the filter chain](#errors-from-the-filter-chain)
- [CSRF and CORS](#csrf-and-cors)
- [Passwords](#passwords)
- [Old patterns](#old-patterns)

## What Security 7 removed

Spring Boot 4 ships Spring Security 7. These are compile errors, not deprecations:

| Gone | Replacement |
|---|---|
| `WebSecurityConfigurerAdapter` | a `SecurityFilterChain` `@Bean` |
| `authorizeRequests()`, `antMatchers()`, `mvcMatchers()` | `authorizeHttpRequests()`, `requestMatchers()` |
| `.and()` chaining | lambda DSL only |
| `AntPathRequestMatcher`, `MvcRequestMatcher` | `PathPatternRequestMatcher` (what `requestMatchers` uses) |
| `AuthorizationManager#check` | `AuthorizationManager#authorize` |
| `new DaoAuthenticationProvider()` + `setUserDetailsService(…)` | `new DaoAuthenticationProvider(userDetailsService)` |
| `@EnableGlobalMethodSecurity` | `@EnableMethodSecurity` |
| `SecurityJackson2Modules` | `SecurityJacksonModules` (Jackson 3) |
| OpenSAML 4 support | OpenSAML 5 |

Starter names moved into the security namespace as well:
`spring-boot-starter-oauth2-resource-server` → `spring-boot-starter-security-oauth2-resource-server`,
and the same for `-oauth2-client` and `-oauth2-authorization-server`. The authorization server is
now versioned with Spring Security itself, so any `spring-authorization-server.version` property
override must be deleted.

`AccessDecisionManager` and `AccessDecisionVoter` survive only behind an explicit
`spring-security-access` dependency; they have been deprecated since 5.5 and should become
`AuthorizationManager`. If a large security configuration must be migrated gradually, Security 6.5
carries preparation flags for most of the 7.0 behaviour changes — move to 6.5, flip them, then
upgrade.

## The filter chain bean

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
class SecurityConfig {

    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        return http
            .securityMatcher("/api/**")
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
            .exceptionHandling(e -> e
                .authenticationEntryPoint(problemDetailEntryPoint())
                .accessDeniedHandler(problemDetailAccessDeniedHandler()))
            .build();
    }
}
```

- Rules are evaluated in declaration order; `anyRequest()` must be last, and a `permitAll()`
  written after a broader rule never runs.
- Use `securityMatcher` to scope a chain when an application has both an API and a browser UI.
  Multiple `SecurityFilterChain` beans are ordered by `@Order`; the first matching chain wins and
  the others are not consulted.
- A custom filter registered as a `@Bean` is also picked up by the servlet container and runs twice.
  Register a `FilterRegistrationBean<MyFilter>` with `setEnabled(false)` to keep it inside the
  security chain only.

## Resource server: validating someone else's JWT

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://idp.example.com/realms/app
          audiences: https://api.example.com
```

`issuer-uri` makes Spring fetch the provider metadata and validate `iss`; without it a token signed
by any key the JWKS happens to expose is accepted. Add `audiences` so a token minted for a
different API of the same issuer is rejected.

Scopes arrive as authorities prefixed `SCOPE_`, so a scope check is
`hasAuthority("SCOPE_orders:read")` — `hasRole("orders:read")` looks for `ROLE_orders:read` and
always fails. Roles that live in a provider-specific claim need a converter:

```java
@Bean
JwtAuthenticationConverter jwtAuthConverter() {
    var authorities = new JwtGrantedAuthoritiesConverter();
    authorities.setAuthoritiesClaimName("roles");
    authorities.setAuthorityPrefix("ROLE_");
    var converter = new JwtAuthenticationConverter();
    converter.setJwtGrantedAuthoritiesConverter(authorities);
    return converter;
}
```

A resource server is stateless and needs no `UserDetailsService`. Read the caller with
`@AuthenticationPrincipal Jwt jwt` rather than casting `getPrincipal()`.

## First-party tokens

Issue your own tokens only when there is no authorization server to delegate to; the resource
server support can validate self-issued JWTs too. If you do:

- Validate `iss`, `aud`, `exp` and a token-type claim, and accept only access tokens on the bearer
  filter — a refresh token presented as a bearer token must be a 401.
- Catch `ExpiredJwtException` inside the filter. Escaping it turns an expired token into a 500.
- Check the current account state (enabled, locked, expired credentials) on every request; claims
  are a snapshot from issue time.
- Let infrastructure failures stay 5xx. Catching `AuthenticationException` broadly around a user
  lookup turns a database outage into "invalid credentials".
- Rotate refresh tokens on every use and revoke the previous one, keyed by a hashed token family.
- Keep the signing key in the environment. HS256 needs at least a 256-bit key or
  `Keys.hmacShaKeyFor` throws `WeakKeyException`.

## Method security

`@EnableMethodSecurity` enables `@PreAuthorize`/`@PostAuthorize`. It is proxy-based, so the same
self-invocation rule as `@Transactional` applies: an internal `this.method()` call is unchecked.

```java
@PreAuthorize("hasRole('ADMIN') or #userId == authentication.principal.id")
UserProfile getProfile(UUID userId) { … }

@PreAuthorize("@orderSecurity.isOwner(#orderId, authentication)")
Order findById(UUID orderId) { … }
```

Put the annotations on the service, not the controller: the controller is one of several entry
points, the service is the actual boundary. `@PostAuthorize` loads the object before deciding, so
never use it where loading itself is the sensitive operation.

## Errors from the filter chain

`@RestControllerAdvice` cannot see exceptions thrown before the dispatcher servlet, which is where
all authentication and authorization failures happen. Without an `AuthenticationEntryPoint` and an
`AccessDeniedHandler`, API clients get an empty 401/403 body or a redirect to a login page. Emit
the same Problem Details shape as the rest of the API from both.

Missing or invalid credentials on a protected route is 401; an authenticated caller lacking the
authority is 403. An invalid token presented to a public route is still a 401 — the credential was
supplied and it was bad.

## CSRF and CORS

Disable CSRF only for an API authenticated purely by an `Authorization` header. As soon as a
browser sends a cookie automatically, CSRF protection is load-bearing; a cookie-based SPA uses
`CookieCsrfTokenRepository.withHttpOnlyFalse()`.

Configure CORS through `http.cors(…)` and a `CorsConfigurationSource` bean so it is part of the
security chain. `@CrossOrigin` on a controller runs after the security filters, so preflight
requests are rejected before they reach it.

## Passwords

`PasswordEncoderFactories.createDelegatingPasswordEncoder()` stores an `{id}` prefix and lets the
algorithm be upgraded later. A bare `BCryptPasswordEncoder` cannot be migrated without resetting
every password. Use strength 12 for bcrypt in production.

## Old patterns

<details>
<summary>Configuration styles that no longer compile</summary>

```java
// Security 5: adapter + chained matchers
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    protected void configure(HttpSecurity http) throws Exception {
        http.csrf().disable()
            .authorizeRequests().antMatchers("/admin/**").hasRole("ADMIN")
            .and().httpBasic();
    }
}
```

Both the adapter and the chained `and()` DSL were removed. `authorizeRequests()` and
`antMatchers()` went with them. There is no compatibility flag; rewrite as a `SecurityFilterChain`
bean with the lambda DSL.
</details>

<!-- sources: rrezart-spring-boot, adityamparikh-boot4, spring-docs, spring-boot-wiki -->
