import { Component, OnInit, inject, signal } from '@angular/core'; // <-- Import signal
import { CommonModule } from '@angular/common';
import { ApiClientService, Product, VerificationResponse } from '../../services/api-client.service'; // <-- Import VerificationResponse
import { UiStateService } from '../../services/ui-state.service'; // <-- Import UiStateService
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
  // Use inject for cleaner dependency injection
  private apiService = inject(ApiClientService);
  private uiState = inject(UiStateService); // <-- Inject UiStateService

  products: Product[] = [];
  isLoading = signal(true); // <-- Use signal for loading state
  errorMessage = signal<string | null>(null); // <-- Use signal for error message

  // Signal to track which CraftID is currently being verified
  verifyingId = signal<string | null>(null);

  // Array to control how many skeletons are shown
  skeletonItems = new Array(6);

  // Polygonscan base URL for Amoy testnet
  readonly polygonscanBaseUrl = 'https://amoy.polygonscan.com/tx/';

  ngOnInit(): void {
    this.fetchProducts();
  }

  onImgError(event: Event): void {
    const target = event.target as HTMLImageElement;
    target.src = '/placeholder.png'; // Make sure placeholder.png exists in /public or /assets
  }

  fetchProducts(showLoading: boolean = true): void {
    if (showLoading) {
      this.isLoading.set(true);
      this.errorMessage.set(null);
      this.products = [];
    }
    this.apiService.getProducts().pipe(
      tap(data => {
        this.products = data;
      }),
      catchError(error => {
        console.error('Failed to fetch products:', error);
        this.errorMessage.set('Failed to load products. Please check the backend connection or API status.');
        this.products = [];
        return of([]); // Complete the stream gracefully
      }),
      finalize(() => {
        this.isLoading.set(false); // Ensure loading stops
      })
    ).subscribe(); // No need for next/complete handlers here
  }

  /**
   * NEW: Handles the verification button click.
   * Fetches verification status and redirects or shows a message.
   * @param publicId The CraftID to verify.
   */
  verify(publicId: string): void {
    if (!publicId) return; // Prevent call if ID is missing

    this.verifyingId.set(publicId); // Set loading state for this specific button

    this.apiService.verifyCraftID(publicId).pipe(
      finalize(() => {
        this.verifyingId.set(null); // Clear loading state when done (success or error)
      })
    ).subscribe({
      next: (response: VerificationResponse) => {
        console.log('Verification Response:', response);
        if (response.tx_hash) {
          // Transaction hash exists, redirect to Polygonscan
          const url = `${this.polygonscanBaseUrl}${response.tx_hash}`;
          console.log(`Redirecting to: ${url}`);
          window.open(url, '_blank'); // Open in a new tab
        } else {
          // No transaction hash, show appropriate message
          let message = response.verification_details?.reason || 'Verification is pending.';
          if (response.status === 'anchored' && !response.tx_hash) {
             message = 'Anchored, but transaction hash is missing. Please contact support.';
          } else if (response.status === 'pending') {
             message = 'Anchoring to the blockchain is still pending.';
          } else if (response.is_tampered) {
              message = 'Warning: Metadata may have been tampered with!';
              this.uiState.showToast(message, 'error', 5000); // Show longer error
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
