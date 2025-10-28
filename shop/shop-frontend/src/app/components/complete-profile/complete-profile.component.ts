# shop/shop-frontend/src/app/components/complete-profile/complete-profile.component.ts
// shop/shop-frontend/src/app/components/complete-profile/complete-profile.component.ts
import { Component, OnInit, inject, NgZone } from '@angular/core'; // Import NgZone
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService, AppUser } from '../../services/auth.service'; // Import AppUser

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
  ngZone = inject(NgZone); // Inject NgZone

  pendingUser: PendingUser | null = null;
  userType: 'artisan' | 'customer' = 'customer';
  loading = false;
  message = '';
  readonly agenticServiceUrl = 'https://agentic-service-978458840399.asia-southeast1.run.app/dev-ui/?app=agents'; // Define URL


  ngOnInit(): void {
    const pendingData = localStorage.getItem('pendingUserProfile');
    if (pendingData) {
      try {
        this.pendingUser = JSON.parse(pendingData);
        // Also check if user is actually logged in, otherwise redirect
        if (!this.auth.currentUser()) {
             console.warn('Pending profile data exists, but user is not logged in. Redirecting to login.');
             localStorage.removeItem('pendingUserProfile'); // Clean up invalid state
             this.router.navigate(['/login']);
        }
      } catch (e) {
         console.error('Failed to parse pending user profile data:', e);
         localStorage.removeItem('pendingUserProfile'); // Clean up corrupted data
         this.router.navigate(['/login']);
      }
    } else {
      console.log('No pending user profile data found. Checking current user state.');
      // If no pending data, maybe user landed here directly but is logged in?
      // Or maybe they refreshed? Check current user state from service.
      const currentUser = this.auth.currentUser();
      if (currentUser && currentUser.userType) {
          // User is logged in and has a profile, redirect appropriately
          console.log('User already has a profile. Redirecting...');
          this.handleRedirect(currentUser); // Use existing redirect logic
      } else if (currentUser && !currentUser.userType) {
          // Logged in but somehow profile is still incomplete? Stay here.
          console.warn('User logged in but profile seems incomplete. Allowing profile completion.');
          // Synthesize pendingUser from currentUser if possible
          this.pendingUser = { uid: currentUser.uid, name: currentUser.displayName || 'User', email: currentUser.email || '' };
      }
       else {
          // No pending data and not logged in
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
      // createUserProfile should now return the updated AppUser or null
      const updatedUser = await this.auth.createUserProfile(
        this.pendingUser.uid,
        this.pendingUser.name,
        this.pendingUser.email,
        this.userType
      );

      localStorage.removeItem('pendingUserProfile'); // Clean up immediately on success attempt

      if (updatedUser) {
          // Use NgZone for navigation
          this.ngZone.run(() => {
              this.handleRedirect(updatedUser); // Use the returned user data
          });
      } else {
          // Handle case where profile creation failed but didn't throw? Unlikely but possible.
          this.message = 'Profile saved, but failed to retrieve updated user data. Redirecting to home.';
          console.warn('createUserProfile returned null unexpectedly.');
          this.ngZone.run(() => this.router.navigate(['/home']));
      }

    } catch (error: any) {
      console.error('Error saving profile:', error);
      this.message = 'Failed to save profile: ' + (error.message || 'Unknown error');
      this.loading = false; // Stop loading on error
    }
  }

  // Helper function for redirection logic (can be identical to LoginComponent's)
  private handleRedirect(user: AppUser | null) {
    // Check userType directly from the object returned/passed in
    if (user?.userType === 'artisan') {
      console.log('Redirecting Artisan to external service...');
      window.location.href = this.agenticServiceUrl;
    } else if (user?.userType === 'customer') {
      console.log('Redirecting Customer to /home...');
      this.router.navigate(['/home']);
    } else {
      // Fallback if user object is null or userType is missing
      console.warn('User profile complete but userType unclear. Redirecting to /home as default.');
      this.router.navigate(['/home']);
    }
  }
}