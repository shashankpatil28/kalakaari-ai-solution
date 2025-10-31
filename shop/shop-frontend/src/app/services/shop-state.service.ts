// shop-frontend/src/app/services/shop-state.service.ts
import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ShopStateService {
  /**
   * A global signal holding the current search query.
   */
  public readonly searchQuery = signal<string>('');

  /**
   * Updates the global search query.
   * @param query The new search term.
   */
  public setSearchQuery(query: string): void {
    this.searchQuery.set(query.trim());
  }
}