// shop-frontend/src/app/app.routes.ts
import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { SignupComponent } from './components/signup/signup.component';
import { HomeComponent } from './components/home/home.component';
import { authGuard } from './auth/auth.guard';
import { CompleteProfileComponent } from './components/complete-profile/complete-profile.component';
import { publicGuard } from './auth/public.guard'; // <-- IMPORT NEW GUARD

export const routes: Routes = [
  { 
    path: 'login', 
    component: LoginComponent, 
    data: { animation: 'LoginPage' },
    canActivate: [publicGuard] // <-- ADD GUARD
  },
  { 
    path: 'signup', 
    component: SignupComponent, 
    data: { animation: 'SignupPage' },
    canActivate: [publicGuard] // <-- ADD GUARD
  },
  { path: 'complete-profile', component: CompleteProfileComponent },
  { path: 'home', component: HomeComponent, canActivate: [authGuard] },
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: '**', redirectTo: 'login' },
];