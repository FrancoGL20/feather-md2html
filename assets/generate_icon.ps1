Add-Type -AssemblyName System.Drawing

$size = 256
$bmp = New-Object System.Drawing.Bitmap $size, $size
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$g.Clear([System.Drawing.Color]::Transparent)

# Background Squircle (Apple icon shape)
$rect = New-Object System.Drawing.Rectangle 12, 12, 232, 232
$path = New-Object System.Drawing.Drawing2D.GraphicsPath
$radius = 52
$d = $radius * 2

$path.AddArc($rect.X, $rect.Y, $d, $d, 180, 90)
$path.AddArc($rect.Right - $d, $rect.Y, $d, $d, 270, 90)
$path.AddArc($rect.Right - $d, $rect.Bottom - $d, $d, $d, 0, 90)
$path.AddArc($rect.X, $rect.Bottom - $d, $d, $d, 90, 90)
$path.CloseFigure()

# Background gradient: Deep Obsidian Mate (#111114 to #070708)
$brushBg = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    (New-Object System.Drawing.Point 0, 0),
    (New-Object System.Drawing.Point 0, 256),
    [System.Drawing.Color]::FromArgb(255, 17, 17, 20),
    [System.Drawing.Color]::FromArgb(255, 7, 7, 8)
)
$g.FillPath($brushBg, $path)

# Subtle warm light-catching border
$penBorder = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(80, 248, 250, 252), 2)
$g.DrawPath($penBorder, $path)

# Subtle volcanic amber outer glow / inner border
$penInner = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(50, 249, 115, 22), 3)
$g.DrawPath($penInner, $path)

# Draw Document Shape (Folded page)
$docPath = New-Object System.Drawing.Drawing2D.GraphicsPath
$dx = 66
$dy = 46
$dw = 124
$dh = 164
$fold = 36

# Points for folded page:
$docPath.AddLine($dx + 12, $dy, $dx + $dw - $fold, $dy)
$docPath.AddLine($dx + $dw, $dy + $fold, $dx + $dw, $dy + $dh - 12)
# Bottom right curve
$docPath.AddArc($dx + $dw - 24, $dy + $dh - 24, 24, 24, 0, 90)
$docPath.AddLine($dx + $dw - 12, $dy + $dh, $dx + 12, $dy + $dh)
# Bottom left curve
$docPath.AddArc($dx, $dy + $dh - 24, 24, 24, 90, 90)
$docPath.AddLine($dx, $dy + $dh - 12, $dx, $dy + 12)
# Top left curve
$docPath.AddArc($dx, $dy, 24, 24, 180, 90)
$docPath.CloseFigure()

# Fill document with basalt obsidian glass / gradient
$brushDoc = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    (New-Object System.Drawing.Point $dx, $dy),
    (New-Object System.Drawing.Point ($dx + $dw), ($dy + $dh)),
    [System.Drawing.Color]::FromArgb(255, 23, 24, 28),
    [System.Drawing.Color]::FromArgb(255, 14, 14, 17)
)
$g.FillPath($brushDoc, $docPath)
$penDoc = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(65, 255, 255, 255), 1.5)
$g.DrawPath($penDoc, $docPath)

# Fold corner triangle
$foldPath = New-Object System.Drawing.Drawing2D.GraphicsPath
$foldPath.AddLine($dx + $dw - $fold, $dy, $dx + $dw - $fold, $dy + $fold - 6)
$foldPath.AddArc($dx + $dw - $fold, $dy + $fold - 12, 12, 12, 180, 90)
$foldPath.AddLine($dx + $dw - $fold + 6, $dy + $fold, $dx + $dw, $dy + $fold)
$foldPath.AddLine($dx + $dw - $fold, $dy, $dx + $dw, $dy + $fold)
$foldPath.CloseFigure()
$brushFold = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 32, 33, 39))
$g.FillPath($brushFold, $foldPath)

# Document text lines (symbolic)
$penLine = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(190, 248, 250, 252), 4)
$penLine.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
$penLine.EndCap = [System.Drawing.Drawing2D.LineCap]::Round

# Line 1 (Short title)
$g.DrawLine($penLine, ($dx + 22), ($dy + 40), ($dx + 68), ($dy + 40))
# Line 2 (Heading underline - Volcanic Amber)
$penAccent = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(255, 249, 115, 22), 4)
$penAccent.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
$penAccent.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
$g.DrawLine($penAccent, ($dx + 22), ($dy + 56), ($dx + $dw - 24), ($dy + 56))

# Line 3, 4, 5 (Basalt slate lines)
$penSub = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(130, 148, 163, 184), 3.5)
$penSub.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
$penSub.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
$g.DrawLine($penSub, ($dx + 22), ($dy + 76), ($dx + $dw - 24), ($dy + 76))
$g.DrawLine($penSub, ($dx + 22), ($dy + 94), ($dx + $dw - 36), ($dy + 94))
$g.DrawLine($penSub, ($dx + 22), ($dy + 112), ($dx + 75), ($dy + 112))

# Electric lightning bolt / HTML badge in bottom-right (Volcanic Amber Sunset gradient)
$boltPath = New-Object System.Drawing.Drawing2D.GraphicsPath
$bx = $dx + 52
$by = $dy + 96
$boltPath.AddLine($bx + 26, $by, $bx + 8, $by + 34)
$boltPath.AddLine($bx + 8, $by + 34, $bx + 20, $by + 34)
$boltPath.AddLine($bx + 14, $by + 60, $bx + 38, $by + 22)
$boltPath.AddLine($bx + 38, $by + 22, $bx + 24, $by + 22)
$boltPath.CloseFigure()

$brushBoltGlow = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(90, 249, 115, 22))
$g.FillEllipse($brushBoltGlow, ($bx - 5), ($by + 5), 52, 52)

$brushBolt = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    (New-Object System.Drawing.Point $bx, $by),
    (New-Object System.Drawing.Point ($bx + 40), ($by + 60)),
    [System.Drawing.Color]::FromArgb(255, 251, 146, 60),
    [System.Drawing.Color]::FromArgb(255, 212, 87, 6)
)
$g.FillPath($brushBolt, $boltPath)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pngPath = Join-Path $scriptDir "app_icon.png"
$icoPath = Join-Path $scriptDir "app_icon.ico"

# Save high-res PNG
$bmp.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)

# Convert PNG to Windows ICO format (256x256 embedded PNG)
$pngBytes = [System.IO.File]::ReadAllBytes($pngPath)
$ms = New-Object System.IO.MemoryStream
$bw = New-Object System.IO.BinaryWriter $ms

# ICONHEADER (6 bytes)
$bw.Write([uint16]0) # Reserved
$bw.Write([uint16]1) # Type 1 (ICO)
$bw.Write([uint16]1) # Number of images (1)

# ICONDIRENTRY (16 bytes)
$bw.Write([byte]0)   # Width (0 = 256px)
$bw.Write([byte]0)   # Height (0 = 256px)
$bw.Write([byte]0)   # Colors
$bw.Write([byte]0)   # Reserved
$bw.Write([uint16]1) # Planes
$bw.Write([uint16]32)# BitCount
$bw.Write([uint32]$pngBytes.Length) # Image size
$bw.Write([uint32]22)# Offset (6 + 16 = 22)

# Write PNG bytes
$bw.Write($pngBytes)
$bw.Flush()

[System.IO.File]::WriteAllBytes($icoPath, $ms.ToArray())
$g.Dispose()
$bmp.Dispose()
$ms.Dispose()

Write-Output "Iconos generados exitosamente: $pngPath y $icoPath"
