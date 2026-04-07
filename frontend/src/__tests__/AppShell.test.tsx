import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import { AppShell, BottomNav } from '../components/layout/AppShell'

function renderWithRouter(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AppShell />
    </MemoryRouter>,
  )
}

describe('AppShell — TopNav', () => {
  it('renders all 4 nav items in the top nav', () => {
    renderWithRouter('/')

    // All 4 tabs should appear — TopNav has nav links for desktop
    const navLinks = screen.getAllByRole('link', { name: /dashboard|records|insights|passport/i })
    // TopNav + BottomNav each render 4 links = 8 total
    expect(navLinks.length).toBeGreaterThanOrEqual(4)

    const labels = navLinks.map((l) => l.textContent?.trim())
    expect(labels).toEqual(expect.arrayContaining(['Dashboard', 'Records', 'Insights', 'Passport']))
  })

  it('does not include the old Timeline or Charts tabs', () => {
    renderWithRouter('/')

    const timelineLinks = screen.queryAllByRole('link', { name: /timeline/i })
    expect(timelineLinks).toHaveLength(0)

    const chartsLinks = screen.queryAllByRole('link', { name: /charts/i })
    expect(chartsLinks).toHaveLength(0)
  })
})

describe('AppShell — BottomNav', () => {
  it('renders exactly 4 tabs', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <BottomNav />
      </MemoryRouter>,
    )

    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(4)
  })

  it('applies teal-600 active color class to Dashboard when on /', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <BottomNav />
      </MemoryRouter>,
    )

    // The Dashboard link label should carry the active teal color
    const dashLabel = screen.getByText('Dashboard')
    expect(dashLabel.className).toContain('text-teal-600')
  })

  it('applies inactive slate-400 color to non-active tabs', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <BottomNav />
      </MemoryRouter>,
    )

    const recordsLabel = screen.getByText('Records')
    expect(recordsLabel.className).toContain('text-slate-400')
  })

  it('bottom nav has md:hidden class so it is hidden on desktop breakpoint', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/']}>
        <BottomNav />
      </MemoryRouter>,
    )

    const nav = container.querySelector('nav')
    expect(nav?.className).toContain('md:hidden')
  })
})
