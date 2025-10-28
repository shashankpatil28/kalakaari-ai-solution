# shop/shop-frontend/src/app/components/utils/skeleton-card/skeleton-card.component.ts
// shop/shop-frontend/src/app/components/utils/skeleton-card/skeleton-card.component.ts
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-skeleton-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './skeleton-card.component.html',
  // No specific styles needed unless you want more complex skeletons
})
export class SkeletonCardComponent {
  // Optional input if you ever want to display a message per skeleton
  @Input() message?: string;
}