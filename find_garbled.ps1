$path = "D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\CET4-Master-OS.html"
$content = Get-Content $path -Encoding UTF8
$raw = Get-Content $path -Encoding UTF8 -Raw

# Find the EXAM_DATA closing </script> position
$dataScriptEnd = $raw.IndexOf('</script>', $raw.IndexOf('const EXAM_DATA'))
Write-Host ("EXAM_DATA script ends at byte position: " + $dataScriptEnd)

# Find the line number where EXAM_DATA ends
$bytesSoFar = 0
$dataEndLine = 0
for ($i = 0; $i -lt $content.Count; $i++) {
    $bytesSoFar += $content[$i].Length + 2  # +2 for CR/LF
    if ($bytesSoFar -ge $dataScriptEnd) {
        $dataEndLine = $i + 1
        break
    }
}
Write-Host ("EXAM_DATA ends at approximately line: " + $dataEndLine)

$found = 0
$repChar = [char]0xFFFD

for ($i = $dataEndLine; $i -lt $content.Count -and $found -lt 60; $i++) {
    $line = $content[$i]
    if ($line -match $repChar) {
        Write-Host ("Line $($i+1): " + $line.Substring(0, [Math]::Min(150, $line.Length)))
        $found++
    }
}
Write-Host ("`nFound $found garbled lines after EXAM_DATA section")
