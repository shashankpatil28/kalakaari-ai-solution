# shop/shop-frontend/src/app/services/api-client.service.ts
// shop/shop-frontend/src/app/services/api-client.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Define interfaces to match the backend API response
export interface VerificationData {
  public_id: string;
  public_hash: string;
  verification_url: string;
}

export interface ArtisanInfo {
  name: string;
  location: string;
}

export interface ArtInfo {
  name: string;
  description: string;
  photo: string;
}

export interface Product {
  artisan_info: ArtisanInfo;
  art_info: ArtInfo;
  verification: VerificationData;
}

@Injectable({
  providedIn: 'root'
})
export class ApiClientService {
  private readonly apiUrl = 'https://basic-backend-fastapi.vercel.app/get-products';

  constructor(private http: HttpClient) { }
  /**
   * Fetches all products from the shop backend.
   * @returns An Observable of an array of Product objects.
   */
  getProducts(): Observable<Product[]> {
    return this.http.get<Product[]>(this.apiUrl);
  }
}
