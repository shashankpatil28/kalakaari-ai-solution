// shop-frontend/src/app/components/home/home.component.ts
import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiClientService, Product, VerificationResponse } from '../../services/api-client.service';
import { UiStateService } from '../../services/ui-state.service';
import { ShopStateService } from '../../services/shop-state.service';
import { catchError, finalize, map, of, tap } from 'rxjs';
import { SkeletonCardComponent } from '../utils/skeleton-card/skeleton-card.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, SkeletonCardComponent],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  // Injected Services
  private apiService = inject(ApiClientService);
  private uiState = inject(UiStateService);
  private shopState = inject(ShopStateService);

  // State Signals
  allProducts = signal<Product[]>([]); // <-- REMOVED 'private'
  isLoading = signal(true);
  errorMessage = signal<string | null>(null);
  verifyingId = signal<string | null>(null);
  
  // Computed Signal for Filtering
  filteredProducts = computed(() => {
    const query = this.shopState.searchQuery().toLowerCase();
    if (!query) {
      return this.allProducts(); // Return all if search is empty
    }
    return this.allProducts().filter(product => 
      product.art_info.name.toLowerCase().includes(query) ||
      product.artisan_info.name.toLowerCase().includes(query)
    );
  });

  // Other properties
  skeletonItems = new Array(6);
  readonly polygonscanBaseUrl = 'https://amoy.polygonscan.com/tx/';

  ngOnInit(): void {
    this.fetchProducts();
  }

  onImgError(event: Event): void {
    const target = event.target as HTMLImageElement;
    target.src = '/placeholder.png';
  }

  fetchProducts(showLoading: boolean = true): void {
    if (showLoading) {
      this.isLoading.set(true);
      this.errorMessage.set(null);
      this.allProducts.set([]);
    }
    this.apiService.getProducts().pipe(
      tap(data => {
        this.allProducts.set(data);
      }),
      catchError(error => {
        console.error('Failed to fetch products:', error);
        this.errorMessage.set('Failed to load products. Please check the backend connection or API status.');
        this.allProducts.set([]);
        return of([]);
      }),
      finalize(() => {
        this.isLoading.set(false);
      })
    ).subscribe();
  }

  verify(publicId: string): void {
    if (!publicId) return; 

    this.verifyingId.set(publicId);

    this.apiService.verifyCraftID(publicId).pipe(
      finalize(() => {
        this.verifyingId.set(null);
      })
    ).subscribe({
      next: (response: VerificationResponse) => {
        console.log('Verification Response:', response);
        if (response.tx_hash) {
          const url = `${this.polygonscanBaseUrl}${response.tx_hash}`;
          console.log(`Redirecting to: ${url}`);
          window.open(url, '_blank');
        } else {
          let message = response.verification_details?.reason || 'Verification is pending.';
          if (response.status === 'anchored' && !response.tx_hash) {
             message = 'Anchored, but transaction hash is missing. Please contact support.';
          } else if (response.status === 'pending') {
             message = 'Anchoring to the blockchain is still pending.';
          } else if (response.is_tampered) {
              message = 'Warning: Metadata may have been tampered with!';
              this.uiState.showToast(message, 'error', 5000);
              return;
          }
          this.uiState.showToast(message, 'info');
        }
      },
      error: (err) => {
        console.error(`Failed to verify CraftID ${publicId}:`, err);
        this.uiState.showToast(`Error verifying CraftID ${publicId}. Please try again later.`, 'error');
      }
    });
  }
}