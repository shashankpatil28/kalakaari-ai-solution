// shop/shop-frontend/src/app/components/login/login.component.ts
import { Component, NgZone } from '@angular/core'; // Import NgZone
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService, AppUser } from '../../services/auth.service'; // Import AppUser

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './login.component.html',
})
export class LoginComponent {
  email = '';
  password = '';
  message = '';
  loading = false;
  readonly agenticServiceUrl = 'https://agentic-service-978458840399.asia-southeast1.run.app/dev-ui/?app=agents'; // Define URL

  constructor(
    private auth: AuthService,
    private router: Router,
    private ngZone: NgZone // Inject NgZone
  ) {}

  async onLogin() {
    if (!this.email || !this.password) {
        this.message = 'Please enter both email and password.';
        return;
    }
    this.message = '';
    this.loading = true;
    try {
      const user = await this.auth.login(this.email, this.password);
      this.message = '✅ Login successful! Redirecting...';

      // Use NgZone for navigation to ensure it happens within Angular's context
      this.ngZone.run(() => {
        this.handleRedirect(user);
      });

    } catch (e: any) {
      console.error("Login failed:", e);
      this.message = '❌ Login failed: ' + (e.message?.includes('auth/invalid-credential') ? 'Invalid email or password.' : (e.message || e.code));
      this.loading = false; // Ensure loading stops on error
    }
    // No finally block needed for loading = false here due to navigation
  }

  async onGoogleLogin() {
    this.message = '';
    this.loading = true;
    try {
      // loginWithGoogle returns null if profile completion is needed (already redirects)
      const user = await this.auth.loginWithGoogle();

      if (user) { // Only proceed if login was successful and didn't redirect to complete-profile
        this.message = '✅ Login successful! Redirecting...';
        // Use NgZone for navigation
        this.ngZone.run(() => {
          this.handleRedirect(user);
        });
      } else {
        // User needs to complete profile, navigation handled by AuthService
        this.message = 'Redirecting to complete profile...';
        // Keep loading true until navigation occurs or handle differently if needed
        // this.loading = false; // Optionally stop loading indicator here
      }
    } catch (e: any) {
      console.error("Google Login failed:", e);
      // Handle popup closed error gracefully
      if (e.code !== 'auth/popup-closed-by-user') {
         this.message = '❌ Login failed: ' + (e.message || e.code);
      } else {
          this.message = ''; // Clear message if user just closed popup
      }
      this.loading = false; // Ensure loading stops on error
    }
  }

  // Helper function for redirection logic
  private handleRedirect(user: AppUser | null) {
    if (user?.userType === 'artisan') {
      console.log('Redirecting Artisan to external service...');
      // Use window.location.href for external navigation
      window.location.href = this.agenticServiceUrl;
    } else if (user?.userType === 'customer') {
      console.log('Redirecting Customer to /home...');
      // Use Angular Router for internal navigation
      this.router.navigate(['/home']);
    } else {
      // Fallback or handle cases where userType might be undefined
      // (e.g., profile fetch failed, but auth succeeded)
      console.warn('User logged in but userType is unknown. Redirecting to /home as default.');
      this.router.navigate(['/home']);
    }
  }
}