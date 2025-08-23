import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <nav style="padding: 12px; display:flex; gap:20px; border-bottom:1px solid #eee;">
      <a routerLink="/login" routerLinkActive="active-link">Login</a>
      <a routerLink="/signup" routerLinkActive="active-link">Signup</a>
    </nav>
    <main style="padding:16px;">
      <router-outlet></router-outlet>
    </main>
  `,
  styles: [`
    a { text-decoration: none; color: #555; font-weight: 500; }
    a.active-link { color: #1976d2; font-weight: 600; }
    nav { background:#f9f9f9; }
  `]
})
export class AppComponent {}
