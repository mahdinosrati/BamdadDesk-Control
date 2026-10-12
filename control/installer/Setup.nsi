Unicode true
Name "BamdadDesk Organization Setup"
OutFile "BamdadDesk-Setup.exe"
RequestExecutionLevel admin
SetCompressor lzma
ShowInstDetails show
Page instfiles
Section
  InitPluginsDir
  SetOutPath "$PLUGINSDIR"
  File "BamdadDesk.exe"
  File "profile.json"
  File "Setup.ps1"
  DetailPrint "Installing BamdadDesk and staging automatic organization enrollment..."
  nsExec::ExecToLog '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$PLUGINSDIR\Setup.ps1"'
  Pop $0
  StrCmp $0 "0" done
  MessageBox MB_ICONSTOP "Setup failed. Review the details above. Existing enrollment is preserved."
  SetErrorLevel 1
  Abort
done:
  DetailPrint "Installation completed. The service will register when the HTTPS panel is reachable."
SectionEnd
