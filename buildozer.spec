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

android.archs = arm64-v8a
android.api = 34
android.minapi = 21
android.sdk = 34

p4a.fork = kivy
p4a.branch = develop
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
