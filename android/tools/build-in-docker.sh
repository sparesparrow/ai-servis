#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=ai-servis-android-build:latest
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
ANDROID_DIR="$PROJECT_ROOT"
SDK_VOL=ai_servis_android_sdk

# Build image (use android/ as build context)
cd "$ANDROID_DIR"
docker build -t "$IMAGE_NAME" .

# Bootstrap SDK into the named volume: accept licenses and install packages into /sdk
docker run --rm \
  -v $SDK_VOL:/sdk \
  -e ANDROID_HOME=/sdk \
  -e ANDROID_SDK_ROOT=/sdk \
  "$IMAGE_NAME" bash -lc "set -e; \
    sdkmanager --version >/dev/null; \
    yes | sdkmanager --sdk_root=/sdk --licenses >/dev/null; \
    sdkmanager --sdk_root=/sdk 'platform-tools' 'platforms;android-34' 'build-tools;34.0.0' >/dev/null"

# Run build with mounted project and persistent SDK + Gradle caches
exec docker run --rm --init \
  -u $(id -u):$(id -g) \
  -v "$ANDROID_DIR":/workspace \
  -v $SDK_VOL:/opt/android-sdk \
  -e ANDROID_HOME=/opt/android-sdk \
  -e ANDROID_SDK_ROOT=/opt/android-sdk \
  -e GRADLE_USER_HOME=/workspace/.gradle \
  -w /workspace \
  "$IMAGE_NAME" ./gradlew --no-daemon assembleDebug
