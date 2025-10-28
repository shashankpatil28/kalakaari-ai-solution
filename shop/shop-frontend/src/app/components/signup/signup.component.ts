// shop-frontend/src/app/components/signup/signup.component.ts
import { Component, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService, AppUser } from '../../services/auth.service';
import { AnimatedInfoComponent } from '../utils/animated-info/animated-info.component'; // <-- IMPORT NEW COMPONENT

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, AnimatedInfoComponent], // <-- ADD NEW COMPONENT
  templateUrl: './signup.component.html',
})
export class SignupComponent {
  name = '';
  email = '';
  password = '';
  confirm = '';
  userType: 'artisan' | 'art-lover' = 'art-lover'; // <-- CHANGED 'customer' to 'art-lover'
  message = '';
  loading = false;
  readonly agenticServiceUrl = 'https://agentic-service-978458840399.asia-southeast1.run.app/dev-ui/?app=agents';

  constructor(
    private auth: AuthService,
    private router: Router,
    private ngZone: NgZone
  ) {}

  async onSignup() {
    this.message = '';
    // --- Start Validation ---
    if (!this.name.trim()) { this.message = 'Name is required'; return; }
    if (!this.email.trim()) { this.message = 'Email is required'; return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.email)) { this.message = 'Invalid email format'; return; }
    if (this.password.length < 6) { this.message = 'Password must be at least 6 characters'; return; }
    if (this.password !== this.confirm) { this.message = 'Passwords do not match'; return; }
    if (!this.userType) { this.message = 'Please select an account type'; return; }
    // --- End Validation ---

    this.loading = true;
    try {
      const newUser = await this.auth.signup(this.email, this.password, this.name, this.userType);
      this.message = '✅ Signup successful! Redirecting...';

      this.ngZone.run(() => {
        this.handleRedirect(newUser);
      });

    } catch (e: any) {
      console.error("Signup failed:", e);
      this.message = '❌ Signup failed: ' + this.humanizeError(e?.message || e?.code || 'Unknown error');
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
      console.warn('User signed up but userType unclear. Redirecting to /home as default.');
      this.router.navigate(['/home']);
    }
  }

  private humanizeError(msg: string) {
    if (msg.includes('auth/email-already-in-use')) return 'Email already in use.';
    if (msg.includes('auth/invalid-email')) return 'Invalid email address.';
    if (msg.includes('auth/weak-password')) return 'Password is too weak.';
    return msg;
  }
}