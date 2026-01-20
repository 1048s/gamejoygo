[app]
title = KaneDefense
package.name = kanedefense
package.domain = org.user.kane
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ttf,ico
source.include_patterns = image/*,sound/*
version = 1.0.0
requirements = python3,pygame,Pillow

orientation = landscape
fullscreen = 1
android.accept_sdk_license = True
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk_buildtools = 33.0.0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE
android.private_storage = True