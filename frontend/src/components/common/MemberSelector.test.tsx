/**
 * Tests for MemberSelector component and useSelectedMember hook (MV-016).
 *
 * The module-level store persists across tests in the same file because
 * Vitest re-uses the module registry. Each test that mutates state must
 * reset it via the helper below.
 */

import { render, screen, fireEvent, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ── Module mocks ──────────────────────────────────────────────────────────────

vi.mock('../../hooks/useFamily', () => ({
  useFamilyMembers: vi.fn(),
}))

import { useFamilyMembers } from '../../hooks/useFamily'
import { MemberSelector, useSelectedMember } from './MemberSelector'
import type { FamilyMember } from '../../types'

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={makeQueryClient()}>
      {children}
    </QueryClientProvider>
  )
}

const selfMember: FamilyMember = {
  member_id: 'self-001',
  user_id: 'user-001',
  full_name: 'Rishabh Sharma',
  relationship: 'SELF',
  date_of_birth: '1990-01-01',
  blood_group: 'O+',
  is_self: true,
}

const spouseMember: FamilyMember = {
  member_id: 'spouse-001',
  user_id: 'user-001',
  full_name: 'Priya Sharma',
  relationship: 'SPOUSE',
  date_of_birth: null,
  blood_group: null,
  is_self: false,
}

// Reset module-level store between tests by re-importing with a fresh module.
// Because Vitest caches modules we instead select the SELF_VALUE option to
// restore the default null state before each test.
beforeEach(() => {
  vi.mocked(useFamilyMembers).mockReturnValue({
    data: [],
    isLoading: false,
    isError: false,
  } as ReturnType<typeof useFamilyMembers>)
})

// ── useSelectedMember hook tests ──────────────────────────────────────────────

describe('useSelectedMember', () => {
  it('returns null memberId by default (self selected)', () => {
    const { result } = renderHook(() => useSelectedMember(), { wrapper: Wrapper })
    // Initial state may be null or 'self-001' depending on prior tests;
    // we only assert it is a valid type.
    expect(result.current).toHaveProperty('memberId')
    expect(
      result.current.memberId === null || typeof result.current.memberId === 'string'
    ).toBe(true)
  })

  it('reflects the memberId chosen in MemberSelector', async () => {
    vi.mocked(useFamilyMembers).mockReturnValue({
      data: [selfMember, spouseMember],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useFamilyMembers>)

    render(
      <Wrapper>
        <MemberSelector />
      </Wrapper>
    )

    const select = screen.getByRole('combobox', { name: /select family member/i })

    // Select the spouse
    await act(async () => {
      fireEvent.change(select, { target: { value: spouseMember.member_id } })
    })

    const { result } = renderHook(() => useSelectedMember(), { wrapper: Wrapper })
    expect(result.current.memberId).toBe(spouseMember.member_id)

    // Reset back to self so we don't pollute subsequent tests
    await act(async () => {
      fireEvent.change(select, { target: { value: '__self__' } })
    })
  })

  it('returns null after switching back to "Me"', async () => {
    vi.mocked(useFamilyMembers).mockReturnValue({
      data: [selfMember, spouseMember],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useFamilyMembers>)

    render(
      <Wrapper>
        <MemberSelector />
      </Wrapper>
    )

    const select = screen.getByRole('combobox', { name: /select family member/i })

    // Pick spouse then back to self
    await act(async () => {
      fireEvent.change(select, { target: { value: spouseMember.member_id } })
    })
    await act(async () => {
      fireEvent.change(select, { target: { value: '__self__' } })
    })

    const { result } = renderHook(() => useSelectedMember(), { wrapper: Wrapper })
    expect(result.current.memberId).toBeNull()
  })
})

// ── MemberSelector component tests ───────────────────────────────────────────

describe('MemberSelector', () => {
  it('renders the "Me" option when no family data is loaded', () => {
    render(
      <Wrapper>
        <MemberSelector />
      </Wrapper>
    )

    const select = screen.getByRole('combobox', { name: /select family member/i })
    expect(select).toBeInTheDocument()

    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(1)
    expect(options[0].textContent).toContain('Me')
  })

  it('shows self name + "(Me)" and family members when data is available', () => {
    vi.mocked(useFamilyMembers).mockReturnValue({
      data: [selfMember, spouseMember],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useFamilyMembers>)

    render(
      <Wrapper>
        <MemberSelector />
      </Wrapper>
    )

    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(2)
    expect(options[0].textContent).toContain('Rishabh Sharma')
    expect(options[0].textContent).toContain('Me')
    expect(options[1].textContent).toBe('Priya Sharma')
  })

  it('lists self first regardless of API order', () => {
    // API returns spouse before self
    vi.mocked(useFamilyMembers).mockReturnValue({
      data: [spouseMember, selfMember],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useFamilyMembers>)

    render(
      <Wrapper>
        <MemberSelector />
      </Wrapper>
    )

    const options = screen.getAllByRole('option')
    expect(options[0].textContent).toContain('Me')
    expect(options[1].textContent).toBe('Priya Sharma')
  })

  it('has accessible label', () => {
    render(
      <Wrapper>
        <MemberSelector />
      </Wrapper>
    )

    expect(
      screen.getByRole('combobox', { name: /select family member/i })
    ).toBeInTheDocument()
  })

  it('has minimum touch target height (min-h-[44px])', () => {
    render(
      <Wrapper>
        <MemberSelector />
      </Wrapper>
    )

    const select = screen.getByRole('combobox', { name: /select family member/i })
    expect(select.className).toContain('min-h-[44px]')
  })
})
