$f = Get-Item "D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\CET4-Master-OS.html"
$sizeKB = [math]::Round($f.Length / 1KB, 1)
Write-Host ("File size: " + $f.Length.ToString("N0") + " bytes / " + $sizeKB.ToString() + " KB")
