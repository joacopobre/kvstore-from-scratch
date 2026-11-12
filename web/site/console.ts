import { el } from './dom'
import { setSwitch } from './switch'
const CONSOLE_NAV_HTML = `
  <div role="group">
    <div id="console-navbar" class="relative flex rounded-full bg-black/5 p-1 ">
      <span data-pill class="absolute left-1 top-1 bottom-1 rounded-full bg-white shadow-sm
                             transition-all duration-300 ease-out motion-reduce:transition-none"></span>
      <button type="button" data-value="set" class="relative cursor-pointer px-5 py-2 text-sm font-medium">Set</button>
      <button type="button" data-value="get" class="relative cursor-pointer px-5 py-2 text-sm font-medium">Get</button>
      <button type="button" data-value="delete"   class="relative cursor-pointer px-5 py-2 text-sm font-medium">Delete</button>
    </div>
  </div>
  
`
type ApiResult = { status: number; data: unknown }

let op = 'set'
export function renderConsoleNav() {
  document.getElementById('console-nav')!.innerHTML = CONSOLE_NAV_HTML
}

export function syncConsoleSwitch() {
  const nav = document.getElementById('console-nav')
  if (!nav) return
  setSwitch(nav, op)
}

function selectOp(newOp: string) {
  op = newOp
  const bar = document.getElementById('console-navbar')
  if (!bar) return
  setSwitch(bar, op)

  const needsValue = newOp === 'set'
  const wrapper = document.getElementById('value-wrapper')
  const inner = wrapper?.querySelector('#value-inner')
  if (!inner || !wrapper) return

  wrapper.classList.toggle('grid-rows-[1fr]', needsValue)
  wrapper.classList.toggle('grid-rows-[0fr]', !needsValue)

  inner.classList.toggle('opacity-0', !needsValue)

  wrapper.inert = !needsValue
}

export function consoleInit() {
  const consoleForm = document.getElementById('console-form')
  consoleForm?.addEventListener('submit', (e) => {
    e.preventDefault()
    run()
  })
  renderConsoleNav()
  const bar = document.getElementById('console-navbar')
  const opOptions = bar?.querySelectorAll<HTMLElement>('[data-value]')
  if (!opOptions) return
  for (const option of opOptions) {
    option.addEventListener('click', () => {
      const val = option.dataset.value
      if (!val) return
      selectOp(val)
    })
  }
}

async function run() {
  const key = el<HTMLInputElement>('key')
  const keyText = key.value
  const value = el<HTMLInputElement>('value')
  const valueText = value.value
  const out = el<HTMLElement>('out')
  if (!key.value) {
    out.textContent = 'Need a key to run the operation'
    return
  }
  const method = op === 'get' ? 'GET' : 'POST'

  const path =
    op === 'get'
      ? `/api/${op}?key=${encodeURIComponent(keyText)}`
      : `/api/${op}`

  let body: object | undefined
  if (op === 'set') {
    body = { key: keyText, value: valueText }
  } else if (op === 'delete') {
    body = { key: keyText }
  }

  const result = await request(method, path, body)
  out.textContent = JSON.stringify(result)
}

async function request(
  method: string,
  path: string,
  body?: object
): Promise<ApiResult> {
  const options: RequestInit = { method }
  if (body) {
    options.headers = { 'Content-Type': 'application/json' }
    options.body = JSON.stringify(body)
  }
  let res
  let data: unknown = null
  try {
    res = await fetch(path, options)
    try {
      data = await res.json()
    } catch {} // not JSON: leave data as null
  } catch {
    return { status: 0, data: { error: 'could not reach the server' } }
  }
  return { status: res.status, data }
}
