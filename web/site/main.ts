import './style.css'
import { renderNav, movePill } from './nav'
import { initToc } from './toc'
import { el } from './dom'
import { syncConsoleSwitch, consoleInit } from './console'
export {}

const pages = ['project', 'console', 'about']
const DEFAULT_PAGE = pages[0]

function showPage() {
  let name = location.hash.slice(1)
  if (!pages.includes(name)) {
    name = DEFAULT_PAGE
  }
  pages.forEach((p) => {
    el(p).hidden = p !== name
  })
  movePill(name)
  window.scrollTo({ top: 100, behavior: 'smooth' })
  initToc(name)
  if (name === 'console') syncConsoleSwitch()
}

window.addEventListener('hashchange', showPage)
renderNav()

consoleInit()
showPage()
