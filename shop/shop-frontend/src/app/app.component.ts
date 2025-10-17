// shop/shop-frontend/src/app/app.component.ts
import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule],
  template: `
    <nav class="bg-surface sticky top-0 z-50 border-b border-secondary">
      <div class="container flex items-center justify-between py-4">
        <h1 class="text-2xl font-bold text-accent">Kalaakari Shop</h1>
        <div class="flex items-center gap-6">
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
        </div>
      </div>
    </nav>

    <main class="container py-10">
      <router-outlet></router-outlet>
    </main>
  `,
})
export class AppComponent {}