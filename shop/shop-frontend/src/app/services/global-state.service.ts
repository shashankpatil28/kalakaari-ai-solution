// shop-frontend/src/app/services/global-state.service.ts
import { Injectable, signal } from '@angular/core';

export interface ToastMessage {
  message: string;
  type: 'success' | 'error' | 'info';
}

@Injectable({
  providedIn: 'root'
})
export class GlobalStateService {

  // Global state signal for a toast notification
  public readonly toast = signal<ToastMessage | null>(null);

  /**
   * Shows a toast message for a few seconds.
   * @param message The message to display.
   * @param type The type of toast (success, error, info) for styling.
   * @param duration How long to show the toast in milliseconds.
   */
  public showToast(message: string, type: 'success' | 'error' | 'info' = 'info', duration: number = 3000): void {
    // Set the toast message
    this.toast.set({ message, type });

    // Clear the toast message after the duration
    setTimeout(() => {
      this.toast.set(null);
    }, duration);
  }

  // You can add more global state signals here as needed
  // public readonly isLoading = signal<boolean>(false);
  // public readonly cartItems = signal<any[]>([]);
}