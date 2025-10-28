// shop-frontend/src/app/app.component.ts
import { Component, inject, signal } from '@angular/core'; // <-- IMPORT signal
import { ChildrenOutletContexts, NavigationEnd, Router, RouterModule } from '@angular/router'; // <-- IMPORT Router, NavigationEnd
import { routerAnimation } from './animation';
import { AuthService } from './services/auth.service';
import { CommonModule } from '@angular/common';
import { UiStateService } from './services/ui-state.service'; // <-- IMPORT RENAMED SERVICE
import { filter } from 'rxjs/operators'; // <-- IMPORT filter

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule, CommonModule],
  templateUrl: './app.component.html',
  animations: [routerAnimation],
})
export class AppComponent {
  auth = inject(AuthService);
  uiState = inject(UiStateService); // <-- INJECT RENAMED SERVICE
  
  private contexts = inject(ChildrenOutletContexts);
  private router = inject(Router); // <-- INJECT Router

  // --- NEW LOGIC TO HIDE NAVBAR ---
  public showNavbar = signal(true); // Default to true

  constructor() {
    // Listen to router events to hide navbar on login/signup
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd)
    ).subscribe((event: NavigationEnd) => {
      if (event.urlAfterRedirects === '/login' || event.urlAfterRedirects === '/signup') {
        this.showNavbar.set(false);
      } else {
        this.showNavbar.set(true);
      }
    });
  }
  // --- END NEW LOGIC ---

  getRouteAnimationData() {
    return this.contexts.getContext('primary')?.route?.snapshot?.data?.['animation'];
  }
}