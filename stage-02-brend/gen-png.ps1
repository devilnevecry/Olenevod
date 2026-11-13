$ErrorActionPreference = "Stop"
$brand = "C:\Users\nu11\Documents\GitHub\Olenevod\olenevod\brand"

function New-Buffer($w,$h){ [byte[]]::new($w*$h*4) }

# Инлайн-заливка диапазона пикселей одной строки (без вызова функции на пиксель)
$FillSpan = {
  param($buf,$w,$y,$x0,$x1,$b,$g,$r,$a)
  $base = ($y*$w+$x0)*4
  for($x=$x0;$x -le $x1;$x++){
    $buf[$base]=$b; $buf[$base+1]=$g; $buf[$base+2]=$r; $buf[$base+3]=$a
    $base += 4
  }
}

function Fill-Rect($buf,$w,$h,$x,$y,$w2,$h2,$c){
  $x0=[math]::Max(0,[math]::Floor($x)); $y0=[math]::Max(0,[math]::Floor($y))
  $x1=[math]::Min($w-1,[math]::Floor($x+$w2)-1); $y1=[math]::Min($h-1,[math]::Floor($y+$h2)-1)
  if($x0 -gt $x1 -or $y0 -gt $y1){return}
  # шаблон строки
  $tpl = [byte[]]::new(($x1-$x0+1)*4); $k=0
  for($xx=$x0;$xx -le $x1;$xx++){ $tpl[$k++]=$c.b; $tpl[$k++]=$c.g; $tpl[$k++]=$c.r; $tpl[$k++]=$c.a }
  $rowBytes = ($x1-$x0+1)*4
  for($yy=$y0;$yy -le $y1;$yy++){
    [System.Array]::Copy($tpl,0,$buf,($yy*$w+$x0)*4,$rowBytes)
  }
}
function Fill-Circle($buf,$w,$h,$cx,$cy,$r,$c){
  $ry = [math]::Ceiling($r)
  for($dy=-$ry;$dy -le $ry;$dy++){
    $yy=$cy+$dy; if($yy -lt 0 -or $yy -ge $h){continue}
    $dx=[math]::Sqrt([math]::Max(0,$r*$r-$dy*$dy))
    $x0=[math]::Max(0,[math]::Ceiling($cx-$dx-1e-6)); $x1=[math]::Min($w-1,[math]::Floor($cx+$dx+1e-6))
    if($x0 -le $x1){ & $FillSpan $buf $w $yy $x0 $x1 $c.b $c.g $c.r $c.a }
  }
}
function Stroke-Circle($buf,$w,$h,$cx,$cy,$r,$thick,$c){
  for($t=0;$t -lt $thick;$t++){
    $rr=$r-$t; if($rr -le 0){break}
    $x=$rr; $y=0; $err=0
    while($x -ge $y){
      $pts = @(($cx+$x),($cy+$y)),@(($cx-$x),($cy+$y)),@(($cx+$x),($cy-$y)),@(($cx-$x),($cy-$y)),@(($cx+$y),($cy+$x)),@(($cx-$y),($cy+$x)),@(($cx+$y),($cy-$x)),@(($cx-$y),($cy-$x))
      foreach($p in $pts){
        $px=$p[0]; $py=$p[1]
        if($px -ge 0 -and $px -lt $w -and $py -ge 0 -and $py -lt $h){
          $i=($py*$w+$px)*4; $buf[$i]=$c.b; $buf[$i+1]=$c.g; $buf[$i+2]=$c.r; $buf[$i+3]=$c.a
        }
      }
      $y++; $err += 1+2*$y
      if(2*$err-$x+1 -gt 0){ $x--; $err += 1-2*$x }
    }
  }
}
function Fill-Polygon($buf,$w,$h,$pts,$c){
  $edges=@()
  for($i=0;$i -lt $pts.Count;$i++){
    $p1=$pts[$i]; $p2=$pts[($i+1)%$pts.Count]
    if([math]::Abs($p1.y-$p2.y) -lt 1e-9){continue}
    if($p1.y -lt $p2.y){$a=$p1;$b=$p2}else{$a=$p2;$b=$p1}
    $dx=($b.x-$a.x)/($b.y-$a.y)
    $edges += [PSCustomObject]@{ymin=[math]::Floor($a.y); ymax=[math]::Ceiling($b.y); x=[double]$a.x; dx=$dx}
  }
  for($y=0;$y -lt $h;$y++){
    $active = $edges.Where({$_.ymin -le $y -and $_.ymax -gt $y})
    foreach($e in $active){ $e.x += $e.dx }
    $sorted = $active | Sort-Object x
    for($i=0;$i +1 -lt $sorted.Count;$i+=2){
      $xa=[math]::Max(0,[math]::Ceiling($sorted[$i].x-1e-6)); $xb=[math]::Min($w-1,[math]::Floor($sorted[$i+1].x+1e-6))
      if($xa -le $xb){ & $FillSpan $buf $w $y $xa $xb $c.b $c.g $c.r $c.a }
    }
  }
}

