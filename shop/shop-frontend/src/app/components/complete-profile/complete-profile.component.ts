// shop-frontend/src/app/components/complete-profile/complete-profile.component.ts
import { Component, OnInit, inject, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService, AppUser } from '../../services/auth.service';

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
})
export class CompleteProfileComponent implements OnInit {
  auth = inject(AuthService);
  router = inject(Router);
  ngZone = inject(NgZone);

  pendingUser: PendingUser | null = null;
  userType: 'artisan' | 'art-lover' = 'art-lover'; // <-- CHANGED 'customer' to 'art-lover'
  loading = false;
  message = '';
  readonly agenticServiceUrl = 'https://agentic-service-978458840399.asia-southeast1.run.app/dev-ui/?app=agents';


  ngOnInit(): void {
    const pendingData = localStorage.getItem('pendingUserProfile');
    if (pendingData) {
      try {
        this.pendingUser = JSON.parse(pendingData);
        if (!this.auth.currentUser()) {
             console.warn('Pending profile data exists, but user is not logged in. Redirecting to login.');
             localStorage.removeItem('pendingUserProfile');
             this.router.navigate(['/login']);
        }
      } catch (e) {
         console.error('Failed to parse pending user profile data:', e);
         localStorage.removeItem('pendingUserProfile');
         this.router.navigate(['/login']);
      }
    } else {
      console.log('No pending user profile data found. Checking current user state.');
      const currentUser = this.auth.currentUser();
      if (currentUser && currentUser.userType) {
          console.log('User already has a profile. Redirecting...');
          this.handleRedirect(currentUser);
      } else if (currentUser && !currentUser.userType) {
          console.warn('User logged in but profile seems incomplete. Allowing profile completion.');
          this.pendingUser = { uid: currentUser.uid, name: currentUser.displayName || 'User', email: currentUser.email || '' };
      }
       else {
          console.log('Not logged in and no pending data. Redirecting to login.');
          this.router.navigate(['/login']);
       }
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
      const updatedUser = await this.auth.createUserProfile(
        this.pendingUser.uid,
        this.pendingUser.name,
        this.pendingUser.email,
        this.userType
      );

      localStorage.removeItem('pendingUserProfile');

      if (updatedUser) {
          this.ngZone.run(() => {
              this.handleRedirect(updatedUser);
          });
      } else {
          this.message = 'Profile saved, but failed to retrieve updated user data. Redirecting to home.';
          console.warn('createUserProfile returned null unexpectedly.');
          this.ngZone.run(() => this.router.navigate(['/home']));
      }

    } catch (error: any) {
      console.error('Error saving profile:', error);
      this.message = 'Failed to save profile: ' + (error.message || 'Unknown error');
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
      console.warn('User profile complete but userType unclear. Redirecting to /home as default.');
      this.router.navigate(['/home']);
    }
  }
}