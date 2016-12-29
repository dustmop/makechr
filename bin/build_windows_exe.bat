python setup.py py2exe
if exist dist\no_icon.exe del dist\no_icon.exe
rename dist\makechr.exe no_icon.exe
ResourceHacker.exe -open dist/no_icon.exe -save dist/makechr.exe -action addskip -res makechr/res/windows.ico -mask ICONGROUP,MAINICON,
if exist dist\no_icon.exe del dist\no_icon.exe
