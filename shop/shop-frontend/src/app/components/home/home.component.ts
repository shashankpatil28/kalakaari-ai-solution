import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
})
export class HomeComponent {
  constructor(public auth: AuthService) {}

  products = [
    { id: 1, name: 'Wireless Headphones', price: 2999, image: 'https://via.placeholder.com/150' },
    { id: 2, name: 'Smart Watch', price: 4999, image: 'https://via.placeholder.com/150' },
    { id: 3, name: 'Gaming Mouse', price: 1999, image: 'https://via.placeholder.com/150' },
    { id: 4, name: 'Bluetooth Speaker', price: 2599, image: 'https://via.placeholder.com/150' },
  ];
}
