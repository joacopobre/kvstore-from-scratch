const NAV_HTML = `
  <nav class="sticky top-4 z-10 mx-auto mt-4 w-fit">
    <div id="navbar" class="relative flex rounded-full bg-black/5 p-1 backdrop-blur">
      <span id="pill" class="absolute left-1 top-1 bottom-1 rounded-full bg-white shadow-sm
                             transition-all duration-300 ease-out motion-reduce:transition-none"></span>
      <a href="#project" data-page="project" class="relative px-5 py-2 text-sm font-medium">Project</a>
      <a href="#console" data-page="console" class="relative px-5 py-2 text-sm font-medium">Console</a>
      <a href="#about"   data-page="about"   class="relative px-5 py-2 text-sm font-medium">About</a>
    </div>
  </nav>
`

export function renderNav() {
  document.getElementById('nav-root')!.innerHTML = NAV_HTML
}

export function movePill(name: string) {
  console.log('movePill', name)
  const links = document.querySelectorAll<HTMLAnchorElement>('#navbar a')
  const pill = document.getElementById('pill')

  const link = [...links].find((l) => l.dataset.page === name)

  if (!pill || !link) return

  pill.style.width = `${link.offsetWidth}px`
  pill.style.transform = `translateX(${link.offsetLeft - 4}px)`

  for (const link of links) {
    const active = link.dataset.page === name
    link.classList.toggle('text-ink', active)
    link.classList.toggle('text-muted', !active)
  }
}
