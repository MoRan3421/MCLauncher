$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\MCLauncher.lnk")
$Shortcut.TargetPath = "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
$Shortcut.Arguments = '"D:\minecraft cllent\main.py"'
$Shortcut.WorkingDirectory = "D:\minecraft cllent"
$Shortcut.Description = "MCLauncher - Minecraft 全能启动器"
$Shortcut.IconLocation = "%SystemRoot%\System32\imageres.dll, 165"
$Shortcut.Save()
Write-Host "桌面快捷方式已更新!"
