// shop-frontend/src/app/components/utils/animated-info/animated-info.component.ts
import { Component, Input, OnInit, OnDestroy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-animated-info',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="h-10 text-lg text-text-muted text-center relative">
      @for (item of phrases; track $index) {
        <span 
          class="absolute left-0 right-0 transition-opacity duration-500 ease-in-out"
          [class.opacity-0]="currentPhraseIndex() !== $index"
          [class.opacity-100]="currentPhraseIndex() === $index">
          {{ item.text }}
        </span>
      }
    </div>
  `
})
export class AnimatedInfoComponent implements OnInit, OnDestroy {
  
  @Input() phrases = [
    { text: "Are you an Artisan?", duration: 3000 },
    { text: "Protect your craft with AI-powered IP.", duration: 3000 },
    { text: "Are you an Art Lover?", duration: 3000 },
    { text: "Discover and buy unique, verified art.", duration: 3000 }
  ];

  currentPhraseIndex = signal(0);
  private intervalId: any;

  ngOnInit(): void {
    this.startAnimation();
  }

  ngOnDestroy(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
  }

  startAnimation(): void {
    this.intervalId = setInterval(() => {
      this.currentPhraseIndex.update(index => (index + 1) % this.phrases.length);
    }, this.phrases[this.currentPhraseIndex()].duration);
  }
}