// shop/shop-frontend/src/app/components/complete-profile/complete-profile.component.ts
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

interface PendingUser {
    uid: string;
    name: string;
    email: string;
}

@Component({
  selector: 'app-complete-profile',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './complete-profile.component.html',
  // Add styles if needed: styleUrls: ['./complete-profile.component.scss']
})
export class CompleteProfileComponent implements OnInit {
  auth = inject(AuthService);
  router = inject(Router);

  pendingUser: PendingUser | null = null;
  userType: 'artisan' | 'customer' = 'customer';
  loading = false;
  message = '';

  ngOnInit(): void {
    const pendingData = localStorage.getItem('pendingUserProfile');
    if (pendingData) {
      this.pendingUser = JSON.parse(pendingData);
    } else {
      // If no pending data, maybe redirect to login or home?
      console.error('No pending user profile data found.');
      this.router.navigate(['/login']);
    }
  }

  async onSubmit() {
    if (!this.pendingUser) {
      this.message = 'Error: User data is missing.';
      return;
    }
    if (!this.userType) {
        this.message = 'Please select an account type.';
        return;
    }

    this.loading = true;
    this.message = '';

    try {
      await this.auth.createUserProfile(
        this.pendingUser.uid,
        this.pendingUser.name,
        this.pendingUser.email,
        this.userType
      );
      localStorage.removeItem('pendingUserProfile'); // Clean up
      this.router.navigate(['/home']); // Navigate to home after profile creation
    } catch (error: any) {
      console.error('Error saving profile:', error);
      this.message = 'Failed to save profile: ' + (error.message || 'Unknown error');
    } finally {
      this.loading = false;
    }
  }
} 