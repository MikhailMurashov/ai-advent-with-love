import { create } from 'zustand'

interface Notification {
  id: string
  content: string
}

interface NotificationState {
  notifications: Notification[]
  addNotification: (content: string) => void
  removeNotification: (id: string) => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  addNotification: (content) =>
    set((state) => ({
      notifications: [...state.notifications, { id: crypto.randomUUID(), content }],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}))
