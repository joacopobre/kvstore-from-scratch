export function setSwitch(bar: HTMLElement, value: string) {
  const options = bar.querySelectorAll<HTMLElement>('[data-value]')
  const pill = bar.querySelector<HTMLElement>('[data-pill]')

  const match = [...options].find((p) => p.dataset.value === value)

  if (!match || !pill) return

  pill.style.width = `${match.offsetWidth}px`
  pill.style.transform = `translateX(${match.offsetLeft - 4}px)`

  for (const option of options) {
    const active = option.dataset.value === value
    option.classList.toggle('text-ink', active)
    option.classList.toggle('text-muted', !active)
  }
}
