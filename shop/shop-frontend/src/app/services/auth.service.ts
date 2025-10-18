// shop/shop-frontend/src/app/services/auth.service.ts
import { Injectable, signal, NgZone, inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  Auth,
  User,
  onAuthStateChanged,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  updateProfile,
  GoogleAuthProvider,
  signInWithPopup,
  setPersistence,
  browserLocalPersistence,
  authState
} from '@angular/fire/auth';
import {
  doc,
  setDoc,
  Firestore,
  getDoc,
} from '@angular/fire/firestore';
import { Observable, of, tap } from 'rxjs';
import { environment } from '../../environments/environments';

export interface AppUser extends User {
  userType?: 'artisan' | 'customer';
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private auth: Auth = inject(Auth);
  private firestore: Firestore = inject(Firestore);
  private router: Router = inject(Router);
  private ngZone: NgZone = inject(NgZone);

  currentUser = signal<AppUser | null>(null);
  public readonly authState$: Observable<User | null> = authState(this.auth);

  constructor() {
    // Try setting persistence immediately. If it fails, log and continue.
    setPersistence(this.auth, browserLocalPersistence)
      .then(() => {
        console.log('Persistence set to local.');
      })
      .catch((error) => {
        // Log the specific persistence error, but don't block app initialization
        console.error('Error setting persistence:', error);
      })
      .finally(() => {
        // Always setup the listener regardless of persistence success/failure
        this.setupAuthStateListener();
      });
  }

  private setupAuthStateListener() {
    onAuthStateChanged(this.auth, (user) => {
      // Run the ENTIRE callback logic within NgZone
      this.ngZone.run(() => {
        if (user) {
          console.log('(Listener) Auth State Changed: User logged in:', user.uid);
          this.fetchUserProfile(user); // Fetch profile when auth state confirms user
        } else {
          console.log('(Listener) Auth State Changed: User logged out.');
          if (this.currentUser() !== null) { // Only update if state actually changes
            this.currentUser.set(null);
          }
        }
      });
    });
  }

  private fetchUserProfile(user: User) {
    const userDocRef = doc(this.firestore, `users/${user.uid}`);
    // Use try-catch within the promise handler for better error isolation
    getDoc(userDocRef).then(docSnap => {
        // Run the promise resolution logic within NgZone
        this.ngZone.run(() => {
            if (docSnap.exists()) {
                const profile = docSnap.data();
                // Ensure profile includes expected fields before setting
                const appUser: AppUser = {
                   ...user,
                   // Safely access userType, default to undefined if missing
                   userType: profile?.['userType'] as ('artisan' | 'customer' | undefined)
                };
                this.currentUser.set(appUser);
                console.log('(Listener) User profile fetched:', this.currentUser());
            } else {
                 // Profile doesn't exist yet, set current user without userType
                this.currentUser.set({ ...user, userType: undefined });
                console.warn('(Listener) User profile document not found for UID:', user.uid);
            }
        });
    }).catch(error => {
        // Run error handling within NgZone
        this.ngZone.run(() => {
            console.error("(Listener) Error fetching user profile:", error);
            // Set user state even if profile fetch fails, explicitly mark userType as unknown
            this.currentUser.set({ ...user, userType: undefined });
        });
    });
  }

  isLoggedIn(): boolean {
    // Base isLoggedIn on the signal's current state
    return !!this.currentUser();
  }

  async signup(email: string, password: string, displayName: string, userType: 'artisan' | 'customer') {
    const cred = await createUserWithEmailAndPassword(this.auth, email, password);
    // Ensure profile is created FIRST
    await this.createUserProfile(cred.user.uid, displayName, email, userType);
    // Then update Auth profile
    await updateProfile(cred.user, { displayName });

    // Manually construct the full AppUser object for the signal
    const newUser: AppUser = {
        ...cred.user, // Spread the base User object properties
        displayName: displayName, // Ensure display name is included
        userType: userType // Add the userType
    };

    // Update the signal within the zone AFTER profile is confirmed created
    this.ngZone.run(() => {
        this.currentUser.set(newUser);
        console.log("Manual signal set after signup:", this.currentUser());
    });
    return cred;
  }

  async login(email: string, password: string) {
    // Login simply signs the user in. The authState listener handles profile fetching.
    return await signInWithEmailAndPassword(this.auth, email, password);
  }

  async loginWithGoogle() {
    const provider = new GoogleAuthProvider();
    try {
      const cred = await signInWithPopup(this.auth, provider);
      const user = cred.user;
      const userDocRef = doc(this.firestore, `users/${user.uid}`);

      // Check profile existence immediately after successful popup
      const docSnap = await getDoc(userDocRef);

      if (!docSnap.exists()) {
        console.log('New Google user detected. Storing pending info and redirecting.');
        // Store minimal necessary info
        localStorage.setItem('pendingUserProfile', JSON.stringify({
          uid: user.uid,
          name: user.displayName || 'User',
          email: user.email || ''
        }));
        // Navigate within the zone AFTER storing data
        this.ngZone.run(() => this.router.navigate(['/complete-profile']));
        return null; // Explicitly return null to indicate redirection
      } else {
        console.log('Existing Google user logged in.');
        // Profile exists. Let the authState listener handle fetching,
        // but update signal manually here for immediate feedback if needed.
        const profile = docSnap.data();
        const existingUser: AppUser = {
           ...user,
           userType: profile?.['userType'] as ('artisan' | 'customer' | undefined)
        };
        // Update signal within zone for consistency
        this.ngZone.run(() => {
            this.currentUser.set(existingUser);
            console.log("Manual signal set for existing Google user:", this.currentUser());
        });
        return cred; // Return credential to indicate success
      }
    } catch (error: any) {
      console.error("Google Sign-In Error:", error);
      // Optional: Check for specific cancellation errors
      if (error.code === 'auth/popup-closed-by-user') {
        console.log("Google Sign-In popup closed by user.");
      }
      // Don't navigate here, let the component handle UI feedback
      throw error; // Re-throw for component or global error handler
    }
  }

  async logout() {
    await signOut(this.auth);
    // Navigate within the zone AFTER sign out completes
    this.ngZone.run(() => this.router.navigate(['/login']));
  }

  async createUserProfile(uid: string, name: string | null, email: string | null, userType: 'artisan' | 'customer', merge = false) {
    // Ensure essential details have default values if null
    const profileName = name || 'User';
    const profileEmail = email || 'No Email';

    const userDocRef = doc(this.firestore, `users/${uid}`);
    console.log(`Attempting to create/update profile for UID: ${uid} with type: ${userType}`);
    try {
      await setDoc(userDocRef, {
        uid,
        name: profileName,
        email: profileEmail,
        userType,
        createdAt: new Date().toISOString(), // Use ISO string for consistency
      }, { merge }); // Use merge option passed in
      console.log(`Profile successfully created/updated for UID: ${uid}`);

      // Update signal AFTER successful Firestore write
      const authUser = this.auth.currentUser;
      if (authUser && authUser.uid === uid) {
        this.ngZone.run(() => {
          const updatedUser: AppUser = {
            ...authUser,
            // Use potentially updated name/email from profile data
            displayName: profileName,
            email: profileEmail,
            userType: userType
          };
          this.currentUser.set(updatedUser);
          console.log("Signal updated after profile creation/update:", this.currentUser());
        });
      }
    } catch (error) {
      // Log the specific error from Firestore
      console.error(`Firestore Error: Failed to create/update profile for UID: ${uid}`, error);
      throw error; // Propagate the error
    }
  }
}