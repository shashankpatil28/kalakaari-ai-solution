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
  templateUrl: './app.component.html',
  animations: [routerAnimation],
})
export class AppComponent {
  auth = inject(AuthService); // Modern way to inject service
  private contexts = inject(ChildrenOutletContexts);

  getRouteAnimationData() {
    return this.contexts.getContext('primary')?.route?.snapshot?.data?.['animation'];
  }
}