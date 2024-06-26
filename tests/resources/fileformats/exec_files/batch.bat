@echo off
echo "remarkable how many folk don't know about the @ for batch files"
echo %DATE%
wmic cpu get name
systeminfo | findstr /c:"Total Physical Memory"


