import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// --- Interfaces for getProducts (Unchanged) ---
export interface VerificationData {
  public_id: string;
  public_hash: string | null;
  verification_url: string; // Note: This might become redundant if handled client-side
}
export interface ArtisanInfo { name: string; location: string; }
export interface ArtInfo { name: string; description: string; photo: string; }
export interface Product {
  artisan_info: ArtisanInfo;
  art_info: ArtInfo;
  verification: VerificationData;
}

// --- NEW Interface for verifyCraftID Response ---
export interface VerificationDetails {
  metadata_tampered: boolean;
  blockchain_verified: boolean;
  reason: string;
}
export interface VerificationResponse {
  public_id: string;
  status: string; // e.g., "pending", "anchored"
  public_hash: string;
  stored_hash: string;
  computed_hash: string;
  is_tampered: boolean;
  tx_hash: string | null; // Transaction hash (can be null)
  anchored_at: string | null;
  blockchain_timestamp: string | null;
  verification_details: VerificationDetails;
}

@Injectable({
  providedIn: 'root'
})
export class ApiClientService {
  // URLs for different services
  private readonly shopApiUrl = 'https://kalakaari-shop-backend-978458840399.asia-southeast1.run.app';
  private readonly masterIpApiUrl = 'https://master-ip-service-978458840399.asia-southeast1.run.app';

  constructor(private http: HttpClient) { }

  /**
   * Fetches all products from the shop backend.
   */
  getProducts(): Observable<Product[]> {
    return this.http.get<Product[]>(`${this.shopApiUrl}/get-products`);
  }

  /**
   * NEW: Verifies a CraftID using the Master IP service.
   * @param publicId The CraftID (e.g., "CID-00012") to verify.
   * @returns An Observable of the VerificationResponse.
   */
  verifyCraftID(publicId: string): Observable<VerificationResponse> {
    return this.http.get<VerificationResponse>(`${this.masterIpApiUrl}/verify/${publicId}`);
  }
}
