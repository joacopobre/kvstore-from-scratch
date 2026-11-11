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
}

export function consoleInit() {
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
