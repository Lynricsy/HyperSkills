FROM eclipse-temurin:25-jdk AS build
WORKDIR /app
COPY . .
RUN ./mvnw -q -DskipTests package \
 && java -Djarmode=layertools -jar target/payments-service.jar extract --destination target/layers

FROM eclipse-temurin:25-jre
WORKDIR /app
COPY --from=build /app/target/layers/dependencies/ ./
COPY --from=build /app/target/layers/spring-boot-loader/ ./
COPY --from=build /app/target/layers/snapshot-dependencies/ ./
COPY --from=build /app/target/layers/application/ ./
ENV JAVA_TOOL_OPTIONS="-XX:+UseZGC -XX:-ZGenerational -XX:MaxRAMPercentage=75"
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
