Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = 'Stop'

$Root = if ($MyInvocation.MyCommand.Path) {
  Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
  (Get-Location).Path
}
$Output = Join-Path $Root 'prototypes'
New-Item -ItemType Directory -Force -Path $Output | Out-Null

$W = 1179
$H = 2556
$ScreenW = 843
$ScreenH = 2154
$ScreenX = [int](($W - $ScreenW) / 2)
$ScreenY = 168
$FontFamily = 'Microsoft YaHei'

function Hex([string]$value) {
  return [System.Drawing.ColorTranslator]::FromHtml($value)
}

function New-Font([float]$size, [string]$style = 'Regular') {
  $fontStyle = [System.Enum]::Parse([System.Drawing.FontStyle], $style)
  return [System.Drawing.Font]::new($FontFamily, $size, $fontStyle, [System.Drawing.GraphicsUnit]::Pixel)
}

function New-PathRoundRect([float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
  $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
  $d = $r * 2
  $path.AddArc($x, $y, $d, $d, 180, 90)
  $path.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
  $path.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
  $path.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
  $path.CloseFigure()
  return $path
}

function Fill-RoundRect($g, [float]$x, [float]$y, [float]$w, [float]$h, [float]$r, [string]$fill) {
  $brush = [System.Drawing.SolidBrush]::new((Hex $fill))
  $path = New-PathRoundRect $x $y $w $h $r
  $g.FillPath($brush, $path)
  $path.Dispose()
  $brush.Dispose()
}

function Stroke-RoundRect($g, [float]$x, [float]$y, [float]$w, [float]$h, [float]$r, [string]$stroke, [float]$width = 2) {
  $pen = [System.Drawing.Pen]::new((Hex $stroke), $width)
  $path = New-PathRoundRect $x $y $w $h $r
  $g.DrawPath($pen, $path)
  $path.Dispose()
  $pen.Dispose()
}

function Fill-Rect($g, [float]$x, [float]$y, [float]$w, [float]$h, [string]$fill) {
  $brush = [System.Drawing.SolidBrush]::new((Hex $fill))
  $g.FillRectangle($brush, $x, $y, $w, $h)
  $brush.Dispose()
}

function Draw-Line($g, [float]$x1, [float]$y1, [float]$x2, [float]$y2, [string]$stroke, [float]$width = 2) {
  $pen = [System.Drawing.Pen]::new((Hex $stroke), $width)
  $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
  $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
  $g.DrawLine($pen, $x1, $y1, $x2, $y2)
  $pen.Dispose()
}

function Draw-Ellipse($g, [float]$x, [float]$y, [float]$w, [float]$h, [string]$fill, [string]$stroke = '', [float]$width = 2) {
  if ($fill) {
    $brush = [System.Drawing.SolidBrush]::new((Hex $fill))
    $g.FillEllipse($brush, $x, $y, $w, $h)
    $brush.Dispose()
  }
  if ($stroke) {
    $pen = [System.Drawing.Pen]::new((Hex $stroke), $width)
    $g.DrawEllipse($pen, $x, $y, $w, $h)
    $pen.Dispose()
  }
}

function Wrap-Text($g, [string]$text, [System.Drawing.Font]$font, [float]$maxWidth) {
  $lines = New-Object System.Collections.Generic.List[string]
  foreach ($paragraph in ($text -split "`n")) {
    $line = ''
    foreach ($ch in $paragraph.ToCharArray()) {
      $candidate = $line + $ch
      $measure = $g.MeasureString($candidate, $font)
      if ($measure.Width -gt $maxWidth -and $line.Length -gt 0) {
        $lines.Add($line)
        $line = [string]$ch
      } else {
        $line = $candidate
      }
    }
    if ($line.Length -gt 0) {
      $lines.Add($line)
    } elseif ($paragraph.Length -eq 0) {
      $lines.Add('')
    }
  }
  return $lines
}

function Draw-Text(
  $g,
  [string]$text,
  [float]$x,
  [float]$y,
  [float]$size,
  [string]$color,
  [string]$style = 'Regular',
  [float]$maxWidth = 0,
  [float]$lineHeight = 1.42,
  [string]$align = 'Left'
) {
  $font = New-Font $size $style
  $brush = [System.Drawing.SolidBrush]::new((Hex $color))
  $format = [System.Drawing.StringFormat]::new()
  $format.Alignment = switch ($align) {
    'Center' { [System.Drawing.StringAlignment]::Center; break }
    'Right' { [System.Drawing.StringAlignment]::Far; break }
    default { [System.Drawing.StringAlignment]::Near; break }
  }
  $format.LineAlignment = [System.Drawing.StringAlignment]::Near
  if ($maxWidth -le 0) {
    $g.DrawString($text, $font, $brush, $x, $y, $format)
  } else {
    $lines = Wrap-Text $g $text $font $maxWidth
    $lineY = $y
    foreach ($line in $lines) {
      $g.DrawString($line, $font, $brush, [System.Drawing.RectangleF]::new($x, $lineY, $maxWidth, $size * $lineHeight), $format)
      $lineY += $size * $lineHeight
    }
  }
  $format.Dispose()
  $brush.Dispose()
  $font.Dispose()
}

function Draw-CenteredText($g, [string]$text, [float]$centerX, [float]$y, [float]$size, [string]$color, [string]$style = 'Regular', [float]$maxWidth = 0) {
  if ($maxWidth -gt 0) {
    Draw-Text $g $text ($centerX - $maxWidth / 2) $y $size $color $style $maxWidth 1.42 'Center'
  } else {
    $font = New-Font $size $style
    $measure = $g.MeasureString($text, $font)
    $font.Dispose()
    Draw-Text $g $text ($centerX - $measure.Width / 2) $y $size $color $style 0 1.42 'Center'
  }
}

function Draw-StatusBar($g, [float]$w) {
  Draw-Text $g '9:41' 34 22 24 '#172033' 'Bold'
  Draw-Line $g ($w - 104) 38 ($w - 88) 38 '#172033' 3
  Draw-Line $g ($w - 78) 38 ($w - 62) 38 '#172033' 3
  Fill-RoundRect $g ($w - 51) 27 27 16 5 '#172033'
  Fill-RoundRect $g ($w - 47) 30 21 10 3 '#FFFFFF'
  Draw-Line $g ($w - 20) 32 ($w - 16) 32 '#172033' 3
}

function Draw-Back($g, [float]$x = 34, [float]$y = 111, [string]$color = '#172033') {
  Draw-Line $g ($x + 18) $y $x $y $color 3
  Draw-Line $g ($x + 18) ($y - 14) $x $y $color 3
  Draw-Line $g ($x + 18) ($y + 14) $x $y $color 3
}

function Draw-TopBar($g, [float]$w, [string]$title, [string]$rightText = '') {
  Draw-StatusBar $g $w
  Draw-Back $g
  Draw-CenteredText $g $title ($w / 2) 91 30 '#172033' 'Bold'
  if ($rightText) {
    Draw-Text $g $rightText ($w - 130) 95 23 '#768396' 'Bold' 96 1.2 'Right'
  }
}

function Draw-HomeIcon($g, [float]$cx, [float]$cy, [string]$color) {
  $pen = [System.Drawing.Pen]::new((Hex $color), 3)
  $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
  $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
  $points = [System.Drawing.PointF[]]@(
    [System.Drawing.PointF]::new($cx - 15, $cy - 2),
    [System.Drawing.PointF]::new($cx, $cy - 15),
    [System.Drawing.PointF]::new($cx + 15, $cy - 2),
    [System.Drawing.PointF]::new($cx + 15, $cy + 16),
    [System.Drawing.PointF]::new($cx - 15, $cy + 16),
    [System.Drawing.PointF]::new($cx - 15, $cy - 2)
  )
  $g.DrawLines($pen, $points)
  $g.DrawLine($pen, $cx, $cy + 16, $cx, $cy + 4)
  $pen.Dispose()
}

function Draw-PinIcon($g, [float]$cx, [float]$cy, [string]$color) {
  $pen = [System.Drawing.Pen]::new((Hex $color), 3)
  $g.DrawEllipse($pen, $cx - 13, $cy - 17, 26, 32)
  $g.DrawEllipse($pen, $cx - 4, $cy - 8, 8, 8)
  $pen.Dispose()
}

function Draw-PlusIcon($g, [float]$cx, [float]$cy, [string]$color) {
  Draw-Ellipse $g ($cx - 23) ($cy - 23) 46 46 $color
  Draw-Line $g ($cx - 11) $cy ($cx + 11) $cy '#FFFFFF' 3
  Draw-Line $g $cx ($cy - 11) $cx ($cy + 11) '#FFFFFF' 3
}

function Draw-MessageIcon($g, [float]$cx, [float]$cy, [string]$color) {
  Stroke-RoundRect $g ($cx - 17) ($cy - 14) 34 28 9 $color 3
  Draw-Line $g ($cx - 5) ($cy + 14) ($cx - 10) ($cy + 23) $color 3
  Draw-Line $g ($cx - 7) $cy ($cx + 7) $cy $color 3
}

function Draw-UserIcon($g, [float]$cx, [float]$cy, [string]$color) {
  Draw-Ellipse $g ($cx - 8) ($cy - 18) 16 16 '' $color 3
  $pen = [System.Drawing.Pen]::new((Hex $color), 3)
  $g.DrawArc($pen, $cx - 18, $cy + 1, 36, 25, 180, 180)
  $pen.Dispose()
}

function Draw-TabBar($g, [float]$w, [float]$h, [int]$selected) {
  $top = $h - 136
  Fill-Rect $g 0 $top $w 136 '#FFFFFF'
  Draw-Line $g 0 $top $w $top '#E8ECEE' 2
  $items = @('首页', '地图', '发布', '消息', '我的')
  $centers = @(84, 253, 421, 590, 759)
  for ($i = 0; $i -lt 5; $i++) {
    $color = if ($i -eq $selected) { '#EE735A' } else { '#96A0AC' }
    switch ($i) {
      0 { Draw-HomeIcon $g $centers[$i] ($top + 40) $color }
      1 { Draw-PinIcon $g $centers[$i] ($top + 40) $color }
      2 { Draw-PlusIcon $g $centers[$i] ($top + 40) '#EE735A' }
      3 { Draw-MessageIcon $g $centers[$i] ($top + 40) $color }
      4 { Draw-UserIcon $g $centers[$i] ($top + 40) $color }
    }
    Draw-CenteredText $g $items[$i] $centers[$i] ($top + 74) 19 $color 'Bold'
  }
  Draw-Ellipse $g 405 ($top + 12) 32 32 '#FFD84D'
  Draw-Text $g 'AI' 412 ($top + 18) 12 '#172033' 'Bold'
}

function Draw-Logo($g, [float]$x, [float]$y, [float]$scale = 1) {
  Draw-Ellipse $g $x ($y + 10 * $scale) (30 * $scale) (30 * $scale) '#FFD84D' '#172033' (3 * $scale)
  Draw-Ellipse $g ($x + 15 * $scale) $y (30 * $scale) (30 * $scale) '#FF8D71' '#172033' (3 * $scale)
  Draw-Ellipse $g ($x + 29 * $scale) ($y + 15 * $scale) (30 * $scale) (30 * $scale) '#93D9CA' '#172033' (3 * $scale)
}

function Draw-Avatar($g, [float]$x, [float]$y, [float]$size, [string]$skin, [string]$shirt, [string]$hair = '#172033') {
  Draw-Ellipse $g $x $y $size $size $shirt '#FFFFFF' 3
  Draw-Ellipse $g ($x + $size * .24) ($y + $size * .18) ($size * .52) ($size * .52) $skin
  Fill-RoundRect $g ($x + $size * .18) ($y + $size * .08) ($size * .64) ($size * .30) ($size * .14) $hair
  Draw-Ellipse $g ($x + $size * .40) ($y + $size * .49) ($size * .07) ($size * .07) '#172033'
  Draw-Ellipse $g ($x + $size * .57) ($y + $size * .49) ($size * .07) ($size * .07) '#172033'
}

function Draw-Chip($g, [string]$label, [float]$x, [float]$y, [float]$w, [string]$fill = '#F1F3F1', [string]$textColor = '#5B6878', [string]$stroke = '') {
  Fill-RoundRect $g $x $y $w 44 22 $fill
  if ($stroke) { Stroke-RoundRect $g $x $y $w 44 22 $stroke 2 }
  Draw-CenteredText $g $label ($x + $w / 2) ($y + 10) 19 $textColor 'Bold'
}

function Draw-SearchBar($g, [float]$x, [float]$y, [float]$w, [string]$placeholder) {
  Fill-RoundRect $g $x $y $w 64 32 '#FFFFFF'
  Draw-Ellipse $g ($x + 24) ($y + 21) 18 18 '' '#99A4AE' 3
  Draw-Line $g ($x + 38) ($y + 37) ($x + 47) ($y + 46) '#99A4AE' 3
  Draw-Text $g $placeholder ($x + 66) ($y + 19) 22 '#94A0AC'
}

function Draw-MapBase($g, [float]$x, [float]$y, [float]$w, [float]$h, [float]$scale = 1) {
  Fill-Rect $g $x $y $w $h '#EEF2ED'
  $river = [System.Drawing.PointF[]]@(
    [System.Drawing.PointF]::new($x + $w * .54, $y - 10),
    [System.Drawing.PointF]::new($x + $w * .67, $y + $h * .08),
    [System.Drawing.PointF]::new($x + $w * .57, $y + $h * .24),
    [System.Drawing.PointF]::new($x + $w * .72, $y + $h * .42),
    [System.Drawing.PointF]::new($x + $w * .63, $y + $h * .62),
    [System.Drawing.PointF]::new($x + $w * .76, $y + $h + 20),
    [System.Drawing.PointF]::new($x + $w * .98, $y + $h + 20),
    [System.Drawing.PointF]::new($x + $w * .90, $y + $h * .58),
    [System.Drawing.PointF]::new($x + $w * .82, $y + $h * .35),
    [System.Drawing.PointF]::new($x + $w * .89, $y + $h * .06),
    [System.Drawing.PointF]::new($x + $w * .78, $y - 10)
  )
  $brush = [System.Drawing.SolidBrush]::new((Hex '#BFE2E1'))
  $g.FillPolygon($brush, $river)
  $brush.Dispose()
  for ($i = 0; $i -lt 10; $i++) {
    $x1 = $x - 30 + $i * 115
    $y1 = $y + 40
    $points = [System.Drawing.PointF[]]@(
      [System.Drawing.PointF]::new($x1, $y1 + ($i % 3) * 55),
      [System.Drawing.PointF]::new($x1 + 100, $y1 + 90 + (($i + 1) % 3) * 42),
      [System.Drawing.PointF]::new($x1 + 220, $y1 + 36 + (($i + 2) % 3) * 58),
      [System.Drawing.PointF]::new($x1 + 360, $y1 + 145 + ($i % 2) * 60)
    )
    $pen = [System.Drawing.Pen]::new((Hex '#D1D9D2'), 6 * $scale)
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $g.DrawCurve($pen, $points)
    $pen.Dispose()
  }
  for ($i = 0; $i -lt 8; $i++) {
    $x1 = $x + 40 + $i * 112
    Draw-Line $g $x1 $y ($x1 + 78) ($y + $h) '#DDE4DE' (3 * $scale)
  }
  for ($i = 0; $i -lt 9; $i++) {
    $px = $x + 26 + (($i * 137) % [math]::Max(1, [int]($w - 48)))
    $py = $y + 110 + (($i * 89) % [math]::Max(1, [int]($h - 180)))
    Draw-Ellipse $g $px $py 8 8 '#CFD8D0'
  }
  Draw-Text $g '岳麓山' ($x + 62) ($y + 188) 22 '#82968D' 'Bold'
  Draw-Text $g '橘子洲' ($x + $w * .49) ($y + $h * .30) 22 '#6E9D9A' 'Bold'
  Draw-Text $g '五一广场' ($x + $w * .26) ($y + $h * .72) 22 '#82968D' 'Bold'
  Draw-Text $g '湘江' ($x + $w * .76) ($y + $h * .70) 20 '#72A9A7' 'Regular'
}

function Draw-MapMarker($g, [float]$x, [float]$y, [string]$fill, [string]$label, [string]$sub = '') {
  Draw-Ellipse $g ($x - 24) ($y - 24) 48 48 $fill '#FFFFFF' 4
  Draw-Ellipse $g ($x - 8) ($y - 8) 16 16 '#FFFFFF'
  if ($label) {
    Fill-RoundRect $g ($x - 62) ($y + 32) 124 40 20 '#FFFFFF'
    Draw-CenteredText $g $label $x ($y + 42) 17 '#172033' 'Bold'
  }
}

function Draw-ActivityThumb($g, [float]$x, [float]$y, [float]$w, [float]$h, [int]$kind = 0) {
  $fills = @('#F9D58A', '#B9E2D5', '#D9C6F1', '#FFD0BE')
  Fill-RoundRect $g $x $y $w $h 22 $fills[$kind % $fills.Count]
  if ($kind % 2 -eq 0) {
    Draw-Ellipse $g ($x + $w * .64) ($y + 20) ($h * .45) ($h * .45) '#FFD84D'
    Draw-Line $g ($x + 20) ($y + $h * .68) ($x + $w - 24) ($y + $h * .68) '#FFFFFF' 7
    Draw-Line $g ($x + 30) ($y + $h * .84) ($x + $w - 50) ($y + $h * .80) '#F39B67' 5
    for ($i = 0; $i -lt 4; $i++) {
      Draw-Ellipse $g ($x + 36 + $i * 44) ($y + $h * .42 + ($i % 2) * 15) 20 20 '#FFFFFF' '#172033' 2
    }
  } else {
    Fill-RoundRect $g ($x + 28) ($y + $h * .38) ($w - 56) ($h * .28) 16 '#FFFFFF'
    Draw-Line $g ($x + 48) ($y + $h * .52) ($x + $w - 48) ($y + $h * .52) '#A8D2C5' 5
    Draw-Ellipse $g ($x + 42) ($y + 24) 26 26 '#FF8D71'
    Draw-Ellipse $g ($x + $w - 78) ($y + 22) 28 28 '#93D9CA'
    Draw-Ellipse $g ($x + 46) ($y + $h * .72) 22 22 '#FFD84D'
    Draw-Ellipse $g ($x + $w - 72) ($y + $h * .72) 22 22 '#FF8D71'
  }
}

function Draw-HomePage($g, [float]$w, [float]$h) {
  Fill-Rect $g 0 0 $w $h '#FBF9F3'
  Draw-StatusBar $g $w
  Draw-Logo $g 34 84 .72
  Draw-Text $g '团团团' 106 91 27 '#172033' 'Bold'
  Fill-RoundRect $g ($w - 146) 81 112 50 25 '#FFFFFF'
  Draw-PinIcon $g ($w - 123) 106 '#EE735A'
  Draw-Text $g '长沙市' ($w - 105) 96 20 '#536173' 'Bold'
  Draw-Line $g ($w - 47) 111 ($w - 34) 111 '#9BA5AE' 2
  Draw-Line $g ($w - 41) 105 ($w - 34) 111 '#9BA5AE' 2
  Draw-Line $g ($w - 41) 117 ($w - 34) 111 '#9BA5AE' 2

  Fill-RoundRect $g 34 174 ($w - 68) 350 34 '#172033'
  Draw-Text $g '长沙周末，和谁一起去？' 68 214 43 '#FFFFFF' 'Bold'
  Draw-Text $g '说出你的想法，AI 帮你找到合适的拼团。' 68 286 22 '#CFD8E0' 'Regular' 560 1.55
  Draw-Text $g '自然语言找活动' 68 341 18 '#FFD84D' 'Bold'
  Draw-Line $g 68 365 440 365 '#556274' 2
  Draw-Ellipse $g 680 218 104 104 '#FF8D71'
  Draw-Ellipse $g 696 234 72 72 '#FFD2B8'
  Fill-RoundRect $g 704 258 56 34 17 '#172033'
  Draw-Ellipse $g 711 277 8 8 '#FFFFFF'
  Draw-Ellipse $g 741 277 8 8 '#FFFFFF'
  Draw-Line $g 721 306 744 306 '#172033' 3
  Draw-Line $g 676 320 647 355 '#FFD84D' 8
  Draw-Line $g 783 320 810 354 '#93D9CA' 8
  Draw-Line $g 670 350 642 368 '#FFD84D' 5
  Draw-Line $g 790 349 814 368 '#93D9CA' 5
  Fill-RoundRect $g 68 398 ($w - 136) 116 22 '#FFFFFF'
  Draw-Text $g '比如：周六下午，和 3 位朋友找个安静的地方' 92 428 22 '#99A3AE' 'Regular' 560 1.45
  Draw-Ellipse $g ($w - 150) 427 58 58 '#EE735A'
  Draw-Line $g ($w - 126) 456 ($w - 100) 456 '#FFFFFF' 3
  Draw-Line $g ($w - 108) 444 ($w - 100) 456 '#FFFFFF' 3
  Draw-Line $g ($w - 108) 468 ($w - 100) 456 '#FFFFFF' 3

  Draw-Text $g '热门拼团' 34 572 30 '#172033' 'Bold'
  Draw-Text $g '看看附近的人正在约什么' ($w - 250) 579 19 '#8A96A3' 'Regular' 215 1.3 'Right'
  Draw-ActivityThumb $g 34 628 238 150 0
  Draw-Text $g '橘子洲慢走局' 34 797 23 '#172033' 'Bold'
  Draw-Text $g '周六 16:00 · 已有 3 人' 34 831 18 '#778595'
  Draw-Text $g '2.4 km' 34 863 19 '#EE735A' 'Bold'
  Draw-Text $g '¥32/人' 166 863 19 '#172033' 'Bold'
  Draw-ActivityThumb $g 302 628 238 150 1
  Draw-Text $g '岳麓山轻徒步' 302 797 23 '#172033' 'Bold'
  Draw-Text $g '周日 09:30 · 已有 5 人' 302 831 18 '#778595'
  Draw-Text $g '4.8 km' 302 863 19 '#EE735A' 'Bold'
  Draw-Text $g '¥39/人' 434 863 19 '#172033' 'Bold'
  Draw-ActivityThumb $g 570 628 238 150 2
  Draw-Text $g '湘江边桌游局' 570 797 23 '#172033' 'Bold'
  Draw-Text $g '周六 14:00 · 已有 2 人' 570 831 18 '#778595'
  Draw-Text $g '3.1 km' 570 863 19 '#EE735A' 'Bold'
  Draw-Text $g '¥68/人' 702 863 19 '#172033' 'Bold'

  Fill-RoundRect $g 34 951 ($w - 68) 160 26 '#EFF7F2'
  Draw-Ellipse $g 62 987 52 52 '#FFD2B8'
  Draw-Ellipse $g 121 987 52 52 '#BDE7D9'
  Draw-Ellipse $g 180 987 52 52 '#D8C3EF'
  Draw-Text $g '今天已有 28 个新拼团' 264 982 24 '#172033' 'Bold'
  Draw-Text $g '从一个小想法开始，遇见一群同频的人。' 264 1024 19 '#718091' 'Regular' 470 1.4
  Draw-TabBar $g $w $h 0
}

function Draw-MapPage($g, [float]$w, [float]$h) {
  Fill-Rect $g 0 0 $w $h '#EEF2ED'
  Draw-StatusBar $g $w
  Draw-Text $g '拼团地图' 34 91 31 '#172033' 'Bold'
  Draw-Text $g '长沙市' ($w - 130) 96 20 '#EE735A' 'Bold' 95 1.2 'Right'
  Draw-PinIcon $g ($w - 41) 106 '#EE735A'
  Draw-SearchBar $g 34 147 ($w - 68) '搜索活动、地点或兴趣'
  Draw-Chip $g '全部' 34 229 86 '#172033' '#FFFFFF'
  Draw-Chip $g '运动' 130 229 82 '#FFFFFF' '#657182' '#DDE4E2'
  Draw-Chip $g '聚餐' 222 229 82 '#FFFFFF' '#657182' '#DDE4E2'
  Draw-Chip $g '观影' 314 229 82 '#FFFFFF' '#657182' '#DDE4E2'
  Draw-Chip $g '休闲' 406 229 82 '#FFFFFF' '#657182' '#DDE4E2'
  Draw-MapBase $g 0 295 $w 1088
  Draw-MapMarker $g 188 583 '#EE735A' '3人拼团'
  Draw-MapMarker $g 457 747 '#FFD84D' '5人拼团'
  Draw-MapMarker $g 686 970 '#93D9CA' '2人拼团'
  Draw-MapMarker $g 302 1112 '#C9B4EE' '4人拼团'
  Fill-RoundRect $g ($w - 92) 380 56 56 28 '#FFFFFF'
  Draw-Ellipse $g ($w - 74) 398 20 20 '' '#7F8A95' 3
  Draw-Line $g ($w - 65) 416 ($w - 54) 427 '#7F8A95' 3
  Fill-RoundRect $g ($w - 92) 452 56 56 28 '#FFFFFF'
  Draw-Line $g ($w - 64) 480 ($w - 36) 480 '#7F8A95' 3
  Draw-Line $g ($w - 50) 466 ($w - 50) 494 '#7F8A95' 3
  Fill-RoundRect $g 0 1245 $w 773 40 '#FFFFFF'
  Draw-Ellipse $g 60 1283 9 9 '#EE735A'
  Draw-Text $g '附近有 12 个拼团' 82 1269 20 '#728090' 'Bold'
  Draw-ActivityThumb $g 34 1325 182 116 0
  Draw-Text $g '橘子洲慢走局' 238 1327 23 '#172033' 'Bold'
  Draw-Text $g '周六 16:00 · 还有 3 个位置' 238 1367 18 '#718091'
  Draw-Text $g '2.4 km' 238 1405 19 '#EE735A' 'Bold'
  Draw-Text $g '¥32/人' 330 1405 19 '#172033' 'Bold'
  Draw-Line $g 34 1468 ($w - 34) 1468 '#EEF1EE' 2
  Draw-ActivityThumb $g 34 1496 182 116 1
  Draw-Text $g '岳麓山轻徒步' 238 1498 23 '#172033' 'Bold'
  Draw-Text $g '周日 09:30 · 适合新朋友' 238 1538 18 '#718091'
  Draw-Text $g '4.8 km' 238 1576 19 '#EE735A' 'Bold'
  Draw-Text $g '¥39/人' 330 1576 19 '#172033' 'Bold'
  Draw-Line $g 34 1639 ($w - 34) 1639 '#EEF1EE' 2
  Draw-Text $g '拖动地图查看更多活动' 34 1680 18 '#A0A9B1'
  Draw-TabBar $g $w $h 1
}

function Draw-PublishPage($g, [float]$w, [float]$h) {
  Fill-Rect $g 0 0 $w $h '#FBF9F3'
  Draw-StatusBar $g $w
  Draw-Text $g '发起拼团' 34 91 31 '#172033' 'Bold'
  Draw-Text $g '让 AI 帮你找到同频的人' 34 145 23 '#EE735A' 'Bold'
  Fill-RoundRect $g 34 207 ($w - 68) 336 28 '#FFFFFF'
  Draw-Text $g '说说你想要的活动' 62 239 26 '#172033' 'Bold'
  Draw-Text $g '周六下午和 3 位朋友，找长沙市区 5 公里内、' 62 300 23 '#4F5D6E' 'Regular' 650 1.5
  Draw-Text $g '人均 100 元以内、安静一点的活动' 62 335 23 '#4F5D6E' 'Regular' 650 1.5
  Draw-Text $g '告诉我时间、人数、预算和偏好，剩下的交给我。' 62 445 19 '#A0A9B1' 'Regular' 650 1.5
  Draw-Line $g 62 492 ($w - 62) 492 '#E5E9E7' 2
  Draw-Text $g '输入越具体，匹配越准确' ($w - 270) 508 17 '#A0A9B1' 'Regular' 220 1.2 'Right'

  Draw-Text $g '快速补充' 34 596 27 '#172033' 'Bold'
  Draw-Chip $g '周六下午' 34 650 132 '#FFF0EA' '#EE735A'
  Draw-Chip $g '4 个人' 178 650 102 '#FFF0EA' '#EE735A'
  Draw-Chip $g '5 公里内' 292 650 132 '#FFF0EA' '#EE735A'
  Draw-Chip $g '¥100/人' 436 650 132 '#FFF0EA' '#EE735A'
  Draw-Chip $g '安静' 580 650 92 '#EAF7F1' '#4D8C79'
  Draw-Chip $g '朋友聚会' 680 650 128 '#EAF7F1' '#4D8C79'

  Draw-Text $g '发布后会发生什么？' 34 767 27 '#172033' 'Bold'
  Fill-RoundRect $g 34 819 ($w - 68) 220 24 '#172033'
  Draw-Ellipse $g 73 864 46 46 '#FFD84D'
  Draw-Text $g '1' 89 873 19 '#172033' 'Bold'
  Draw-Text $g 'AI 解析你的需求' 145 861 23 '#FFFFFF' 'Bold'
  Draw-Text $g '把自然语言整理成清晰的条件' 145 901 18 '#CBD6DE'
  Draw-Ellipse $g 73 942 46 46 '#FF8D71'
  Draw-Text $g '2' 89 951 19 '#172033' 'Bold'
  Draw-Text $g '匹配活动和同频伙伴' 145 939 23 '#FFFFFF' 'Bold'
  Draw-Text $g '给你一份可以直接决定的推荐' 145 979 18 '#CBD6DE'

  Fill-RoundRect $g 34 1101 ($w - 68) 104 24 '#EE735A'
  Draw-Text $g '让 AI 帮我找' 287 1130 30 '#FFFFFF' 'Bold'
  Draw-Line $g 526 1153 554 1153 '#FFFFFF' 3
  Draw-Line $g 542 1141 554 1153 '#FFFFFF' 3
  Draw-Line $g 542 1165 554 1153 '#FFFFFF' 3
  Draw-Text $g '发布后你仍然可以修改需求' 34 1263 18 '#9BA5AE' 'Regular' 775 1.4 'Center'
  Draw-TabBar $g $w $h 2
}

function Draw-AIConfirmPage($g, [float]$w, [float]$h) {
  Fill-Rect $g 0 0 $w $h '#FBF9F3'
  Draw-TopBar $g $w '确认你的需求'
  Fill-RoundRect $g 34 173 ($w - 68) 214 28 '#172033'
  Draw-Ellipse $g 72 212 72 72 '#FFD84D'
  Draw-Text $g 'AI' 91 230 21 '#172033' 'Bold'
  Draw-Text $g '我这样理解，可以吗？' 172 211 27 '#FFFFFF' 'Bold'
  Draw-Text $g '如果有不准确的地方，点一下就能修改。' 172 255 19 '#CED8DF' 'Regular' 560 1.4
  Draw-Chip $g '理解完成' 172 309 108 '#EAF7F1' '#4D8C79'

  Draw-Text $g '你的活动条件' 34 449 30 '#172033' 'Bold'
  Fill-RoundRect $g 34 507 ($w - 68) 550 26 '#FFFFFF'
  $rows = @(
    @('人数', '4 人', '#FFD84D'),
    @('时间', '周六下午', '#FF8D71'),
    @('范围', '5 公里内', '#93D9CA'),
    @('预算', '¥100/人以内', '#FFD84D'),
    @('偏好', '安静 · 朋友聚会', '#FF8D71'),
    @('城市', '长沙市区', '#93D9CA')
  )
  $ry = 544
  foreach ($row in $rows) {
    Draw-Ellipse $g 67 $ry 34 34 $row[2]
    Draw-Text $g $row[0] 124 ($ry + 3) 22 '#8995A1'
    Draw-Text $g $row[1] 250 ($ry + 1) 24 '#172033' 'Bold'
    Draw-Text $g '修改' ($w - 103) ($ry + 5) 18 '#EE735A' 'Bold'
    if ($ry -lt 990) { Draw-Line $g 66 ($ry + 68) ($w - 66) ($ry + 68) '#EEF0ED' 2 }
    $ry += 79
  }
  Fill-RoundRect $g 34 1121 ($w - 68) 112 26 '#EE735A'
  Draw-Text $g '确认并开始匹配' 253 1154 29 '#FFFFFF' 'Bold'
  Draw-Line $g 555 1177 583 1177 '#FFFFFF' 3
  Draw-Line $g 571 1165 583 1177 '#FFFFFF' 3
  Draw-Line $g 571 1189 583 1177 '#FFFFFF' 3
  Draw-Text $g '预计为你找到 12 个合适拼团' 34 1276 20 '#788596' 'Regular' 775 1.4 'Center'
}

function Draw-ResultsPage($g, [float]$w, [float]$h) {
  Fill-Rect $g 0 0 $w $h '#FBF9F3'
  Draw-TopBar $g $w '匹配结果' '筛选'
  Draw-Text $g '找到 12 个合适拼团' 34 178 30 '#172033' 'Bold'
  Draw-Text $g '符合 4 人 · 周六下午 · 5 公里内 · ¥100/人' 34 225 18 '#7C8997'
  Draw-Chip $g '推荐排序' 34 277 122 '#172033' '#FFFFFF'
  Draw-Chip $g '距离最近' 168 277 122 '#FFFFFF' '#677486' '#DDE4E2'
  Fill-RoundRect $g ($w - 138) 277 104 44 22 '#EAF7F1'
  Draw-Text $g '地图' ($w - 107) 289 19 '#4D8C79' 'Bold'
  Draw-PinIcon $g ($w - 51) 299 '#4D8C79'

  $cards = @(
    @('橘子洲慢走局', '周六 16:00 · 还有 3 个位置', '2.4 km', '¥32/人', '94%', 0),
    @('岳麓山轻徒步', '周日 09:30 · 还有 1 个位置', '4.8 km', '¥39/人', '89%', 1),
    @('湘江边桌游局', '周六 14:00 · 还有 4 个位置', '3.1 km', '¥68/人', '87%', 2)
  )
  $cy = 356
  foreach ($card in $cards) {
    Fill-RoundRect $g 34 $cy ($w - 68) 260 26 '#FFFFFF'
    Draw-ActivityThumb $g 58 ($cy + 27) 190 142 $card[5]
    Fill-RoundRect $g 168 ($cy + 38) 66 34 17 '#172033'
    Draw-CenteredText $g $card[4] 201 ($cy + 47) 16 '#FFD84D' 'Bold'
    Draw-Text $g $card[0] 276 ($cy + 36) 25 '#172033' 'Bold'
    Draw-Text $g $card[1] 276 ($cy + 78) 18 '#788596' 'Regular' 480 1.3
    Draw-Text $g $card[2] 276 ($cy + 124) 20 '#EE735A' 'Bold'
    Draw-Text $g $card[3] 383 ($cy + 124) 20 '#172033' 'Bold'
    Draw-Text $g '为什么推荐' 58 ($cy + 191) 18 '#4D8C79' 'Bold'
    Draw-Text $g '距离和预算都很合适，氛围安静，适合朋友聊天。' 168 ($cy + 188) 17 '#758292' 'Regular' 600 1.35
    $cy += 292
  }
  Draw-Text $g '还可以继续调整需求' 34 1304 19 '#A0A9B1' 'Regular' 775 1.4 'Center'
}

function Draw-GroupDetailPage($g, [float]$w, [float]$h) {
  Fill-Rect $g 0 0 $w $h '#FBF9F3'
  Draw-StatusBar $g $w
  Fill-Rect $g 0 0 $w 622 '#B9E2D5'
  Draw-Back $g 34 111 '#FFFFFF'
  Draw-Text $g '分享' ($w - 81) 96 20 '#FFFFFF' 'Bold'
  Draw-Ellipse $g ($w - 47) 101 8 8 '#FFFFFF'
  Draw-Ellipse $g ($w - 30) 101 8 8 '#FFFFFF'
  Draw-Ellipse $g ($w - 64) 101 8 8 '#FFFFFF'
  Draw-Ellipse $g 568 206 180 180 '#FFD84D'
  Draw-Line $g 114 518 740 518 '#FFFFFF' 16
  Draw-Line $g 164 473 274 518 '#93C5AE' 8
  Draw-Line $g 274 518 396 468 '#93C5AE' 8
  Draw-Line $g 396 468 546 518 '#93C5AE' 8
  Draw-Line $g 546 518 690 466 '#93C5AE' 8
  Draw-Avatar $g 176 391 76 '#FFD2B8' '#FF8D71'
  Draw-Avatar $g 289 379 86 '#F2C5AB' '#FFD84D'
  Draw-Avatar $g 402 394 76 '#DCA98C' '#93D9CA'
  Draw-Avatar $g 516 378 86 '#F8D5BE' '#C9B4EE'
  Fill-RoundRect $g 34 554 ($w - 68) 238 28 '#FFFFFF'
  Draw-Text $g '橘子洲慢走局' 62 594 32 '#172033' 'Bold'
  Fill-RoundRect $g ($w - 192) 588 126 44 22 '#FFF0EA'
  Draw-CenteredText $g '匹配度 94%' ($w - 129) 600 18 '#EE735A' 'Bold'
  Draw-Text $g '周六 16:00 · 橘子洲南门集合' 62 651 20 '#677486'
  Draw-Text $g '¥32/人 · 已有 3 人 · 还差 3 人' 62 689 20 '#677486'
  Draw-Text $g '适合认识新朋友，也适合边走边聊。' 62 729 19 '#9A6D5D'

  Draw-Text $g '拼团成员' 34 858 28 '#172033' 'Bold'
  Draw-Text $g '3/6 人' ($w - 100) 863 19 '#7E8A98' 'Bold' 68 1.2 'Right'
  Draw-Avatar $g 34 916 74 '#FFD2B8' '#FF8D71'
  Draw-Avatar $g 123 916 74 '#F2C5AB' '#FFD84D'
  Draw-Avatar $g 212 916 74 '#DCA98C' '#93D9CA'
  Fill-RoundRect $g 301 916 74 74 37 '#F3F5F3'
  Draw-Text $g '+' 326 932 33 '#A0A9B1' 'Regular'
  Draw-Text $g '还有 3 个位置，等你来加入' 405 940 20 '#728090'

  Fill-RoundRect $g 34 1050 ($w - 68) 195 24 '#FFFFFF'
  Draw-Text $g '拼团信息' 62 1084 24 '#172033' 'Bold'
  Draw-Text $g '集合点' 62 1133 18 '#8B97A3'
  Draw-Text $g '橘子洲南门地铁站 2 号出口' 178 1130 19 '#172033' 'Bold'
  Draw-Text $g '拼团规则' 62 1180 18 '#8B97A3'
  Draw-Text $g '不迟到 · AA 制 · 友好交流' 178 1177 19 '#172033' 'Bold'

  Fill-RoundRect $g 34 1290 160 76 22 '#FFFFFF'
  Draw-Text $g '收藏' 84 1317 22 '#657182' 'Bold'
  Draw-Ellipse $g 59 1318 15 15 '' '#EE735A' 2
  Fill-RoundRect $g 212 1290 160 76 22 '#FFFFFF'
  Draw-Text $g '分享' 262 1317 22 '#657182' 'Bold'
  Draw-Line $g 237 1330 255 1318 '#EE735A' 3
  Draw-Line $g 255 1318 269 1332 '#EE735A' 3
  Fill-RoundRect $g 390 1290 ($w - 424) 76 22 '#EE735A'
  Draw-CenteredText $g '加入拼团' ($w / 2 + 104) 1314 25 '#FFFFFF' 'Bold'
}

function Draw-ChatPage($g, [float]$w, [float]$h) {
  Fill-Rect $g 0 0 $w $h '#F6F7F4'
  Draw-TopBar $g $w '周六橘子洲慢走局' '群详情'
  Draw-Text $g '3 人已加入 · 还差 3 人' 34 154 18 '#7E8A98'
  Fill-RoundRect $g 34 207 ($w - 68) 198 24 '#EAF7F1'
  Draw-Ellipse $g 66 240 48 48 '#FFD84D'
  Draw-Text $g 'AI' 77 254 14 '#172033' 'Bold'
  Draw-Text $g '团团 AI 助手' 135 238 20 '#4D8C79' 'Bold'
  Draw-Text $g '已为你们创建集合提醒：' 135 274 18 '#58716D'
  Draw-Text $g '周六 16:00，橘子洲南门地铁站 2 号出口' 135 307 18 '#58716D' 'Regular' 570 1.4
  Fill-RoundRect $g 135 347 178 36 18 '#FFFFFF'
  Draw-CenteredText $g '查看活动详情' 224 356 16 '#4D8C79' 'Bold'

  Draw-Avatar $g 34 461 58 '#F2C5AB' '#FFD84D'
  Fill-RoundRect $g 110 458 414 88 22 '#FFFFFF'
  Draw-Text $g '大家好，我是小林，第一次参加。' 136 483 20 '#3F4D5C'
  Draw-Text $g '很期待周末一起走走～' 136 516 20 '#3F4D5C'
  Draw-Text $g '16:18' 532 524 16 '#A1AAB3'

  Fill-RoundRect $g 322 595 487 78 22 '#172033'
  Draw-Text $g '欢迎！我们在南门集合，别忘了带水。' 350 620 19 '#FFFFFF'  'Regular' 420 1.4
  Draw-Text $g '16:20' 739 646 16 '#9AA8B5'
  Draw-Avatar $g 754 706 58 '#FFD2B8' '#FF8D71'

  Fill-RoundRect $g 34 768 ($w - 68) 218 24 '#FFFFFF'
  Draw-Text $g '集合地点' 62 802 21 '#172033' 'Bold'
  Fill-RoundRect $g 62 852 310 82 18 '#EAF7F1'
  Draw-PinIcon $g 92 893 '#4D8C79'
  Draw-Text $g '橘子洲南门' 124 875 20 '#172033' 'Bold'
  Draw-Text $g '距你约 2.4 km' 124 907 17 '#799087'
  Draw-Text $g '已确认' 664 879 18 '#4D8C79' 'Bold'

  Fill-RoundRect $g 34 1617 ($w - 68) 64 30 '#FFFFFF'
  Draw-Text $g '发送位置' 72 1636 19 '#657182' 'Bold'
  Draw-PinIcon $g 54 1649 '#EE735A'
  Fill-RoundRect $g 212 1617 174 64 30 '#FFFFFF'
  Draw-Text $g '查看活动详情' 242 1636 19 '#657182' 'Bold'
  Fill-RoundRect $g 34 1730 ($w - 68) 86 32 '#FFFFFF'
  Draw-Text $g '输入消息...' 66 1759 20 '#B2BBC2'
  Draw-Ellipse $g ($w - 127) 1746 54 54 '#EE735A'
  Draw-Line $g ($w - 106) 1773 ($w - 83) 1773 '#FFFFFF' 3
  Draw-Line $g ($w - 91) 1762 ($w - 83) 1773 '#FFFFFF' 3
  Draw-Line $g ($w - 91) 1784 ($w - 83) 1773 '#FFFFFF' 3
}

function Draw-MyPage($g, [float]$w, [float]$h) {
  Fill-Rect $g 0 0 $w $h '#FBF9F3'
  Draw-StatusBar $g $w
  Draw-Text $g '我的' 34 91 31 '#172033' 'Bold'
  Fill-RoundRect $g 34 167 ($w - 68) 248 28 '#172033'
  Draw-Ellipse $g 68 215 92 92 '#F2C5AB'
  Draw-Ellipse $g 91 241 46 46 '#FFD2B8'
  Fill-RoundRect $g 87 224 54 27 14 '#172033'
  Draw-Text $g '游客模式' 194 214 28 '#FFFFFF' 'Bold'
  Draw-Text $g '登录后管理你的拼团、收藏和聊天' 194 263 19 '#C9D4DB' 'Regular' 510 1.45
  Fill-RoundRect $g 194 320 178 52 26 '#FFD84D'
  Draw-CenteredText $g '微信一键登录' 283 335 19 '#172033' 'Bold'

  Draw-Text $g '我的内容' 34 495 28 '#172033' 'Bold'
  $rows = @(
    @('我的拼团', '查看已加入和已发起的拼团', '#FF8D71'),
    @('我的收藏', '收藏的活动和地点', '#FFD84D'),
    @('浏览记录', '最近看过的推荐', '#93D9CA')
  )
  $yy = 553
  foreach ($row in $rows) {
    Fill-RoundRect $g 34 $yy ($w - 68) 106 20 '#FFFFFF'
    Draw-Ellipse $g 64 ($yy + 29) 48 48 $row[2]
    Draw-Text $g $row[0] 136 ($yy + 23) 22 '#172033' 'Bold'
    Draw-Text $g $row[1] 136 ($yy + 60) 17 '#86919E'
    Draw-Line $g ($w - 68) ($yy + 52) ($w - 50) ($yy + 52) '#A3ADB5' 3
    Draw-Line $g ($w - 57) ($yy + 43) ($w - 50) ($yy + 52) '#A3ADB5' 3
    Draw-Line $g ($w - 57) ($yy + 61) ($w - 50) ($yy + 52) '#A3ADB5' 3
    $yy += 126
  }
  Draw-Text $g '更多设置' 34 968 28 '#172033' 'Bold'
  Fill-RoundRect $g 34 1026 ($w - 68) 88 20 '#FFFFFF'
  Draw-Text $g '隐私与安全' 64 1055 21 '#657182' 'Bold'
  Draw-Text $g '›' ($w - 72) 1047 34 '#A3ADB5' 'Regular'
  Fill-RoundRect $g 34 1130 ($w - 68) 88 20 '#FFFFFF'
  Draw-Text $g '关于团团团' 64 1159 21 '#657182' 'Bold'
  Draw-Text $g '›' ($w - 72) 1151 34 '#A3ADB5' 'Regular'
  Draw-TabBar $g $w $h 4
}

function New-DeviceImage([string]$label, [scriptblock]$pageBlock, [string]$fileName) {
  $bmp = [System.Drawing.Bitmap]::new($W, $H)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
  $g.Clear((Hex '#EEF0EB'))

  Draw-Text $g '团团团 · 高保真产品原型' 60 55 23 '#697587' 'Bold'
  Draw-Text $g $label 60 93 18 '#9AA3AC' 'Regular'
  Fill-RoundRect $g ($ScreenX - 18) ($ScreenY - 18) ($ScreenW + 36) ($ScreenH + 36) 112 '#111522'
  Fill-RoundRect $g $ScreenX $ScreenY $ScreenW $ScreenH 78 '#FBF9F3'

  $save = $g.Save()
  $g.TranslateTransform($ScreenX, $ScreenY)
  $clip = New-PathRoundRect 0 0 $ScreenW $ScreenH 78
  $g.SetClip($clip)
  & $pageBlock $g $ScreenW $ScreenH
  $clip.Dispose()
  $g.Restore($save)

  Fill-RoundRect $g ($ScreenX + 292) ($ScreenY + 13) 258 39 20 '#111522'
  Draw-Ellipse $g ($ScreenX + 513) ($ScreenY + 26) 8 8 '#34404D'
  Fill-RoundRect $g ($ScreenX + 350) ($ScreenY + $ScreenH - 31) 143 8 4 '#111522'

  $path = Join-Path $Output $fileName
  $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose()
  $bmp.Dispose()
}

function Draw-OverviewCard($g, [System.Drawing.Image]$image, [float]$x, [float]$y, [float]$w, [float]$h, [string]$title, [int]$number) {
  Fill-RoundRect $g $x $y $w $h 28 '#FFFFFF'
  $inner = New-PathRoundRect ($x + 10) ($y + 10) ($w - 20) ($h - 50) 20
  $save = $g.Save()
  $g.SetClip($inner)
  $g.DrawImage($image, [System.Drawing.RectangleF]::new($x + 10, $y + 10, $w - 20, $h - 50))
  $g.Restore($save)
  $inner.Dispose()
  Draw-Ellipse $g ($x + 18) ($y + $h - 33) 22 22 '#EE735A'
  Draw-CenteredText $g ([string]$number) ($x + 29) ($y + $h - 29) 13 '#FFFFFF' 'Bold'
  Draw-Text $g $title ($x + 51) ($y + $h - 31) 17 '#172033' 'Bold' ($w - 62) 1.2
}

function New-OverviewImage {
  $ow = 2400
  $oh = 1500
  $bmp = [System.Drawing.Bitmap]::new($ow, $oh)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
  $g.Clear((Hex '#F1F3EF'))
  Draw-Text $g '团团团 · AI 拼团产品流程总览' 78 66 42 '#172033' 'Bold'
  Draw-Text $g '先浏览 → 发布需求 → AI 理解 → 匹配拼团 → 查看详情 → 进入群聊 → 管理个人内容' 80 132 24 '#748192' 'Regular' 2100 1.4
  $titles = @('首页 / 游客', '拼团地图', '需求发布', 'AI 解析', '匹配结果', '拼团详情', '群聊', '我的 / 游客')
  $files = @('01-home-guest.png', '02-group-map.png', '03-publish-request.png', '04-ai-confirm.png', '05-match-results.png', '06-group-detail.png', '07-group-chat.png', '08-my-guest.png')
  $images = @()
  foreach ($file in $files) {
    $images += [System.Drawing.Image]::FromFile((Join-Path $Output $file))
  }
  $cardW = 490
  $cardH = 530
  $xs = @(80, 640, 1200, 1760)
  $ys = @(235, 870)
  $number = 1
  for ($row = 0; $row -lt 2; $row++) {
    for ($col = 0; $col -lt 4; $col++) {
      $idx = $row * 4 + $col
      Draw-OverviewCard $g $images[$idx] $xs[$col] $ys[$row] $cardW $cardH $titles[$idx] $number
      if ($col -lt 3) {
        $arrowX = $xs[$col] + $cardW + 22
        $arrowY = $ys[$row] + 258
        Draw-Line $g $arrowX $arrowY ($arrowX + 30) $arrowY '#EE735A' 5
        Draw-Line $g ($arrowX + 18) ($arrowY - 10) ($arrowX + 30) $arrowY '#EE735A' 5
        Draw-Line $g ($arrowX + 18) ($arrowY + 10) ($arrowX + 30) $arrowY '#EE735A' 5
      }
      $number++
    }
  }
  Draw-Line $g 1990 765 1990 840 '#EE735A' 5
  Draw-Line $g 1978 825 1990 840 '#EE735A' 5
  Draw-Line $g 2002 825 1990 840 '#EE735A' 5
  Draw-Text $g '主流程：用户从浏览开始，经 AI 辅助完成一次可执行的线下相聚。' 80 1450 22 '#7B8795' 'Regular'
  $path = Join-Path $Output '00-flow-overview.png'
  $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  foreach ($image in $images) { $image.Dispose() }
  $g.Dispose()
  $bmp.Dispose()
}

New-DeviceImage '01 首页 / 游客入口' ${function:Draw-HomePage} '01-home-guest.png'
New-DeviceImage '02 拼团地图' ${function:Draw-MapPage} '02-group-map.png'
New-DeviceImage '03 需求发布' ${function:Draw-PublishPage} '03-publish-request.png'
New-DeviceImage '04 AI 需求解析确认' ${function:Draw-AIConfirmPage} '04-ai-confirm.png'
New-DeviceImage '05 匹配结果' ${function:Draw-ResultsPage} '05-match-results.png'
New-DeviceImage '06 拼团详情' ${function:Draw-GroupDetailPage} '06-group-detail.png'
New-DeviceImage '07 群聊界面' ${function:Draw-ChatPage} '07-group-chat.png'
New-DeviceImage '08 我的 / 未登录' ${function:Draw-MyPage} '08-my-guest.png'
New-OverviewImage

Write-Output "Generated prototypes in $Output"
