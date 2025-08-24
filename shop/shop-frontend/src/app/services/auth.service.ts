import { Injectable, signal, effect } from '@angular/core';
import {
  Auth,
  user as authUser,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  setPersistence,
  browserLocalPersistence,
  updateProfile,
  getIdToken
} from '@angular/fire/auth';
import { Router } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class AuthService {
  currentUser = signal<import('firebase/auth').User | null>(null);

  constructor(private auth: Auth, private router: Router) {
    authUser(this.auth).subscribe(u => {
      this.currentUser.set(u ?? null);

      if (u) {
        getIdToken(u).then(token => localStorage.setItem('idToken', token));
        localStorage.setItem('uid', u.uid);
      } else {
        localStorage.removeItem('idToken');
        localStorage.removeItem('uid');
      }
    });

    effect(() => {}); // optional reactive tracking
  }

  isLoggedIn(): boolean {
    return !!this.currentUser();
  }

  async signup(email: string, password: string, displayName?: string) {
    await setPersistence(this.auth, browserLocalPersistence);
    const cred = await createUserWithEmailAndPassword(this.auth, email, password);
    if (displayName) {
      await updateProfile(cred.user, { displayName });
    }
    return cred.user;
  }

  async login(email: string, password: string) {
    await setPersistence(this.auth, browserLocalPersistence);
    const cred = await signInWithEmailAndPassword(this.auth, email, password);
    return cred.user;
  }

  async logout() {
    await signOut(this.auth);
    this.router.navigate(['/login']);
  }
}
