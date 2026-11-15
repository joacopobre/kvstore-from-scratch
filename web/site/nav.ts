import { setSwitch } from './switch'
const NAV_HTML = `
  <nav aria-label="Pages">
    <div id="navbar" class="relative flex rounded-full border border-line bg-paper/80 p-1 shadow-[0_1px_2px_rgb(0_0_0/0.04)] backdrop-blur-md">
      <span data-pill class="absolute left-0 top-1 bottom-1 rounded-full bg-soft ring-1 ring-line
                             transition-[transform,width] duration-300 ease-out motion-reduce:transition-none"></span>
      <a href="#project" data-value="project" class="relative rounded-full px-4 py-1.5 text-[13px] leading-5 font-medium text-muted transition-colors hover:text-ink motion-reduce:transition-none">Project</a>
      <a href="#console" data-value="console" class="relative rounded-full px-4 py-1.5 text-[13px] leading-5 font-medium text-muted transition-colors hover:text-ink motion-reduce:transition-none">Console</a>
      <a href="#about"   data-value="about"   class="relative rounded-full px-4 py-1.5 text-[13px] leading-5 font-medium text-muted transition-colors hover:text-ink motion-reduce:transition-none">About</a>
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