# ---------- PNG ----------
function Crc32($bytes){
  $table = [System.Collections.ArrayList]::new()
  for($i=0;$i -lt 256;$i++){
    $c=$i; for($j=0;$j -lt 8;$j++){ if($c -band 1){$c = ($c -shr 1) -bxor 0xEDB88320}else{$c = $c -shr 1} }
    $table.Add($c) > $null
  }
  $crc = 0xFFFFFFFF
  foreach($b in $bytes){ $crc = ($crc -shr 8) -bxor $table[($crc -bxor $b) -band 0xFF] }
  return $crc -bxor 0xFFFFFFFF
}
function Write-Uint32BE($stream,$v){
  $stream.Write([byte](($v -shr 24)-band0xFF),0,1)
  $stream.Write([byte](($v -shr 16)-band0xFF),0,1)
  $stream.Write([byte](($v -shr 8)-band0xFF),0,1)
  $stream.Write([byte]($v-band0xFF),0,1)
}
function Chunk($stream,$type,$data){
  $mem = [System.IO.MemoryStream]::new()
  Write-Uint32BE $mem $data.Length
  $tb = [System.Text.Encoding]::ASCII.GetBytes($type); $mem.Write($tb,0,4)
  $mem.Write($data,0,$data.Length)
  Write-Uint32BE $mem (Crc32 ($tb + $data))
  $stream.Write($mem.ToArray(),0,$mem.Length)
}
function Encode-Png($w,$h,$buf){
  $ms = [System.IO.MemoryStream]::new()
  $ms.Write([byte[]]@(0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A),0,8)
  $ihdr = [byte[]]::new(13)
  $ihdr[0]=($w -shr 24)-band0xFF; $ihdr[1]=($w -shr 16)-band0xFF; $ihdr[2]=($w -shr 8)-band0xFF; $ihdr[3]=$w-band0xFF
  $ihdr[4]=($h -shr 24)-band0xFF; $ihdr[5]=($h -shr 16)-band0xFF; $ihdr[6]=($h -shr 8)-band0xFF; $ihdr[7]=$h-band0xFF
  $ihdr[8]=8; $ihdr[9]=6; $ihdr[10]=0; $ihdr[11]=0; $ihdr[12]=0
  Chunk $ms "IHDR" $ihdr
  $scan = [byte[]]::new(($w*4+1)*$h); $pi=0
  for($y=0;$y -lt $h;$y++){
    $scan[$pi++]=0
    for($x=0;$x -lt $w;$x++){ $i=($y*$w+$x)*4; $scan[$pi++]=$buf[$i+2]; $scan[$pi++]=$buf[$i+1]; $scan[$pi++]=$buf[$i]; $scan[$pi++]=$buf[$i+3] }
  }
  $comp = [System.IO.MemoryStream]::new()
  $def = [System.IO.Compression.DeflateStream]::new($comp,[System.IO.Compression.CompressionMode]::Compress, $true)
  $def.Write($scan,0,$scan.Length); $def.Close(); $def.Dispose()
  $raw = $comp.ToArray()
  $a=1;$b=0
  foreach($x in $raw){ $a=($a+$x)%65521; $b=($b+$a)%65521 }
  $adler = (($b -shl 16) -bor $a) -band 0xFFFFFFFF
  $zlib = [byte[]]::new($raw.Length+6); $zlib[0]=0x78; $zlib[1]=0x9C
  [System.Array]::Copy($raw,0,$zlib,2,$raw.Length)
  $zlib[$zlib.Length-4]=(($adler -shr 24)-band0xFF); $zlib[$zlib.Length-3]=(($adler -shr 16)-band0xFF)
  $zlib[$zlib.Length-2]=(($adler -shr 8)-band0xFF); $zlib[$zlib.Length-1]=$adler-band0xFF
  Chunk $ms "IDAT" $zlib
  Chunk $ms "IEND" $empty
  return $ms.ToArray()
}
$empty = [byte[]]::new(0)
function Save-Png($path,$w,$h,$buf){ [System.IO.File]::WriteAllBytes($path,(Encode-Png $w $h $buf)) }

# ---------- palette ----------
$INK900   = @{r=20;g=16;b=13;a=255}
$PAPER100 = @{r=242;g=234;b=219;a=255}
$BRASS400 = @{r=200;g=164;b=104;a=255}
$EMBER500 = @{r=212;g=73;b=42;a=255}

