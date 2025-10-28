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
}