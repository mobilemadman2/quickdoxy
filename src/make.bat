if not exist frontendUI.py python make_qt.py
python make_docu.py False
python make_qt.py
pyi-makespec --onefile --windowed __main__.py
python make_zip.py
pyinstaller __main__.spec
rmdir /s /q ..\dst
mkdir ..\dst
copy dist\__main__.exe ..\dst\quickdoxy.exe
copy quickdoxy.zip ..\dst\quickdoxy.pyw
rmdir /s /q dist
rmdir /s /q build
rmdir /s /q __pycache__
del /f __main__.spec
del /f quickdoxy.zip