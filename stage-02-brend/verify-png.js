const fs = require("fs")
const p = require("path")
const dir = "C:\\Users\\nu11\\Documents\\GitHub\\Olenevod\\olenevod\\brand"
for (const x of fs.readdirSync(dir)) {
  if (!(x.endsWith(".png") || x.endsWith(".ico"))) continue
  const b = fs.readFileSync(p.join(dir, x))
  const okPng = b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4E && b[3] === 0x47
  const w = okPng ? b.readUInt32BE(16) : null
  const h = okPng ? b.readUInt32BE(20) : null
  console.log(x, okPng ? "PNG OK" : "ICO  ", w && h ? w + "x" + h : "")
}
