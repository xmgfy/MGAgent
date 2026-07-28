import { create } from 'zustand'

interface Toast {
  id: number
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
}

interface ToastStore {
  toasts: Toast[]
  showToast: (type: Toast['type'], message: string) => void
  removeToast: (id: number) => void
}

let toastId = 0

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  showToast: (type, message) => {
    const id = ++toastId
    set((state) => ({
      toasts: [...state.toasts, { id, type, message }],
    }))
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }))
    }, 4000)
  },
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}))

export const toast = {
  success: (message: string) => useToastStore.getState().showToast('success', message),
  error: (message: string) => useToastStore.getState().showToast('error', message),
  info: (message: string) => useToastStore.getState().showToast('info', message),
  warning: (message: string) => useToastStore.getState().showToast('warning', message),
}
