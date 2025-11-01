// shop-frontend/src/app/pipes/truncate.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'truncate',
  standalone: true
})
export class TruncatePipe implements PipeTransform {
  transform(value: string | null | undefined, frontLen: number, backLen: number, fill: string = '...'): string {
    if (!value) {
      return '';
    }

    if (value.length <= frontLen + backLen) {
      return value;
    }

    const front = value.substring(0, frontLen);
    const back = value.substring(value.length - backLen);

    return `${front}${fill}${back}`;
  }
}