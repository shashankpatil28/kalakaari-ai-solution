import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../auth/auth.service';

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

  constructor(private auth: AuthService, private router: Router) {}

  async onLogin() {
    this.message = '';
    this.loading = true;
    try {
      await this.auth.login(this.email, this.password);
      this.message = 'Login successful! Redirecting...';
      setTimeout(() => this.router.navigate(['/home']), 1200);
    } catch (e: any) {
      this.message = 'Login failed: ' + (e.message || e.code);
    } finally {
      this.loading = false;
    }
  }
}
