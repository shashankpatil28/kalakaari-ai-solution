// shop/shop-frontend/src/app/app.component.ts
import { Component, inject } from '@angular/core';
import { ChildrenOutletContexts, RouterModule } from '@angular/router';
import { routerAnimation } from './animation';
import { AuthService } from './services/auth.service'; // Import AuthService
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule, CommonModule], // Add CommonModule
  template: `
    <nav class="bg-surface sticky top-0 z-50 border-b border-secondary">
      <div class="container flex items-center justify-between py-4">
        <h1 class="text-2xl font-bold text-accent">Kalaakari Shop</h1>
        <div class="flex items-center gap-6">
          <!-- Logged Out State -->
          <ng-container *ngIf="!auth.currentUser()">
            <a
              routerLink="/login"
              class="font-medium text-text-muted hover:text-accent transition-colors duration-300"
              >Login</a
            >
            <a
              routerLink="/signup"
              class="font-medium text-text-muted hover:text-accent transition-colors duration-300"
              >Sign Up</a
            >
          </ng-container>

          <!-- Logged In State -->
          <ng-container *ngIf="auth.currentUser() as user">
            <span class="font-medium text-text-muted">
              Hello, {{ user.displayName || 'User' }}
            </span>
            <button
              (click)="auth.logout()"
              class="font-medium text-text-muted hover:text-accent transition-colors duration-300"
            >
              Logout
            </button>
          </ng-container>
        </div>
      </div>
    </nav>
    <main>
      <div [@routerAnimation]="getRouteAnimationData()">
        <router-outlet></router-outlet>
      </div>
    </main>
  `,
  animations: [routerAnimation],
})
export class AppComponent {
  auth = inject(AuthService); // Modern way to inject service
  private contexts = inject(ChildrenOutletContexts);

  getRouteAnimationData() {
    return this.contexts.getContext('primary')?.route?.snapshot?.data?.['animation'];
  }
}