# shop/shop-frontend/src/app/services/auth.service.ts
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
  authState,
  UserCredential // Import UserCredential
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
  userType?: 'artisan' | 'customer' | undefined; // Explicitly allow undefined
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
    setPersistence(this.auth, browserLocalPersistence)
      .then(() => {
        console.log('Persistence set to local.');
      })
      .catch((error) => {
        console.error('Error setting persistence:', error);
      })
      .finally(() => {
        this.setupAuthStateListener();
      });
  }

  private setupAuthStateListener() {
    onAuthStateChanged(this.auth, (user) => {
      this.ngZone.run(() => {
        if (user) {
          console.log('(Listener) Auth State Changed: User logged in:', user.uid);
          // Only fetch profile if currentUser signal doesn't match or lacks userType
          const currentSignalUser = this.currentUser();
          if (!currentSignalUser || currentSignalUser.uid !== user.uid || currentSignalUser.userType === undefined) {
             this.fetchUserProfile(user);
          } else {
             console.log('(Listener) Signal already up-to-date for user:', user.uid);
          }
        } else {
          console.log('(Listener) Auth State Changed: User logged out.');
          if (this.currentUser() !== null) {
            this.currentUser.set(null);
          }
        }
      });
    });
  }

  // Modified to return AppUser or null if profile fetch fails/missing
  private async fetchUserProfile(user: User): Promise<AppUser | null> {
    const userDocRef = doc(this.firestore, `users/${user.uid}`);
    try {
      const docSnap = await getDoc(userDocRef);
      let appUser: AppUser;
      if (docSnap.exists()) {
        const profile = docSnap.data();
        appUser = {
          ...user,
          userType: profile?.['userType'] as ('artisan' | 'customer' | undefined)
        };
        console.log('(Fetcher) User profile fetched:', appUser);
      } else {
        appUser = { ...user, userType: undefined }; // Profile doesn't exist yet
        console.warn('(Fetcher) User profile document not found for UID:', user.uid);
      }
      // Update signal within zone
      this.ngZone.run(() => this.currentUser.set(appUser));
      return appUser; // Return the fetched/constructed user object
    } catch (error) {
        console.error("(Fetcher) Error fetching user profile:", error);
        const errorUser: AppUser = { ...user, userType: undefined };
        // Update signal even on error
        this.ngZone.run(() => this.currentUser.set(errorUser));
        return errorUser; // Return user object even if fetch failed, userType will be undefined
    }
  }


  isLoggedIn(): boolean {
    return !!this.currentUser();
  }

  // --- Core Auth Methods ---

  // Modified to return AppUser
  async signup(email: string, password: string, displayName: string, userType: 'artisan' | 'customer'): Promise<AppUser> {
    const cred = await createUserWithEmailAndPassword(this.auth, email, password);
    // Profile must be created FIRST
    await this.createUserProfile(cred.user.uid, displayName, email, userType);
    await updateProfile(cred.user, { displayName });

    const newUser: AppUser = {
        ...cred.user,
        displayName: displayName,
        userType: userType
    };

    this.ngZone.run(() => {
        this.currentUser.set(newUser);
        console.log("Manual signal set after signup:", this.currentUser());
    });
    return newUser; // Return the newly created AppUser
  }

  // Modified to return AppUser or null
  async login(email: string, password: string): Promise<AppUser | null> {
    const cred = await signInWithEmailAndPassword(this.auth, email, password);
    // After successful sign-in, immediately fetch the profile
    return await this.fetchUserProfile(cred.user);
  }

  // Modified to return AppUser or null (if redirecting)
  async loginWithGoogle(): Promise<AppUser | null> {
    const provider = new GoogleAuthProvider();
    try {
      const cred = await signInWithPopup(this.auth, provider);
      const user = cred.user;
      const userDocRef = doc(this.firestore, `users/${user.uid}`);
      const docSnap = await getDoc(userDocRef);

      if (!docSnap.exists()) {
        console.log('New Google user detected. Storing pending info and redirecting.');
        localStorage.setItem('pendingUserProfile', JSON.stringify({
          uid: user.uid,
          name: user.displayName || 'User',
          email: user.email || ''
        }));
        this.ngZone.run(() => this.router.navigate(['/complete-profile']));
        return null; // Indicate profile completion needed
      } else {
        console.log('Existing Google user logged in.');
        // Profile exists. Fetch it to get userType and update signal
        const profile = docSnap.data();
        const existingUser: AppUser = {
           ...user,
           userType: profile?.['userType'] as ('artisan' | 'customer' | undefined)
        };
        this.ngZone.run(() => {
            this.currentUser.set(existingUser);
            console.log("Manual signal set for existing Google user:", this.currentUser());
        });
        return existingUser; // Return the AppUser
      }
    } catch (error: any) {
      console.error("Google Sign-In Error:", error);
      if (error.code === 'auth/popup-closed-by-user') {
        console.log("Google Sign-In popup closed by user.");
      }
      throw error;
    }
  }

  async logout() {
    await signOut(this.auth);
    this.ngZone.run(() => this.router.navigate(['/login']));
  }

  // Modified to return the updated AppUser or null on error
  async createUserProfile(uid: string, name: string | null, email: string | null, userType: 'artisan' | 'customer', merge = false): Promise<AppUser | null> {
    const profileName = name || 'User';
    const profileEmail = email || 'No Email';
    const userDocRef = doc(this.firestore, `users/${uid}`);
    console.log(`Attempting to create/update profile for UID: ${uid} with type: ${userType}`);
    const profileData = {
        uid,
        name: profileName,
        email: profileEmail,
        userType,
        createdAt: new Date().toISOString(),
    };

    try {
      await setDoc(userDocRef, profileData , { merge });
      console.log(`Profile successfully created/updated for UID: ${uid}`);

      const authUser = this.auth.currentUser;
      let updatedUser: AppUser | null = null;
      if (authUser && authUser.uid === uid) {
          updatedUser = {
            ...authUser,
            displayName: profileName,
            email: profileEmail,
            userType: userType
          };
          // Update signal immediately
          this.ngZone.run(() => {
            this.currentUser.set(updatedUser);
            console.log("Signal updated after profile creation/update:", this.currentUser());
          });
      }
      return updatedUser ?? { ...profileData, // Construct a basic user object if authUser isn't current somehow
            // Add required User fields if needed, though they might be missing
            // This case is less likely but provides a fallback return
            providerId: 'firebase', // Example placeholder
            delete: async () => {}, // Example placeholder
            getIdToken: async () => '', // Example placeholder
            // ... add other required User fields/methods with placeholders
          } as unknown as AppUser;
    } catch (error) {
      console.error(`Firestore Error: Failed to create/update profile for UID: ${uid}`, error);
      // Don't update signal on error, return null to indicate failure
      return null;
    }
  }
}