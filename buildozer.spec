[app]
title = Milk Diary Pro
package.name = milkdiarypro
package.domain = org.anshul

source.dir = .
source.include_exts = py,png,jpg,jpeg,json,db

version = 1.0

requirements = python3,kivy,plyer,reportlab

orientation = portrait
fullscreen = 1

android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1

android.api = 34
android.minapi = 21
android.sdk = 34
