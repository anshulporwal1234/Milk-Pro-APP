[app]
title = Milk Diary Pro
package.name = milkdiarypro
package.domain = org.anshul

source.dir = .

source.include_exts = py,png,jpg,jpeg,json,db,ttf

version = 1.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,reportlab

orientation = portrait
fullscreen = 1

android.permissions = INTERNET
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
