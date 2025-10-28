// shop-frontend/src/app/services/auth.service.ts
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
  UserCredential
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
  userType?: 'artisan' | 'art-lover' | undefined; // <-- CHANGED 'customer' to 'art-lover'
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
    this.setupAuthStateListener();
    setPersistence(this.auth, browserLocalPersistence)
      .then(() => {
        console.log('Persistence set to local.');
      })
      .catch((error) => {
        console.error('Error setting persistence:', error);
      });
  }

  private setupAuthStateListener() {
    onAuthStateChanged(this.auth, (user) => {
      this.ngZone.run(() => {
        if (user) {
          console.log('(Listener) Auth State Changed: User logged in:', user.uid);
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

  private async fetchUserProfile(user: User): Promise<AppUser | null> {
    const userDocRef = doc(this.firestore, `users/${user.uid}`);
    try {
      const docSnap = await getDoc(userDocRef);
      let appUser: AppUser;
      if (docSnap.exists()) {
        const profile = docSnap.data();
        appUser = {
          ...user,
          userType: profile?.['userType'] as ('artisan' | 'art-lover' | undefined) // <-- CHANGED
        };
        console.log('(Fetcher) User profile fetched:', appUser);
      } else {
        appUser = { ...user, userType: undefined };
        console.warn('(Fetcher) User profile document not found for UID:', user.uid);
      }
      this.ngZone.run(() => this.currentUser.set(appUser));
      return appUser;
    } catch (error) {
        console.error("(Fetcher) Error fetching user profile:", error);
        const errorUser: AppUser = { ...user, userType: undefined };
        this.ngZone.run(() => this.currentUser.set(errorUser));
        return errorUser;
    }
  }


  isLoggedIn(): boolean {
    return !!this.currentUser();
  }

  // --- Core Auth Methods ---

  async signup(email: string, password: string, displayName: string, userType: 'artisan' | 'art-lover'): Promise<AppUser> { // <-- CHANGED
    const cred = await createUserWithEmailAndPassword(this.auth, email, password);
    await this.createUserProfile(cred.user.uid, displayName, email, userType); // <-- CHANGED
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
    return newUser;
  }

  async login(email: string, password: string): Promise<AppUser | null> {
    const cred = await signInWithEmailAndPassword(this.auth, email, password);
    return await this.fetchUserProfile(cred.user);
  }

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
        return null;
      } else {
        console.log('Existing Google user logged in.');
        const profile = docSnap.data();
        const existingUser: AppUser = {
           ...user,
           userType: profile?.['userType'] as ('artisan' | 'art-lover' | undefined) // <-- CHANGED
        };
        this.ngZone.run(() => {
            this.currentUser.set(existingUser);
            console.log("Manual signal set for existing Google user:", this.currentUser());
        });
        return existingUser;
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

  async createUserProfile(uid: string, name: string | null, email: string | null, userType: 'artisan' | 'art-lover', merge = false): Promise<AppUser | null> { // <-- CHANGED
    const profileName = name || 'User';
    const profileEmail = email || 'No Email';
    const userDocRef = doc(this.firestore, `users/${uid}`);
    console.log(`Attempting to create/update profile for UID: ${uid} with type: ${userType}`);
    const profileData = {
        uid,
        name: profileName,
        email: profileEmail,
        userType, // <-- Will be 'artisan' or 'art-lover'
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
          this.ngZone.run(() => {
            this.currentUser.set(updatedUser);
            console.log("Signal updated after profile creation/update:", this.currentUser());
          });
      }
      return updatedUser ?? { ...profileData,
            providerId: 'firebase',
            delete: async () => {},
            getIdToken: async () => '',
          } as unknown as AppUser;
    } catch (error) {
      console.error(`Firestore Error: Failed to create/update profile for UID: ${uid}`, error);
      return null;
    }
  }
}