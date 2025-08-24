import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule],
  template: `
    <nav class="flex items-center justify-between px-6 py-3 bg-blue-600 text-white shadow-md">
      <h1 class="text-xl font-bold">🛍️ MyShop</h1>
      <div class="flex gap-4">
        <a routerLink="/login" class="hover:underline">Login</a>
        <a routerLink="/signup" class="hover:underline">Signup</a>
      </div>
    </nav>
    <router-outlet></router-outlet>
  `,
})
export class AppComponent {}
