[app]
title = Milk Diary Pro
package.name = milkdiarypro
package.domain = org.anshul
source.dir = .
source.include_exts = py,png,jpg,kv,db,json
version = 1.1

# Strict requirements bina kisi external mismatch ke
requirements = python3,kivy==2.3.0,kivymd==1.2.0,reportlab,openpyxl,plyer

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
android.allow_backup = True
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1