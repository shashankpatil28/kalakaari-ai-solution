// shop-frontend/src/app/components/login/login.component.ts
import { Component, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService, AppUser } from '../../services/auth.service';
import { AnimatedInfoComponent } from '../utils/animated-info/animated-info.component'; // <-- IMPORT NEW COMPONENT

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, AnimatedInfoComponent], // <-- ADD NEW COMPONENT
  templateUrl: './login.component.html',
})
export class LoginComponent {
  email = '';
  password = '';
  message = '';
  loading = false;
  readonly agenticServiceUrl = 'https://agentic-service-978458840399.asia-southeast1.run.app/dev-ui/?app=agents';

  constructor(
    private auth: AuthService,
    private router: Router,
    private ngZone: NgZone
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
      this.ngZone.run(() => {
        this.handleRedirect(user);
      });
    } catch (e: any) {
      console.error("Login failed:", e);
      this.message = '❌ Login failed: ' + (e.message?.includes('auth/invalid-credential') ? 'Invalid email or password.' : (e.message || e.code));
      this.loading = false;
    }
  }

  async onGoogleLogin() {
    this.message = '';
    this.loading = true;
    try {
      const user = await this.auth.loginWithGoogle();
      if (user) {
        this.message = '✅ Login successful! Redirecting...';
        this.ngZone.run(() => {
          this.handleRedirect(user);
        });
      } else {
        this.message = 'Redirecting to complete profile...';
      }
    } catch (e: any) {
      console.error("Google Login failed:", e);
      if (e.code !== 'auth/popup-closed-by-user') {
         this.message = '❌ Login failed: ' + (e.message || e.code);
      } else {
          this.message = '';
      }
      this.loading = false;
    }
  }

  private handleRedirect(user: AppUser | null) {
    if (user?.userType === 'artisan') {
      console.log('Redirecting Artisan to external service...');
      window.location.href = this.agenticServiceUrl;
    } else if (user?.userType === 'art-lover') { // <-- CHANGED 'customer' to 'art-lover'
      console.log('Redirecting Art Lover to /home...');
      this.router.navigate(['/home']);
    } else {
      console.warn('User logged in but userType is unknown. Redirecting to /home as default.');
      this.router.navigate(['/home']);
    }
  }
}