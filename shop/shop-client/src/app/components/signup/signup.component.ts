import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service'; // <-- updated path

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './signup.component.html',
})
export class SignupComponent {
  name = '';
  email = '';
  password = '';
  confirm = '';
  message = '';
  loading = false;

  constructor(private auth: AuthService, private router: Router) {}

  async onSignup() {
    this.message = '';
    if (!this.name.trim()) { this.message = 'Name is required'; return; }
    if (!this.email.trim()) { this.message = 'Email is required'; return; }
    if (this.password.length < 6) { this.message = 'Password must be at least 6 characters'; return; }
    if (this.password !== this.confirm) { this.message = 'Passwords do not match'; return; }

    this.loading = true;
    try {
      await this.auth.signup(this.email, this.password, this.name);
      this.message = '✅ Signup successful! Redirecting...';
      setTimeout(() => this.router.navigate(['/home']), 1500);
    } catch (e: any) {
      this.message = this.humanizeError(e?.message || e?.code || 'Signup failed');
    } finally {
      this.loading = false;
    }
  }

  private humanizeError(msg: string) {
    if (msg.includes('auth/email-already-in-use')) return 'Email already in use.';
    if (msg.includes('auth/invalid-email')) return 'Invalid email address.';
    if (msg.includes('auth/weak-password')) return 'Password is too weak.';
    return msg;
  }
}
