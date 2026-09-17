[app]
title = Milk Diary Pro
package.name = milkdiarypro
package.domain = org.anshul

source.dir = .
source.include_exts = py,png,jpg,jpeg,json,db,ttf
source.exclude_dirs = tests,__pycache__

version = 1.0

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,plyer,fpdf2,fonttools,defusedxml

orientation = portrait
fullscreen = 1

android.permissions = INTERNET,POST_NOTIFICATIONS

android.archs = arm64-v8a
android.api = 34
android.minapi = 21
android.sdk = 34

p4a.fork = kivy
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
