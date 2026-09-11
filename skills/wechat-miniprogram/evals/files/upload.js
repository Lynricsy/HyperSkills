// ci/upload.js — 由 GitHub Actions 在每次 main 合并后执行
const ci = require('miniprogram-ci')
const fs = require('fs')
const pkg = require('../package.json')

const PRIVATE_KEY = process.env.MP_PRIVATE_KEY || 'REDACTED'

async function main() {
  fs.writeFileSync('/tmp/private.key', PRIVATE_KEY)

  const project = new ci.Project({
    appid: 'wxREDACTEDappid01',
    type: 'miniprogram',
    projectPath: process.cwd(),
    privateKey: '/tmp/private.key',
  })

  const preview = await ci.preview({
    project,
    desc: `preview ${process.env.GITHUB_SHA}`,
    setting: { es6: true, minify: true },
    qrcodeFormat: 'image',
  })
  console.log('preview ok', preview)

  const result = await ci.upload({
    project,
    version: pkg.version,
    desc: process.env.GITHUB_REF_NAME,
    robot: 42,
    setting: { es6: true, minify: true, autoPrefixWXSS: true },
    onProgressUpdate: console.log,
  })

  const total = result.subPackageInfo.find((p) => p.name === '__FULL__')
  if (total.size > 2 * 1024 * 1024) {
    throw new Error('package too large')
  }

  console.log('uploaded, now submitting for review')
  await ci.submitAudit({ project, version: pkg.version })
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
