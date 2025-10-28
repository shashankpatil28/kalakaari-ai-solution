# shop/shop-frontend/src/app/auth/auth.guard.ts
// shop/shop-frontend/src/app/auth/auth.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { map, take, tap } from 'rxjs/operators'; // Import RxJS operators

export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Use the authState$ observable
  return authService.authState$.pipe(
    take(1), // Take only the first emitted value (current auth state)
    map(user => !!user), // Map the user object (or null) to a boolean
    tap(isLoggedIn => {
      console.log('Auth Guard Check - Logged In:', isLoggedIn); // Add log
      if (!isLoggedIn) {
        console.log('Auth Guard: Not logged in, redirecting to /login');
        router.navigate(['/login']); // Use navigate for redirection within tap
      }
    })
  );
};