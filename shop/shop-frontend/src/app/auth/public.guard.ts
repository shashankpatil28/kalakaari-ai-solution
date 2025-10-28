// shop-frontend/src/app/auth/public.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { map, take, tap } from 'rxjs/operators';
import { UiStateService } from '../services/ui-state.service'; // <-- IMPORT RENAMED SERVICE

export const publicGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const uiState = inject(UiStateService); // <-- INJECT RENAMED SERVICE

  return authService.authState$.pipe(
    take(1), // Get the current user state
    map(user => !user), // Invert the logic: allow if user is NOT logged in
    tap(isLoggedOut => {
      if (!isLoggedOut) {
        // User is logged in, redirect them
        console.log('Public Guard: User is already logged in, redirecting to /home');
        
        // Use the ui state service to show a notification
        uiState.showToast('You are already logged in.', 'info'); // <-- USE RENAMED SERVICE
        
        router.navigate(['/home']);
      } else {
        // User is logged out, allow them to see the login/signup page
        console.log('Public Guard: User is not logged in, allowing access.');
      }
    })
  );
};