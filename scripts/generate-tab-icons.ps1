Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IconDir = Join-Path $ProjectRoot 'assets\icons'
New-Item -ItemType Directory -Force -Path $IconDir | Out-Null
foreach ($name in @('home','map','publish','messages','profile')) {
  foreach ($selected in @($false,$true)) {
    $bitmap = [System.Drawing.Bitmap]::new(81,81)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::Transparent)
    $color = if ($selected) { '#EA735B' } else { '#7C8492' }
    $pen = [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml($color),5)
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    switch ($name) {
      'home' {
        $graphics.DrawLines($pen,[System.Drawing.Point[]]@([System.Drawing.Point]::new(13,36),[System.Drawing.Point]::new(40,13),[System.Drawing.Point]::new(68,36)))
        $graphics.DrawLines($pen,[System.Drawing.Point[]]@([System.Drawing.Point]::new(21,33),[System.Drawing.Point]::new(21,66),[System.Drawing.Point]::new(59,66),[System.Drawing.Point]::new(59,33)))
        $graphics.DrawLines($pen,[System.Drawing.Point[]]@([System.Drawing.Point]::new(33,66),[System.Drawing.Point]::new(33,47),[System.Drawing.Point]::new(47,47),[System.Drawing.Point]::new(47,66)))
      }
      'map' {
        $graphics.DrawArc($pen,19,11,43,43,155,230)
        $graphics.DrawLine($pen,21,42,40,69)
        $graphics.DrawLine($pen,60,42,40,69)
        $graphics.DrawEllipse($pen,33,24,15,15)
      }
      'publish' {
        $graphics.DrawEllipse($pen,12,12,57,57)
        $graphics.DrawLine($pen,26,40,55,40)
        $graphics.DrawLine($pen,40,26,40,55)
      }
      'messages' {
        $graphics.DrawArc($pen,12,14,56,46,130,300)
        $graphics.DrawLines($pen,[System.Drawing.Point[]]@([System.Drawing.Point]::new(21,49),[System.Drawing.Point]::new(17,67),[System.Drawing.Point]::new(36,58)))
        $graphics.DrawLine($pen,27,31,53,31)
        $graphics.DrawLine($pen,27,42,45,42)
      }
      'profile' {
        $graphics.DrawEllipse($pen,28,11,25,25)
        $graphics.DrawArc($pen,15,44,51,46,180,180)
        $graphics.DrawLine($pen,15,67,66,67)
      }
    }
    $suffix = if ($selected) { '-active' } else { '' }
    $bitmap.Save((Join-Path $IconDir ($name + $suffix + '.png')),[System.Drawing.Imaging.ImageFormat]::Png)
    $pen.Dispose()
    $graphics.Dispose()
    $bitmap.Dispose()
  }
}
Write-Output 'Generated 10 original tab icons (81 x 81 PNG).'
