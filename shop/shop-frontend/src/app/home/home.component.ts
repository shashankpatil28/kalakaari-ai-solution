import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../auth/auth.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <h2>Home (Protected)</h2>
    <p *ngIf="auth.currentUser()">Hello, {{ auth.currentUser()?.displayName || auth.currentUser()?.email }}</p>
    <button (click)="auth.logout()">Logout</button>
  `,
})
export class HomeComponent {
  constructor(public auth: AuthService) {}
}
