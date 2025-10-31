// shop-frontend/src/app/services/user-state.service.ts
import { Injectable, computed, inject } from '@angular/core';
import { AuthService } from './auth.service';

/**
 * A global, read-only state service for user information.
 * This service acts as a clean "store" for the rest of the app to consume.
 * It gets its data from the AuthService, which remains the single source of truth.
 */
@Injectable({
  providedIn: 'root'
})
export class UserStateService {
  private authService = inject(AuthService);

  // Color mapping for avatar backgrounds
  private avatarColors = [
    '#3B82F6', // blue-500
    '#10B981', // emerald-500
    '#EF4444', // red-500
    '#F59E0B', // amber-500
    '#8B5CF6', // violet-500
    '#EC4899', // pink-500
    '#06B6D4', // cyan-500
  ];

  /**
   * A signal representing the currently authenticated user.
   * Sourced directly from the AuthService.
   */
  public readonly currentUser = this.authService.currentUser.asReadonly();

  /**
   * A computed signal that returns true if the user is logged in.
   */
  public readonly isLoggedIn = computed(() => !!this.currentUser());

  /**
   * A computed signal for the user's name (displayName or 'User').
   */
  public readonly greetingName = computed(() => this.currentUser()?.displayName || 'User');

  /**
   * A computed signal for the user's type.
   */
  public readonly userType = computed(() => this.currentUser()?.userType);

  /**
   * NEW: A computed signal for the user's first initial.
   */
  public readonly userInitial = computed(() => {
    return this.greetingName().charAt(0).toUpperCase() || '?';
  });

  /**
   * NEW: A computed signal for the user's avatar background color.
   * This provides a consistent color based on the first letter.
   */
  public readonly userAvatarColor = computed(() => {
    const charCode = this.userInitial().charCodeAt(0);
    return this.avatarColors[charCode % this.avatarColors.length];
  });
}