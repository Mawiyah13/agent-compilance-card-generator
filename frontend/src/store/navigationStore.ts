import { create } from 'zustand'

type PageType = 'dashboard' | 'editor' | 'details' | 'diff' | 'audit' | 'login' | 'register'

interface NavigationState {
  currentPage: PageType
  selectedCardId: string | null
  diffParams: { cardId: string; v1: string; v2: string } | null
  navigateTo: (page: PageType, cardId?: string | null, diff?: { cardId: string; v1: string; v2: string } | null) => void
}

export const useNavigationStore = create<NavigationState>((set) => ({
  currentPage: 'login',
  selectedCardId: null,
  diffParams: null,
  navigateTo: (page, cardId = null, diff = null) => {
    set({
      currentPage: page,
      selectedCardId: cardId,
      diffParams: diff
    })
  }
}))
