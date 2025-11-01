// shop-frontend/src/app/components/home/home.component.ts
import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiClientService, Product, VerificationResponse } from '../../services/api-client.service';
import { UiStateService } from '../../services/ui-state.service';
import { ShopStateService } from '../../services/shop-state.service';
import { catchError, finalize, map, of, tap } from 'rxjs';
import { SkeletonCardComponent } from '../utils/skeleton-card/skeleton-card.component';
import { VerificationModalComponent } from '../verification-modal/verification-modal.component'; // <-- IMPORT MODAL

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, SkeletonCardComponent, VerificationModalComponent], // <-- ADD MODAL
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  // Injected Services
  private apiService = inject(ApiClientService);
  private uiState = inject(UiStateService);
  private shopState = inject(ShopStateService);

  // State Signals
  allProducts = signal<Product[]>([]);
  isLoading = signal(true);
  errorMessage = signal<string | null>(null);
  verifyingId = signal<string | null>(null);
  
  // --- NEW MODAL STATE SIGNALS ---
  selectedVerificationData = signal<VerificationResponse | null>(null);
  selectedProductName = signal<string | null>(null);
  // --- END NEW SIGNALS ---
  
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
  // readonly polygonscanBaseUrl = 'https://amoy.polygonscan.com/tx/'; // <-- This is now in the modal

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

  /**
   * MODIFIED: Handles the verification button click.
   * Fetches verification status and shows the modal.
   * @param product The entire Product object being verified.
   */
  verify(product: Product): void { // <-- CHANGED signature
    if (!product || !product.verification.public_id) return; 

    this.verifyingId.set(product.verification.public_id);

    this.apiService.verifyCraftID(product.verification.public_id).pipe(
      finalize(() => {
        this.verifyingId.set(null); // Stop button spinner
      })
    ).subscribe({
      next: (response: VerificationResponse) => {
        console.log('Verification Response:', response);
        // --- MODIFIED LOGIC: SET STATE FOR MODAL ---
        this.selectedProductName.set(product.art_info.name);
        this.selectedVerificationData.set(response);
        // --- END MODIFIED LOGIC ---
      },
      error: (err) => {
        console.error(`Failed to verify CraftID ${product.verification.public_id}:`, err);
        this.uiState.showToast(`Error verifying CraftID. Please try again later.`, 'error');
      }
    });
  }

  /**
   * NEW: Closes the verification modal.
   */
  closeModal(): void {
    this.selectedVerificationData.set(null);
    this.selectedProductName.set(null);
  }
}