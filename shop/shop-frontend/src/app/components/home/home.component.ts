// shop/shop-frontend/src/app/components/home/home.component.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiClientService, Product } from '../../services/api-client.service';
import { catchError, map, of, tap } from 'rxjs';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  products: Product[] = [];
  isLoading = true;
  errorMessage = '';

  constructor(
    private apiService: ApiClientService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.fetchProducts();

    // The user's requested "CDR thing" for a live update simulation.
    // In a real-world app, we would use WebSockets or a real-time database
    // like Firestore to push updates. This simulates that behavior for a prototype.
    setInterval(() => {
      this.fetchProducts(false); // Fetch silently in the background
    }, 5000); // Polls every 5 seconds
  }

  onImgError(event: Event): void {
    const target = event.target as HTMLImageElement;
    target.src = 'https://image.shutterstock.com/image-vector/ui-image-placeholder-wireframes-apps-260nw-1037719204.jpg'; // fallback placeholder
  }

  fetchProducts(showLoading: boolean = true): void {
    if (showLoading) {
      this.isLoading = true;
    }
    this.apiService.getProducts().pipe(
      tap(data => {
        // Only update if the data has changed
        if (JSON.stringify(data) !== JSON.stringify(this.products)) {
          this.products = data;
          this.cdr.detectChanges(); // Manually trigger change detection
        }
      }),
      catchError(error => {
        console.error('Failed to fetch products:', error);
        this.errorMessage = 'Failed to load products. Please check the backend server.';
        return of([]);
      })
    ).subscribe(() => {
      this.isLoading = false;
    });
  }
}
