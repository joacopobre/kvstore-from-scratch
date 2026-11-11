import { setSwitch } from './switch'
const NAV_HTML = `
  <nav class="sticky top-4 z-10 mx-auto mt-4 w-fit">
    <div id="navbar" class="relative flex rounded-full bg-black/5 p-1 backdrop-blur">
      <span data-pill class="absolute left-1 top-1 bottom-1 rounded-full bg-white shadow-sm
                             transition-all duration-300 ease-out motion-reduce:transition-none"></span>
      <a href="#project" data-value="project" class="relative px-5 py-2 text-sm font-medium">Project</a>
      <a href="#console" data-value="console" class="relative px-5 py-2 text-sm font-medium">Console</a>
      <a href="#about"   data-value="about"   class="relative px-5 py-2 text-sm font-medium">About</a>
    </div>
  </nav>
`

export function renderNav() {
  document.getElementById('nav-root')!.innerHTML = NAV_HTML
}

export function movePill(name: string) {
  const nav = document.getElementById('navbar')
  if (!nav) return
  setSwitch(nav, name)
}
