# shop/shop-frontend/src/app/app.config.ts
// shop/shop-frontend/src/app/app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient } from '@angular/common/http'; // Import HttpClient provider

import { routes } from './app.routes';
import { environment } from '../environments/environments';

// Firebase imports
import { initializeApp, provideFirebaseApp } from '@angular/fire/app';
import { getAuth, provideAuth } from '@angular/fire/auth';
import { getFirestore, provideFirestore } from '@angular/fire/firestore';

export const appConfig: ApplicationConfig = {
  providers: [
    // Your App Providers
    provideRouter(routes),
    provideAnimations(),
    provideHttpClient(), // <-- ADD THIS LINE

    // Firebase Providers
    provideFirebaseApp(() => initializeApp(environment.firebase)),
    provideAuth(() => getAuth()),
    provideFirestore(() => getFirestore()),
  ],
};