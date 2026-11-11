function buildToc(page: string) {
  const section = document.getElementById(page)
  const toc = section?.querySelector<HTMLElement>('[data-toc]')
  if (!section || !toc) return
  toc.innerHTML = ''
  const headings = section.querySelectorAll('h2')
  for (const heading of headings) {
    const link = document.createElement('a')
    link.textContent = heading.textContent
    link.dataset.target = heading.id
    link.className =
      'block cursor-pointer py-1 text-sm text-muted transition-colors'
    link.href = `#${heading.id}`
    link.addEventListener('click', (e) => {
      e.preventDefault()
      heading.scrollIntoView({ behavior: 'smooth' })
    })
    toc.append(link)
  }
}

function setActive(id: string) {
  const links = document.querySelectorAll<HTMLAnchorElement>('[data-toc] a')

  for (const link of links) {
    const active = link.dataset.target === id
    link.classList.toggle('text-ink', active)
    link.classList.toggle('text-muted', !active)

    link.classList.toggle('font-semibold', active)
    link.classList.toggle('normal', !active)
  }
}

let observer: IntersectionObserver | null = null
function watchHeadings(page: string) {
  if (observer) {
    observer.disconnect()
  }
  const section = document.getElementById(page)
  const headings = section?.querySelectorAll('h2')
  if (!headings) return
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          setActive(entry.target.id)
        }
      }
    },
    { rootMargin: '96px 0px -70% 0px' }
  )

  for (const heading of headings) {
    observer.observe(heading)
  }
}

export function initToc(page: string) {
  buildToc(page)
  watchHeadings(page)
}
