import './style.css'
import { renderNav, movePill } from './nav'
import { initToc } from './toc'
export {}

renderNav()

function el<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id)
  if (node === null) throw new Error(`missing #${id}`)
  return node as T
}

const keyInput = el<HTMLInputElement>('key')
const valueInput = el<HTMLInputElement>('value')
const out = el<HTMLElement>('out')

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
}

window.addEventListener('hashchange', showPage)
showPage()

async function getKey() {
  const response = await fetch(
    `/api/get?key=${encodeURIComponent(keyInput.value)}`
  )

  show(response)
}

async function setKey() {
  const response = await fetch('/api/set', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      key: keyInput.value,
      value: valueInput.value
    })
  })

  show(response)
}

async function deleteKey() {
  const response = await fetch(`/api/delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key: keyInput.value })
  })

  show(response)
}

async function show(response: Response) {
  const data = await response.json()
  out.textContent = `${response.status} ${JSON.stringify(data)}`
}

el('set').addEventListener('click', setKey)
el('delete').addEventListener('click', deleteKey)
el('get').addEventListener('click', getKey)
