# syntax=docker/dockerfile:1
FROM ghcr.io/cirruslabs/android-sdk:34

# Use JDK 21 inside the base image (available in base image)
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Consistent SDK env
ENV ANDROID_HOME=/opt/android-sdk
ENV ANDROID_SDK_ROOT=/opt/android-sdk

# Gradle home inside project to cache in mounted volume
ENV GRADLE_USER_HOME=/workspace/.gradle

# Install required SDK packages (idempotent)
RUN sdkmanager --version \
	&& yes | sdkmanager --licenses >/dev/null || true \
	&& sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0" >/dev/null || true

WORKDIR /workspace

# Copy only gradle wrapper files first for better layer caching
COPY gradle/wrapper/gradle-wrapper.properties gradle/wrapper/gradle-wrapper.properties
COPY gradle/wrapper/gradle-wrapper.jar gradle/wrapper/gradle-wrapper.jar
COPY gradlew gradlew
RUN chmod +x gradlew

# Copy settings and top-level build files
COPY settings.gradle settings.gradle
COPY build.gradle build.gradle
COPY gradle gradle

# Copy app sources
COPY app app

# Default command builds debug APK
CMD ["./gradlew", "--no-daemon", "assembleDebug"]
