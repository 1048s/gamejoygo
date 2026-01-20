[app]
title = KaneDefense
package.name = kanedefense
package.domain = org.user.kane
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ttf,ico
# 폴더 전체를 포함하도록 패턴 수정
source.include_patterns = image/*,sound/*,assets/*
version = 1.0.0

# [필수] Pygame 앱을 위한 requirements (hostpython3 추가 권장)
requirements = python3,pygame,Pillow

orientation = landscape
fullscreen = 1

# [안드로이드 설정]
android.accept_sdk_license = True
# 구글 플레이 스토어 최신 기준인 34로 상향 권장
android.api = 34
android.minapi = 21
android.ndk = 25b
android.build_tools_version = 34.0.0

# [중요] 빌드 속도 및 용량 최적화 (64비트 전용)
# armeabi-v7a를 제외하면 빌드 시간이 절반으로 줄어듭니다.
android.archs = arm64-v8a

# [권한] 안드로이드 11 이상 대응 (저장소 권한 세분화)
android.permissions = INTERNET

# [기타]
android.private_storage = True
android.entrypoint = main.py

[buildozer]
log_level = 2
warn_on_root = 1