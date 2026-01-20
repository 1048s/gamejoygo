[app]
# (str) Title of your application
title = KaneDefense

# (str) Package name
package.name = kanedefense

# (str) Package domain (needed for android packaging)
package.domain = org.user.kane

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ttf,ico

# (list) List of inclusions using pattern matching
source.include_patterns = image/*,sound/*

# (str) Application versioning
version = 0.1

# (list) Application requirements
# 파이썬 표준 라이브러리 외의 필수 라이브러리를 명시합니다.
requirements = python3,pygame,Pillow

# (str) Supported orientations
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE

# (int) Android API to use
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK build-tools version to use (이 줄을 추가하거나 수정하세요)
android.sdk_buildtools = 33.0.0

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True