import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { ViewToggleBar } from './ViewToggleBar'

const mockUseAuth = vi.fn()

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

vi.mock('@/store/workspaceStore', () => ({
  useWorkspaceStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({
      activeViews: ['map', 'table'],
      toggleView: vi.fn(),
    }),
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('ViewToggleBar', () => {
  it('shows the Cesta toggle for agents', () => {
    mockUseAuth.mockReturnValue({ user: { role: 'agent' } })
    render(<ViewToggleBar />)
    expect(screen.getByRole('button', { name: /cesta/i })).toBeTruthy()
  })

  it('hides the Cesta toggle for citizens', () => {
    mockUseAuth.mockReturnValue({ user: { role: 'citizen' } })
    render(<ViewToggleBar />)
    expect(screen.queryByRole('button', { name: /cesta/i })).toBeNull()
  })
})