# эмблема: голова 13-точечный полигон + звезда «Полярная»
$headPts = @(
  @{x=60;y=88},@{x=43;y=82},@{x=36;y=60},@{x=46;y=46},@{x=52;y=34},@{x=60;y=30},@{x=68;y=34},
  @{x=74;y=46},@{x=84;y=60},@{x=77;y=82},@{x=62;y=78},@{x=60;y=81},@{x=58;y=78}
)
$starPts = @(
  @{x=60;y=18.6},@{x=61.2;y=21.6},@{x=64.5;y=24},@{x=61.2;y=26.4},@{x=60;y=29.4},
  @{x=58.8;y=26.4},@{x=55.5;y=24},@{x=58.8;y=21.6}
)
function Draw-Emblem($buf,$w,$h,$cx,$cy,$s,$headC,$starC){
  $pts = @(); foreach($p in $headPts){ $pts += @{x=$cx+$p.x*$s; y=$cy+$p.y*$s} }
  Fill-Polygon $buf $w $h $pts $headC
  $s2 = @(); foreach($p in $starPts){ $s2 += @{x=$cx+$p.x*$s; y=$cy+$p.y*$s} }
  Fill-Polygon $buf $w $h $s2 $starC
}

# ---------- avatars 640x640 ----------
foreach($name in @("avatar-telegram.png","avatar-vk.png","avatar-max.png")){
  $w=640;$h=640;$buf = New-Buffer $w $h
  Fill-Rect $buf $w $h 0 0 $w $h $INK900
  $cx=320;$cy=320
  Stroke-Circle $buf $w $h $cx $cy 286 14 $BRASS400
  Fill-Circle $buf $w $h $cx $cy 240 $INK900
  Stroke-Circle $buf $w $h $cx $cy 240 2 $BRASS400
  Draw-Emblem $buf $w $h $cx 296 2.05 $PAPER100 $EMBER500
  Save-Png "$brand\$name" $w $h $buf
  Write-Host "wrote $name"
}

# ---------- favicon 32x32 ----------
function Make-Favicon($path,$w){
  $buf = New-Buffer $w $w
  Fill-Rect $buf $w $w 0 0 $w $w $INK900
  $cx=$w/2;$cy=$w/2
  $r=[math]::Floor($w*0.42); Stroke-Circle $buf $w $w $cx $cy $r 3 $BRASS400
  Fill-Circle $buf $w $w $cx $cy $([math]::Floor($r*0.72)) $INK900
  Draw-Emblem $buf $w $w $cx $cy ($w/62) $PAPER100 $EMBER500
  Save-Png $path $w $w $buf
}
Make-Favicon "$brand\favicon-32.png" 32

# ---------- apple / icons ----------
foreach($x in @(@{name="apple-touch-icon.png";w=180},@{name="icon-192.png";w=192},@{name="icon-512.png";w=512})){
  $w=$x.w;$h=$w;$buf=New-Buffer $w $h
  Fill-Rect $buf $w $h 0 0 $w $h $INK900
  $cx=$w/2;$cy=$w/2
  $r=[math]::Floor($w*0.44); $t=[math]::Max(2,[math]::Floor($w/40))
  Stroke-Circle $buf $w $h $cx $cy $r $t $BRASS400
  Fill-Circle $buf $w $h $cx $cy $([math]::Floor($r*0.78)) $INK900
  Stroke-Circle $buf $w $h $cx $cy $([math]::Floor($r*0.78)) 2 $BRASS400
  Draw-Emblem $buf $w $h $cx $cy ($w/60) $PAPER100 $EMBER500
  Save-Png "$brand\$($x.name)" $w $h $buf
  Write-Host "wrote $($x.name)"
}
# maskable-512: artwork scaled into center safe zone
$w=512;$h=512;$buf=New-Buffer $w $h
Fill-Rect $buf $w $h 0 0 $w $h $INK900
$cx=256;$cy=256
$r=[math]::Floor($w*0.30); Stroke-Circle $buf $w $h $cx $cy $r 4 $BRASS400
  Fill-Circle $buf $w $h $cx $cy $([math]::Floor($r*0.85)) $INK900
Draw-Emblem $buf $w $h $cx $cy ($w/90) $PAPER100 $EMBER500
Save-Png "$brand\maskable-512.png" $w $h $buf
Write-Host "wrote maskable-512.png"

# ---------- og-default 1200x630 ----------
$w=1200;$h=630;$buf=New-Buffer $w $h
Fill-Rect $buf $w $h 0 0 $w $h $INK900
$cx=600;$cy=330
$r=215; Stroke-Circle $buf $w $h $cx $cy $r 20 $BRASS400
  Fill-Circle $buf $w $h $cx $cy $([math]::Floor($r*0.82)) $INK900
  Stroke-Circle $buf $w $h $cx $cy $([math]::Floor($r*0.82)) 3 $BRASS400
