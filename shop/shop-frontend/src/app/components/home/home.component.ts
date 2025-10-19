// shop/shop-frontend/src/app/components/home/home.component.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiClientService, Product } from '../../services/api-client.service';
import { catchError, map, of, tap } from 'rxjs';
import { SkeletonCardComponent } from '../utils/skeleton-card/skeleton-card.component'; // Import Skeleton component

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, SkeletonCardComponent], // Add SkeletonCardComponent to imports
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  products: Product[] = [];
  isLoading = true;
  errorMessage = '';
  // Array to control how many skeletons are shown
  skeletonItems = new Array(6); // Show 6 skeletons while loading

  constructor(
    private apiService: ApiClientService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.fetchProducts();

    // The polling interval remains the same
    // setInterval(() => {
    //   this.fetchProducts(false);
    // }, 5000);
  }

  onImgError(event: Event): void {
    const target = event.target as HTMLImageElement;
    // Consider using a local placeholder image from your /public folder
    target.src = '/placeholder.png'; // Make sure placeholder.png exists in /public
  }

  fetchProducts(showLoading: boolean = true): void {
    if (showLoading) {
      this.isLoading = true;
      this.errorMessage = ''; // Clear previous errors on new load
      this.products = []; // Clear products to show skeletons
      // Optionally adjust skeleton count based on expected items if known, otherwise fixed is fine
      // this.skeletonItems = new Array(SOME_EXPECTED_COUNT);
    }
    this.apiService.getProducts().pipe(
      tap(data => {
        // Simple assignment is usually fine, no need for JSON compare unless data source is noisy
        this.products = data;
        // No need for manual cdr.detectChanges() here typically, async pipe handles it.
        // If updates aren't showing, *then* add it back. Let's try without first.
      }),
      catchError(error => {
        console.error('Failed to fetch products:', error);
        this.errorMessage = 'Failed to load products. Please check the backend connection or API status.';
        this.products = []; // Ensure products are empty on error
        return of([]); // Return empty array observable to complete the stream
      })
    ).subscribe({
        // No need for next handler if tap does the work
        // next: () => {},
        complete: () => {
            this.isLoading = false; // Set loading false only when observable completes (success or caught error)
            // If using manual CDR: this.cdr.detectChanges();
        }
        // Error is handled by catchError, no need for error handler here unless re-throwing
        // error: () => { this.isLoading = false; }
    });
  }
}