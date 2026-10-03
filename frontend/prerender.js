// Turns the built SPA into one HTML file per address, so a crawler reads every
// public page's words without running any JavaScript. Runs after both builds:
// dist/ holds the browser bundle and its index.html, dist-ssr/ the same app
// compiled for Node.
//
// It writes:
//   dist/index.html, dist/<page>/index.html  each public page, drawn in full
//   dist/<app route>/index.html              an empty shell marked noindex
//   dist/404.html                            the not-found page, noindex
//   dist/sitemap.xml                         every public page
//
// main.py serves exactly these files and answers anything else with 404.html
// and a 404 status, so the router is the one list of real addresses.
import fs from 'node:fs'
import path from 'node:path'
import { questions, render, router } from './dist-ssr/entry-server.js'

const SITE = 'https://calnio.myroslavrepin.com'

const template = fs.readFileSync('dist/index.html', 'utf8')

// Makes a string safe inside an HTML attribute or element.
function escapeHtml(text) {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
}

// The absolute address a page is known by. The root keeps its slash, nothing
// else carries one.
function canonicalFor(address) {
  if (address === '/') {
    return SITE + '/'
  }
  return SITE + address
}

// The structured data a page carries, or null. It is built from the same
// strings the page shows, so it can never claim what the page does not.
function schemaFor(address, meta) {
  if (address === '/') {
    return {
      '@context': 'https://schema.org',
      '@type': 'SoftwareApplication',
      name: 'Calnio',
      applicationCategory: 'ProductivityApplication',
      operatingSystem: 'Web',
      url: canonicalFor('/'),
      description: meta.description,
      offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
    }
  }
  if (address === '/faq') {
    return {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: questions.map(function (entry) {
        return {
          '@type': 'Question',
          name: entry.question,
          acceptedAnswer: { '@type': 'Answer', text: entry.answer.join(' ') },
        }
      }),
    }
  }
  return null
}

// The tags a public page needs in its head: its own title, description,
// canonical address and share card text.
function publicHead(address, meta) {
  const canonical = canonicalFor(address)
  const lines = [
    '<title>' + escapeHtml(meta.title) + '</title>',
    '<meta name="description" content="' + escapeHtml(meta.description) + '" />',
    '<link rel="canonical" href="' + canonical + '" />',
    '<meta property="og:title" content="' + escapeHtml(meta.title) + '" />',
    '<meta property="og:description" content="' + escapeHtml(meta.description) + '" />',
    '<meta property="og:url" content="' + canonical + '" />',
  ]

  const schema = schemaFor(address, meta)
  if (schema) {
    // A "<" inside the JSON could close the script tag early, so it is escaped.
    const json = JSON.stringify(schema).replaceAll('<', '\\u003c')
    lines.push('<script type="application/ld+json">' + json + '</script>')
  }
  return lines.join('\n    ')
}

// The tags a page crawlers must leave out of the index needs.
function privateHead(title) {
  return '<title>' + escapeHtml(title) + '</title>\n    <meta name="robots" content="noindex" />'
}

// The template with this page's head tags and body markup filled in.
function fillTemplate(head, body) {
  if (!template.includes('<!--head-->') || !template.includes('<div id="app"></div>')) {
    throw new Error('dist/index.html lost its <!--head--> or <div id="app"></div> marker')
  }
  return template
    .replace('<!--head-->', head)
    .replace('<div id="app"></div>', '<div id="app">' + body + '</div>')
}

// Writes one page where main.py looks for it: dist/index.html for the root,
// dist/<address>/index.html for everything else.
function writePage(address, html) {
  const directory = path.join('dist', address)
  fs.mkdirSync(directory, { recursive: true })
  fs.writeFileSync(path.join(directory, 'index.html'), html)
}

// Every fixed address the router knows. A parent and its '' child share one,
// and the not-found pattern is not an address.
const addresses = []
router.getRoutes().forEach(function (record) {
  if (record.path.includes(':')) {
    return
  }
  if (addresses.includes(record.path)) {
    return
  }
  addresses.push(record.path)
})

const sitemapEntries = []

for (const address of addresses) {
  const resolved = router.resolve(address)

  // An app page: drawn in the browser once the user is known.
  if (!resolved.meta.public) {
    writePage(address, fillTemplate(privateHead('Calnio'), ''))
    console.log('shell     ' + address)
    continue
  }

  // A public page: drawn in full, indexed, listed in the sitemap.
  const result = await render(address)
  writePage(address, fillTemplate(publicHead(address, result.route.meta), result.html))
  sitemapEntries.push(
    '  <url>\n' +
      '    <loc>' + canonicalFor(address) + '</loc>\n' +
      '    <lastmod>' + result.route.meta.updated + '</lastmod>\n' +
      '  </url>',
  )
  console.log('prerender ' + address)
}

// The not-found page, served by main.py with a 404 status for any unknown path.
const missing = await render('/404')
fs.writeFileSync('dist/404.html', fillTemplate(privateHead(missing.route.meta.title), missing.html))
console.log('prerender 404.html')

fs.writeFileSync(
  'dist/sitemap.xml',
  '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    sitemapEntries.join('\n') +
    '\n</urlset>\n',
)
console.log('sitemap   ' + sitemapEntries.length + ' pages')

// The Node build has done its job and must not ship.
fs.rmSync('dist-ssr', { recursive: true, force: true })