Draw-Emblem $buf $w $h $cx $cy 3.4 $PAPER100 $EMBER500
  Fill-Circle $buf $w $h ($cx-40) $([math]::Floor($cy+205)) 5 $BRASS400
  Fill-Circle $buf $w $h $cx $([math]::Floor($cy+205)) 5 $BRASS400
  Fill-Circle $buf $w $h ($cx+40) $([math]::Floor($cy+205)) 5 $BRASS400
Save-Png "$brand\og-default.png" $w $h $buf
Write-Host "wrote og-default.png"

# ---------- favicon.ico (32x32 + 16x16, 32bpp BMP) ----------
function Write-Uint32LE($bw,$v){ $bw.Write([byte]($v-band0xFF)); $bw.Write([byte](($v -shr 8)-band0xFF)); $bw.Write([byte](($v -shr 16)-band0xFF)); $bw.Write([byte](($v -shr 24)-band0xFF)) }
function Make-FaviconBuf($w){
  $buf = New-Buffer $w $w
  Fill-Rect $buf $w $w 0 0 $w $w $INK900
  $cx=$w/2;$cy=$w/2
  $r=[math]::Floor($w*0.42); Stroke-Circle $buf $w $w $cx $cy $r 2 $BRASS400
  Draw-Emblem $buf $w $w $cx $cy ($w/70) $PAPER100 $EMBER500
  return $buf
}
$ico = [System.IO.MemoryStream]::new(); $bw = [System.IO.BinaryWriter]::new($ico)
$bw.Write([uint16]0); $bw.Write([uint16]1); $bw.Write([uint16]2)
$sizes = @(32,16)
$off = 6 + 16*$sizes.Count
$imgs = @{}
foreach($w in $sizes){
  $imgs[$w] = Make-FaviconBuf $w
  $bw.Write([byte]$w); $bw.Write([byte]$w); $bw.Write([byte]0); $bw.Write([byte]0)
  $bw.Write([uint16]1); $bw.Write([uint16]32); Write-Uint32LE $bw $imgs[$w].Length; Write-Uint32LE $bw $off
  $off += 14 + 40 + $w*4*$w
}
foreach($w in $sizes){
  $buf=$imgs[$w]; $stride=$w*4
  $bw.Write([byte]0x42); $bw.Write([byte]0x4D)
  Write-Uint32LE $bw $(14+40+$stride*$w); $bw.Write([uint16]0); $bw.Write([uint16]0); Write-Uint32LE $bw 14
  Write-Uint32LE $bw 40; Write-Uint32LE $bw $w; Write-Uint32LE $bw $w
  $bw.Write([uint16]1); $bw.Write([uint16]32); Write-Uint32LE $bw 0; Write-Uint32LE $bw $(($stride*$w))
  Write-Uint32LE $bw 0; Write-Uint32LE $bw 0; Write-Uint32LE $bw 0; Write-Uint32LE $bw 0
  for($y=$w-1;$y -ge 0;$y--){ for($x=0;$x -lt $w;$x++){ $i=($y*$w+$x)*4; $bw.Write($buf[$i]); $bw.Write($buf[$i+1]); $bw.Write($buf[$i+2]); $bw.Write($buf[$i+3]) } }
}
$bw.Flush()
[System.IO.File]::WriteAllBytes("$brand\favicon.ico",$ico.ToArray())
Write-Host "wrote favicon.ico"

# ---------- design-review скриншоты знака на фонах и размерах ----------
$review = "C:\Users\nu11\Documents\GitHub\Olenevod\docs\design-review"
New-Item -ItemType Directory -Path $review -Force | Out-Null
function Review-Logo($name,$w,$bg,$head,$star){
  $buf=New-Buffer $w $w
  Fill-Rect $buf $w $w 0 0 $w $w $bg
  $cx=$w/2;$cy=$w/2
  $r=[math]::Floor($w*0.44); $t=[math]::Max(2,[math]::Floor($w/40))
  Stroke-Circle $buf $w $w $cx $cy $r $t $BRASS400
  Fill-Circle $buf $w $w $cx $cy $([math]::Floor($r*0.78)) $bg
  Stroke-Circle $buf $w $w $cx $cy $([math]::Floor($r*0.78)) 2 $BRASS400
  Draw-Emblem $buf $w $w $cx $cy ($w/60) $head $star
  Save-Png "$review\$name" $w $w $buf
  Write-Host "wrote $review\$name"
}
foreach($w in @(32,120,640)){
  Review-Logo ("review-logo-dark-$w.png") $w $INK900 $PAPER100 $EMBER500
  Review-Logo ("review-logo-light-$w.png") $w $PAPER100 $INK900 $EMBER500
}
Write-Host "ALL PNG DONE"
