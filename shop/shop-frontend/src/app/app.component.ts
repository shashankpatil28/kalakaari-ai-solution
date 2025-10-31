// shop-frontend/src/app/app.component.ts
import { Component, inject, signal, HostListener, ElementRef } from '@angular/core';
import { ChildrenOutletContexts, NavigationEnd, Router, RouterModule } from '@angular/router';
import { routerAnimation } from './animation';
import { AuthService } from './services/auth.service';
import { CommonModule } from '@angular/common';
import { UiStateService } from './services/ui-state.service';
import { filter } from 'rxjs/operators';
import { UserStateService } from './services/user-state.service';
import { ShopStateService } from './services/shop-state.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule, CommonModule, FormsModule],
  templateUrl: './app.component.html',
  animations: [routerAnimation],
})
export class AppComponent {
  // Injected Services
  auth = inject(AuthService);
  uiState = inject(UiStateService);
  userState = inject(UserStateService);
  shopState = inject(ShopStateService);
  
  private contexts = inject(ChildrenOutletContexts);
  private router = inject(Router);
  private eRef = inject(ElementRef);

  // Local State
  public showNavbar = signal(true);
  public isProfileMenuOpen = signal(false);
  public searchQuery: string = '';

  // Click-away listener to close the profile menu
  @HostListener('document:click', ['$event.target'])
  onClickAway(targetElement: EventTarget | null) { // <-- CHANGED TYPE
    const wrapper = this.eRef.nativeElement.querySelector('#profileWrapper');
    
    // Check if targetElement is valid and is a Node before calling 'contains'
    if (this.isProfileMenuOpen() && wrapper && targetElement instanceof Node && !wrapper.contains(targetElement)) { // <-- CHANGED CONDITION
      this.isProfileMenuOpen.set(false);
    }
  }

  constructor() {
    // Logic to hide navbar on login/signup
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd)
    ).subscribe((event: NavigationEnd) => {
      this.showNavbar.set(event.urlAfterRedirects !== '/login' && event.urlAfterRedirects !== '/signup');
      
      // Also reset search when navigating away from home (optional, but good UX)
      if (!event.urlAfterRedirects.startsWith('/home')) {
        this.searchQuery = '';
        this.shopState.setSearchQuery('');
      }
    });

    // Initialize local search query from state (for page reloads)
    this.searchQuery = this.shopState.searchQuery();
  }

  getRouteAnimationData() {
    return this.contexts.getContext('primary')?.route?.snapshot?.data?.['animation'];
  }

  // --- NEW METHODS ---

  /**
   * Toggles the profile menu's visibility.
   */
  toggleProfileMenu(): void {
    this.isProfileMenuOpen.update(v => !v);
  }

  /**
   * Updates the global search state as the user types.
   */
  onSearchChange(query: string): void {
    this.shopState.setSearchQuery(query);
  }

  /**
   * Logs out the user and closes the menu.
   */
  logout(): void {
    this.auth.logout();
    this.isProfileMenuOpen.set(false);
  }
}