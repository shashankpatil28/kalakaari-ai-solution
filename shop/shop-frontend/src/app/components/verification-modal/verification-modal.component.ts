// shop-frontend/src/app/components/verification-modal/verification-modal.component.ts
import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { VerificationResponse } from '../../services/api-client.service';
import { TruncatePipe } from '../../pipes/truncate.pipe'; // Import the new pipe

@Component({
  selector: 'app-verification-modal',
  standalone: true,
  imports: [CommonModule, DatePipe, TruncatePipe], // Add pipes
  template: `
    <div 
      (click)="close.emit()" 
      class="fixed inset-0 z-[100] bg-background/80 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div 
        (click)="$event.stopPropagation()"
        class="w-full max-w-lg bg-surface rounded-2xl border border-secondary shadow-xl relative"
      >
        <button 
          (click)="close.emit()"
          class="absolute top-3 right-3 text-text-muted hover:text-accent transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div class="p-6 border-b border-secondary/50">
          @if (verificationData.status === 'anchored' && verificationData.verification_details?.blockchain_verified) {
            <div class="flex items-center gap-3">
              <span class="flex-shrink-0 w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center border border-green-500">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </span>
              <div>
                <h2 class="text-xl font-bold text-accent">CraftID Verified</h2>
                <p class="text-sm text-text-muted">This artwork's origin has been anchored on the blockchain.</p>
              </div>
            </div>
          } @else if (verificationData.status === 'pending') {
            <div class="flex items-center gap-3">
              <span class="flex-shrink-0 w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center border border-amber-500">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                   <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </span>
              <div>
                <h2 class="text-xl font-bold text-accent">Verification Pending</h2>
                <p class="text-sm text-text-muted">This artwork is scheduled to be anchored on the blockchain soon.</p>
              </div>
            </div>
          } @else {
            <div class="flex items-center gap-3">
              <span class="flex-shrink-0 w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500">
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                   <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                 </svg>
              </span>
              <div>
                <h2 class="text-xl font-bold text-accent">Verification Issue</h2>
                <p class="text-sm text-text-muted">{{ verificationData.verification_details?.reason || 'An unknown error occurred.' }}</p>
              </div>
            </div>
          }
        </div>

        <div class="p-6 space-y-4">
          <div class="flex justify-between items-center">
            <span class="text-sm text-text-muted">Title</span>
            <span class="text-sm font-medium text-accent">{{ productName }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm text-text-muted">CraftID</span>
            <span class="text-sm font-mono text-accent">{{ verificationData.public_id }}</span>
          </div>
          
          @if (verificationData.anchored_at) {
            <div class="flex justify-between items-center">
              <span class="text-sm text-text-muted">Anchored At</span>
              <span class="text-sm font-medium text-accent">{{ verificationData.anchored_at | date:'medium' }}</span>
            </div>
          }

          @if (verificationData.tx_hash) {
            <div class="flex justify-between items-center">
              <span class="text-sm text-text-muted">Transaction ID</span>
              <span class="text-sm font-mono text-accent">{{ verificationData.tx_hash | truncate:10:10 }}</span>
            </div>
          }
        </div>

        @if (verificationData.tx_hash) {
          <div class="p-6 bg-background rounded-b-2xl border-t border-secondary/50">
            <a 
              [href]="polygonscanBaseUrl + '0x' + verificationData.tx_hash" 
              target="_blank"
              class="w-full flex items-center justify-center gap-2 text-center py-2 px-4 rounded-lg text-background bg-primary hover:bg-primary-light transition-colors duration-300 font-semibold"
            >
              <span>View on Polygonscan</span>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          </div>
        }

      </div>
    </div>
  `,
  // We can add inline styles for simple components
  styles: [`
    :host {
      display: contents; /* Ensures component doesn't break flex/grid layouts */
    }
  `]
})
export class VerificationModalComponent {
  @Input({ required: true }) verificationData!: VerificationResponse;
  @Input() productName: string | null = 'Artwork';
  @Output() close = new EventEmitter<void>();

  readonly polygonscanBaseUrl = 'https://amoy.polygonscan.com/tx/';
}